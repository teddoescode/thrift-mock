"""Multi-server orchestration from a YAML manifest."""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from thrift_mock.handler import create_handler
from thrift_mock.parser import parse_thrift_file
from thrift_mock.server import create_mock_server

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for a single mock server instance."""

    thrift: Path
    port: int
    transport: str = "buffered"
    protocol: str = "binary"
    overrides: Path | None = None
    timeout_seconds: int = 60


def load_manifest(manifest_path: Path) -> list[ServerConfig]:
    """Load a manifest YAML and return a list of ServerConfig objects.

    Paths for 'thrift' and 'overrides' are resolved relative to the
    manifest file's own directory, so manifests are portable.
    """
    logger.debug("Loading manifest from %s", manifest_path)
    manifest_dir = manifest_path.parent

    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    configs = []
    for entry in data.get("servers", []):
        thrift_path = (manifest_dir / entry["thrift"]).resolve()

        overrides_path: Path | None = None
        if "overrides" in entry:
            overrides_path = (manifest_dir / entry["overrides"]).resolve()

        config = ServerConfig(
            thrift=thrift_path,
            port=entry["port"],
            transport=entry.get("transport", "buffered"),
            protocol=entry.get("protocol", "binary"),
            overrides=overrides_path,
            timeout_seconds=entry.get("timeout", 60),
        )
        configs.append(config)

    logger.info("Loaded manifest: %d server(s) configured", len(configs))
    return configs


class Orchestrator:
    """Manages the lifecycle of multiple mock Thrift servers.

    Each server runs in its own daemon thread.  If a server fails to
    initialise (bad IDL, port conflict, missing overrides file, etc.) the
    error is logged and that entry is skipped — remaining servers are
    unaffected.
    """

    def __init__(self, configs: list[ServerConfig]) -> None:
        self._configs = configs
        self._servers: list[Any] = []
        self._threads: list[threading.Thread] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_all(self) -> None:
        """Start every configured server.  Failures are logged and skipped."""
        for config in self._configs:
            self._start_one(config)

    def stop_all(self) -> None:
        """Gracefully stop all running servers and reset internal state."""
        for server in self._servers:
            try:
                server.close()
            except Exception as exc:
                logger.warning("Error while stopping server: %s", exc)

        self._servers.clear()
        self._threads.clear()
        logger.info("All mock servers stopped")

    @property
    def server_count(self) -> int:
        """Number of servers that started successfully."""
        return len(self._servers)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_one(self, config: ServerConfig) -> None:
        """Attempt to start a single server.  Logs and returns on any failure."""
        label = f"{config.thrift.name}:{config.port}"
        try:
            thrift_module, service_definitions = parse_thrift_file(config.thrift)

            if not service_definitions:
                logger.error("No services found in %s — skipping", config.thrift)
                return

            service_name, service_definition = next(iter(service_definitions.items()))

            strategy = None
            if config.overrides is not None:
                from thrift_mock.overrides import OverrideResponseStrategy, load_overrides

                service_overrides = load_overrides(config.overrides)
                strategy = OverrideResponseStrategy(service_overrides, thrift_module)

            handler = create_handler(service_definition, thrift_module, strategy)
            server = create_mock_server(
                thrift_module=thrift_module,
                service_name=service_name,
                handler=handler,
                port=config.port,
                transport=config.transport,
                protocol=config.protocol,
                timeout_seconds=config.timeout_seconds,
            )

            thread = threading.Thread(
                target=server.serve,
                daemon=True,
                name=f"mock-{label}",
            )
            thread.start()

            self._servers.append(server)
            self._threads.append(thread)

            logger.info(
                "Started %s on port %d (transport=%s, protocol=%s, timeout=%ds)",
                service_name,
                config.port,
                config.transport,
                config.protocol,
                config.timeout_seconds,
            )

        except Exception as exc:
            logger.error("Failed to start server for %s: %s", label, exc)
