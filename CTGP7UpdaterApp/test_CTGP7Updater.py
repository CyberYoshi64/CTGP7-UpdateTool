import pathlib
import pytest
import http.server
import socketserver
import multiprocessing
import socket
from contextlib import closing
import os

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

    @pytest.mark.parametrize("updater", ["data2"], indirect=["updater"])
    def test_fetchinstallfilelistModify(self, updater: CTGP7Updater):
        updater.loadUpdateInfo()
        fileList = [
            CTGP7Updater.FileListEntry(0, "I", updater._buildFilePath("/testfile1.bin"), updater._buildFileURL("/testfile1.bin")),
            CTGP7Updater.FileListEntry(0, "M", updater._buildFilePath("/testfile2.bin"), updater._buildFileURL("/testfile2.bin")),
            CTGP7Updater.FileListEntry(0, "M", updater._buildFilePath("/testfile1.bin"), updater._buildFileURL("/testfile1.bin")),
        ]

        assert updater.fileList == fileList