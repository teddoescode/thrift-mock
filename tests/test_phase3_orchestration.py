"""Phase 3 integration tests: multi-server orchestration from a manifest."""

import time
from pathlib import Path

import pytest
from thriftpy2.rpc import make_client

from thrift_mock.orchestrator import Orchestrator, ServerConfig, load_manifest
from thrift_mock.parser import parse_thrift_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MANIFEST = FIXTURES_DIR / "manifest.yaml"
MANIFEST_BAD = FIXTURES_DIR / "manifest_bad_server.yaml"
MANIFEST_WITH_OVERRIDES = FIXTURES_DIR / "manifest_with_overrides.yaml"


# ---------------------------------------------------------------------------
# Manifest loading (pure data, no servers started)
# ---------------------------------------------------------------------------


class TestManifestLoading:
    """load_manifest parses YAML and resolves paths relative to the manifest."""

    def test_returns_correct_server_count(self):
        configs = load_manifest(MANIFEST)
        assert len(configs) == 2

    def test_thrift_paths_are_resolved_to_absolute_files(self):
        configs = load_manifest(MANIFEST)
        for config in configs:
            assert config.thrift.is_file(), f"Expected file: {config.thrift}"

    def test_defaults_are_applied_when_fields_omitted(self):
        configs = load_manifest(MANIFEST)
        assert configs[0].transport == "buffered"
        assert configs[0].protocol == "binary"
        assert configs[0].overrides is None

    def test_overrides_path_resolved_when_present(self):
        configs = load_manifest(MANIFEST_WITH_OVERRIDES)
        assert configs[0].overrides is not None
        assert configs[0].overrides.is_file()

    def test_port_is_loaded_correctly(self):
        configs = load_manifest(MANIFEST)
        assert configs[0].port == 9791
        assert configs[1].port == 9792


# ---------------------------------------------------------------------------
# Orchestrator lifecycle — all servers healthy
# ---------------------------------------------------------------------------


class TestOrchestratorLifecycle:
    """All servers in a valid manifest start and are reachable."""

    def setup_method(self):
        self.orchestrator = Orchestrator(load_manifest(MANIFEST))
        self.orchestrator.start_all()
        time.sleep(0.4)

    def teardown_method(self):
        self.orchestrator.stop_all()

    def test_all_configured_servers_start_successfully(self):
        assert self.orchestrator.server_count == 2

    def test_first_server_is_reachable_and_returns_defaults(self):
        thrift_module, _ = parse_thrift_file(FIXTURES_DIR / "simple_service.thrift")
        client = make_client(thrift_module.SimpleService, "127.0.0.1", 9791)
        assert client.getAge() == 0

    def test_second_server_is_reachable_and_returns_defaults(self):
        thrift_module, _ = parse_thrift_file(FIXTURES_DIR / "test_service.thrift")
        client = make_client(thrift_module.TestService, "127.0.0.1", 9792)
        assert client.getCount() == 0

    def test_stop_all_shuts_down_all_servers(self):
        self.orchestrator.stop_all()
        # server_count resets to zero after stop
        assert self.orchestrator.server_count == 0


# ---------------------------------------------------------------------------
# Fault tolerance — one bad server config must not kill the rest
# ---------------------------------------------------------------------------


class TestOrchestratorFaultTolerance:
    """A bad server definition is skipped; remaining servers still start."""

    def setup_method(self):
        self.orchestrator = Orchestrator(load_manifest(MANIFEST_BAD))
        self.orchestrator.start_all()
        time.sleep(0.4)

    def teardown_method(self):
        self.orchestrator.stop_all()

    def test_bad_server_is_skipped(self):
        # manifest has 2 entries; one has a non-existent .thrift file
        assert self.orchestrator.server_count == 1

    def test_good_server_still_starts_when_sibling_fails(self):
        thrift_module, _ = parse_thrift_file(FIXTURES_DIR / "simple_service.thrift")
        client = make_client(thrift_module.SimpleService, "127.0.0.1", 9793)
        assert client.getAge() == 0


# ---------------------------------------------------------------------------
# Overrides wired through manifest
# ---------------------------------------------------------------------------


class TestOrchestratorWithOverrides:
    """Overrides specified in the manifest are applied to the server."""

    def setup_method(self):
        self.orchestrator = Orchestrator(load_manifest(MANIFEST_WITH_OVERRIDES))
        self.orchestrator.start_all()
        time.sleep(0.4)

    def teardown_method(self):
        self.orchestrator.stop_all()

    def test_overrides_applied_from_manifest(self):
        thrift_module, _ = parse_thrift_file(FIXTURES_DIR / "simple_service.thrift")
        client = make_client(thrift_module.SimpleService, "127.0.0.1", 9795)
        # simple_overrides.yaml sets getAge → 42
        assert client.getAge() == 42

    def test_non_overridden_method_still_returns_default(self):
        thrift_module, _ = parse_thrift_file(FIXTURES_DIR / "simple_service.thrift")
        client = make_client(thrift_module.SimpleService, "127.0.0.1", 9795)
        assert client.isActive() is False
