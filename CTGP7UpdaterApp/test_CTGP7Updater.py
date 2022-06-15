import pathlib
from turtle import update
import pytest
import http.server
import socketserver
import multiprocessing
import socket
from contextlib import closing
import os
import filecmp

from CTGP7UpdaterApp.CTGP7Updater import CTGP7Updater

class TestCTGP7Updater:

    _TEST_DATA_PATH = "testData"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            print("Server address: {}".format(os.path.abspath(TestCTGP7Updater._TEST_DATA_PATH)))
            super().__init__(*args, directory=TestCTGP7Updater._TEST_DATA_PATH, **kwargs)

    @staticmethod
    def start_server_process(port):
        print("Server port: {}".format(port))
        with socketserver.TCPServer(("", port), TestCTGP7Updater.Handler) as httpd:
            httpd.serve_forever()

    # Fixtures
    @pytest.fixture(scope="class")
    def server_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    @pytest.fixture(scope="class", autouse=True)
    def setup_server(self, server_port):
        p = multiprocessing.Process(target=TestCTGP7Updater.start_server_process, args=(server_port,))
        p.start()
        yield
        p.terminate()

    @pytest.fixture()
    def updater_empty(self):
        return CTGP7Updater()
    
    @pytest.fixture()
    def server_address(self,server_port):
        return "http://localhost:{}".format(server_port)

    @pytest.fixture()
    def updater(self, request, server_address, updater_empty: CTGP7Updater, tmp_path: pathlib.Path):
        updater_empty.setBaseURL(server_address + "/" + request.param + "/")
        updater_empty.setBaseDirectory(tmp_path.resolve())
        return updater_empty
    
    # Tests
    @pytest.mark.parametrize("path,isValid", [
        ("testData/data1", True),
        ("testData/data2", False)
    ])
    def test_isvalidnintendo3dsfolder(self, path, isValid):

        assert CTGP7Updater._isValidNintendo3DSSDCard(path) == isValid

    @pytest.mark.parametrize("updater", ["data1"], indirect=["updater"])
    def test_fetchversion(self, updater: CTGP7Updater):
        updater.getLatestVersion()

        assert updater.latestVersion == "1.2.3"
    
    @pytest.mark.parametrize("updater,diskSpace,extraSpace", [
        ("data1", 1000 + CTGP7Updater._SLACK_FREE_SPACE + 10, 0),
        ("data1", 1000 + CTGP7Updater._SLACK_FREE_SPACE, 0),
        ("data1", 1000 + CTGP7Updater._SLACK_FREE_SPACE - 10, 10)
    ], indirect=["updater"])
    def test_checkinstallsize(self, updater: CTGP7Updater, diskSpace, extraSpace):
        updater.loadUpdateInfo()

        assert updater._checkNeededExtraSpace(diskSpace) == extraSpace

    @pytest.mark.parametrize("updater,expectedList", [
        ("data2", [
            (0, "M", "/testfile1.bin", "/testfile1.bin"),
        ]),
        ("data3", [
            (0, "M", "/testfile1.bin", "/testfile1.bin"),
            (0, "D", "/testfile2.bin", "/testfile2.bin"),
            (0, "F", "/testfile3.bin", "/testfile3.bin"),
            (0, "T", "/testfile4.bin", "/testfile4.bin"),
        ]),
        ("data4", [
            (0, "I", "/testfile1.bin", "/testfile1.bin"),
            (0, "I", "/testfile2.bin", "/testfile2.bin"),
            (0, "M", "/testfile1.bin", "/testfile1.bin"),
            (0, "D", "/testfile2.bin", "/testfile2.bin"),
            (0, "F", "/testfile1.bin", "/testfile1.bin"),
            (0, "T", "/testfile3.bin", "/testfile3.bin"),
        ]),
        ], indirect=["updater"])
    def test_fetchinstallfilelist(self, updater: CTGP7Updater, expectedList):
        updater.loadUpdateInfo()
        entries = []
        for e in expectedList:
            entries.append(CTGP7Updater.FileListEntry(e[0], e[1], updater._buildFilePath(e[2]), updater._buildFileURL(e[3])))
        assert updater.fileList == entries
    
    @pytest.mark.parametrize("updater", ["data5"], indirect=["updater"])
    def test_filedownload(self, updater: CTGP7Updater):
        updater.loadUpdateInfo()

        lastRes = None
        for e in updater.fileList:
            lastRes = e.perform(lastRes)
            assert filecmp.cmp(pathlib.Path("testData/data5/data/" + e.fileOnlyName).resolve(), e.filePath)

    @pytest.mark.parametrize("updater", ["data6"], indirect=["updater"])
    def test_filedelete(self, updater: CTGP7Updater):
        updater.loadUpdateInfo()        

        lastRes = None
        for e in updater.fileList:
            updater.mkFoldersForFile(e.filePath)
            with open(e.filePath, "w") as f:
                f.write("hello world")
            lastRes = e.perform(lastRes)
            assert not os.path.exists(e.filePath)

    @pytest.mark.parametrize("updater", ["data7"], indirect=["updater"])
    def test_filerename(self, updater: CTGP7Updater):
        updater.loadUpdateInfo()        

        lastRes = None
        lastRandomVal = None
        for e in updater.fileList:
            if e.fileMethod == "F":
                lastRandomVal = os.urandom(16)
                updater.mkFoldersForFile(e.filePath)
                with open(e.filePath, "wb") as f:
                    f.write(lastRandomVal)
            lastRes = e.perform(lastRes)
            if e.fileMethod == "T":
                assert os.path.exists(e.filePath)
                with open(e.filePath, "rb") as f:
                    assert f.read() == lastRandomVal