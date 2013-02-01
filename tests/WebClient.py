"""
.. codeauthor: mnl
"""
import unittest
from errno import ETIMEDOUT
from circuits_bricks.web.client import Client
from circuits.core.manager import Manager
from circuits.web.servers import BaseServer
from circuits.web.controllers import BaseController, expose
from circuits.web.dispatchers.dispatcher import Dispatcher
import time
from circuits.web.client import Request
from circuits_bricks.core.timers import Timer
from circuits.core.events import Event
from circuits.core.handlers import handler

class Root(BaseController):

    @expose("test")
    def test(self):
        return "Hello!"

    @expose("test_timeout")
    def test_timeout(self):
        Timer(5, Event.create("response_ready"), self).register(self)
        yield self.waitEvent("response_ready", self)
        yield "Hello!"


class Test(unittest.TestCase):

    def setUp(self):
        self.manager = Manager()
        # Debugger().register(self.manager)
    
        self.server = BaseServer(("localhost", 8123)) 
        self.server.register(self.manager);
        Dispatcher().register(self.server)
        Root().register(self.manager)
        self.manager.start()

    def tearDown(self):
        self.manager.stop()

    def test_absolut(self):
        app = Client("http://localhost:8123/hallo", channel="TestClient")
        app.start()
        app.fire(Request("GET", "http://localhost:8123/test"))
        for i in range(100):
            if app.response:
                break
            time.sleep(0.010)
        
        response = app.response
        assert response.status == 200
        assert response.message == "OK"

        s = response.read()
        assert s == b"Hello!"
        app.stop()

    def test_relative(self):
        app = Client("http://localhost:8123/hallo", channel="TestClient")
        app.start()
        app.fire(Request("GET", "test"))
        for i in range(10000):
            if app.response:
                break
            time.sleep(0.010)
        
        response = app.response
        assert response.status == 200
        assert response.message == "OK"

        s = response.read()
        assert s == b"Hello!"
        app.stop()

    def test_timeout(self):
        app = Client("http://localhost:8123/hallo", channel="TestClient")
        self.error = None
        @handler("error")
        def _on_error(_, e):
            self.error = e
        app.addHandler(_on_error)
        app.start()
        evt = Request("GET", "test_timeout")
        evt.timeout = 0.5
        app.fire(evt)
        for i in range(10000):
            if app.response or self.error:
                break
            time.sleep(0.010)
        
        assert self.error == ETIMEDOUT
        app.stop()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()