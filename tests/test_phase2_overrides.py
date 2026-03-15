"""Phase 2 integration tests: response overrides and exception simulation."""

import threading
import time
from pathlib import Path

import pytest
from thriftpy2.rpc import make_client

from thrift_mock.handler import create_handler
from thrift_mock.overrides import OverrideResponseStrategy, load_overrides
from thrift_mock.parser import parse_thrift_file
from thrift_mock.server import create_mock_server

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_THRIFT = FIXTURES_DIR / "simple_service.thrift"
TEST_THRIFT = FIXTURES_DIR / "test_service.thrift"
SIMPLE_OVERRIDES = FIXTURES_DIR / "simple_overrides.yaml"
EXCEPTION_OVERRIDES = FIXTURES_DIR / "exception_overrides.yaml"


def _start_server_in_thread(server):
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    time.sleep(0.3)
    return thread


class TestScalarOverrides:
    """Overridden scalar methods return the configured value; others return defaults."""

    def setup_method(self):
        self.port = 9778
        self.thrift_module, service_definitions = parse_thrift_file(SIMPLE_THRIFT)
        overrides = load_overrides(SIMPLE_OVERRIDES)
        strategy = OverrideResponseStrategy(overrides, self.thrift_module)
        handler = create_handler(
            service_definitions["SimpleService"], self.thrift_module, strategy
        )
        self.server = create_mock_server(
            thrift_module=self.thrift_module,
            service_name="SimpleService",
            handler=handler,
            port=self.port,
        )
        _start_server_in_thread(self.server)

    def teardown_method(self):
        if hasattr(self, "server"):
            self.server.close()

    def _make_client(self):
        return make_client(self.thrift_module.SimpleService, "127.0.0.1", self.port)

    def test_overridden_i32_returns_configured_value(self):
        client = self._make_client()
        assert client.getAge() == 42

    def test_overridden_string_returns_configured_value(self):
        client = self._make_client()
        assert client.getName() == "Alice"

    def test_non_overridden_method_returns_default(self):
        client = self._make_client()
        assert client.isActive() is False

    def test_non_overridden_double_returns_zero_default(self):
        client = self._make_client()
        assert client.getScore() == 0.0


class TestStructOverride:
    """A dict override is correctly reconstructed as a Thrift struct."""

    def setup_method(self):
        self.port = 9779
        self.thrift_module, service_definitions = parse_thrift_file(SIMPLE_THRIFT)
        overrides = load_overrides(SIMPLE_OVERRIDES)
        strategy = OverrideResponseStrategy(overrides, self.thrift_module)
        handler = create_handler(
            service_definitions["SimpleService"], self.thrift_module, strategy
        )
        self.server = create_mock_server(
            thrift_module=self.thrift_module,
            service_name="SimpleService",
            handler=handler,
            port=self.port,
        )
        _start_server_in_thread(self.server)

    def teardown_method(self):
        if hasattr(self, "server"):
            self.server.close()

    def _make_client(self):
        return make_client(self.thrift_module.SimpleService, "127.0.0.1", self.port)

    def test_overridden_struct_fields_match_config(self):
        client = self._make_client()
        user = client.getUser()
        assert user.id == 99
        assert user.name == "Bob"
        assert user.active is True


class TestExceptionSimulation:
    """A method configured with 'throw' raises the named Thrift exception."""

    def setup_method(self):
        self.port = 9780
        self.thrift_module, service_definitions = parse_thrift_file(TEST_THRIFT)
        overrides = load_overrides(EXCEPTION_OVERRIDES)
        strategy = OverrideResponseStrategy(overrides, self.thrift_module)
        handler = create_handler(
            service_definitions["TestService"], self.thrift_module, strategy
        )
        self.server = create_mock_server(
            thrift_module=self.thrift_module,
            service_name="TestService",
            handler=handler,
            port=self.port,
        )
        _start_server_in_thread(self.server)

    def teardown_method(self):
        if hasattr(self, "server"):
            self.server.close()

    def _make_client(self):
        return make_client(self.thrift_module.TestService, "127.0.0.1", self.port)

    def test_configured_throw_raises_thrift_exception(self):
        client = self._make_client()
        with pytest.raises(self.thrift_module.UserNotFoundException):
            client.getUser(1)

    def test_non_configured_method_returns_default(self):
        client = self._make_client()
        assert client.getCount() == 0
