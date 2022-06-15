from time import time
import pytest
import http.server
import socketserver
import multiprocessing
import socket
from contextlib import closing
import os
import time

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
    def updater(self):
        return CTGP7Updater()
    
    @pytest.fixture()
    def server_address(self,server_port):
        return "http://localhost:{}".format(server_port)

    @pytest.fixture()
    def updater_data1(self, server_address, updater: CTGP7Updater):
        updater.setBaseURL(server_address + "/data1/")
        return updater
    
    def test_isvalidnintendo3dsfolder(self, updater_data1: CTGP7Updater):

        assert True

    def test_fetchversion(self, updater_data1: CTGP7Updater):
        updater_data1.getLatestVersion()

        assert updater_data1.latestVersion == "1.2.3"