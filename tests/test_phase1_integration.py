"""Phase 1 integration test: parse IDL, generate defaults, start server, verify via client."""

import threading
import time
from pathlib import Path

from thriftpy2.rpc import make_client

from thrift_mock.parser import parse_thrift_file
from thrift_mock.handler import create_handler
from thrift_mock.server import create_mock_server

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_THRIFT = FIXTURES_DIR / "simple_service.thrift"


def _start_server_in_thread(server):
    """Start a thrift server in a background thread."""
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    time.sleep(0.3)  # Give server time to bind
    return thread


class TestSimpleServiceDefaults:
    """Verify that a mock server returns correct default values for all basic types."""

    def setup_method(self):
        self.port = 9777
        self.thrift_module, service_definitions = parse_thrift_file(SIMPLE_THRIFT)
        handler = create_handler(service_definitions["SimpleService"], self.thrift_module)
        self.server = create_mock_server(
            thrift_module=self.thrift_module,
            service_name="SimpleService",
            handler=handler,
            port=self.port,
        )
        self._thread = _start_server_in_thread(self.server)

    def teardown_method(self):
        if hasattr(self, "server") and self.server is not None:
            self.server.close()

    def _make_client(self):
        service = getattr(self.thrift_module, "SimpleService")
        return make_client(service, "127.0.0.1", self.port)

    def test_i32_method_returns_zero_default(self):
        client = self._make_client()
        result = client.getAge()
        assert result == 0

    def test_string_method_returns_empty_default(self):
        client = self._make_client()
        result = client.getName()
        assert result == ""

    def test_bool_method_returns_false_default(self):
        client = self._make_client()
        result = client.isActive()
        assert result is False

    def test_double_method_returns_zero_default(self):
        client = self._make_client()
        result = client.getScore()
        assert result == 0.0

    def test_struct_method_returns_populated_default(self):
        client = self._make_client()
        user = client.getUser()
        assert user.id == 0
        assert user.name == ""
        assert user.active is False

    def test_enum_method_returns_first_value_default(self):
        client = self._make_client()
        result = client.getStatus()
        # First enum value is UNKNOWN = 0
        assert result == 0

    def test_list_method_returns_empty_list_default(self):
        client = self._make_client()
        result = client.getTags()
        assert result == []

    def test_map_method_returns_empty_dict_default(self):
        client = self._make_client()
        result = client.getCounts()
        assert result == {}

    def test_void_method_returns_none(self):
        client = self._make_client()
        result = client.ping()
        assert result is None
