"""CLI entry point for thrift-mock."""

import logging
import signal
import sys
import threading
from pathlib import Path

import click

from thrift_mock.handler import create_handler
from thrift_mock.parser import parse_thrift_file
from thrift_mock.server import create_mock_server

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )


@click.group()
def main() -> None:
    """Spin up mock Apache Thrift servers from .thrift IDL files."""


@main.command()
@click.option(
    "--thrift",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the .thrift IDL file.",
)
@click.option(
    "--port",
    required=True,
    type=int,
    help="Port to listen on.",
)
@click.option(
    "--transport",
    type=click.Choice(["buffered", "framed"]),
    default="buffered",
    help="Transport layer (default: buffered).",
)
@click.option(
    "--protocol",
    type=click.Choice(["binary", "compact"]),
    default="binary",
    help="Protocol layer (default: binary).",
)
@click.option(
    "--overrides",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to YAML overrides config (optional).",
)
@click.option(
    "--timeout",
    type=int,
    default=60,
    show_default=True,
    help="Client socket timeout in seconds.",
)
def serve(thrift: Path, port: int, transport: str, protocol: str, overrides: Path | None, timeout: int) -> None:
    """Start a single mock Thrift server from a .thrift IDL file."""
    _configure_logging()

    thrift_module, service_definitions = parse_thrift_file(thrift)

    if not service_definitions:
        logger.error("No services found in %s", thrift)
        sys.exit(1)

    service_name = next(iter(service_definitions))
    service_definition = service_definitions[service_name]

    strategy = None
    if overrides is not None:
        from thrift_mock.overrides import OverrideResponseStrategy, load_overrides

        service_overrides = load_overrides(overrides)
        strategy = OverrideResponseStrategy(service_overrides, thrift_module)

    handler = create_handler(service_definition, thrift_module, strategy)
    server = create_mock_server(
        thrift_module=thrift_module,
        service_name=service_name,
        handler=handler,
        port=port,
        transport=transport,
        protocol=protocol,
        timeout_seconds=timeout,
    )

    def _shutdown(signum, frame):
        logger.info("Shutting down %s server", service_name)
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Serving %s on port %d (transport=%s, protocol=%s, timeout=%ds)",
        service_name,
        port,
        transport,
        protocol,
        timeout,
    )
    server.serve()


@main.command()
@click.option(
    "--file",
    "manifest_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the manifest YAML file.",
)
def manifest(manifest_file: Path) -> None:
    """Start multiple mock Thrift servers from a manifest YAML file."""
    _configure_logging()

    from thrift_mock.orchestrator import Orchestrator, load_manifest

    configs = load_manifest(manifest_file)
    orchestrator = Orchestrator(configs)
    orchestrator.start_all()

    if orchestrator.server_count == 0:
        logger.error("No servers started successfully — check manifest and .thrift files")
        sys.exit(1)

    logger.info(
        "Started %d/%d server(s) from manifest %s",
        orchestrator.server_count,
        len(configs),
        manifest_file,
    )

    def _shutdown(signum, frame):
        logger.info("Shutting down all mock servers")
        orchestrator.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Park the main thread — servers run in daemon threads.
    threading.Event().wait()
