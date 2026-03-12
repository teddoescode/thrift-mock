"""CLI entry point for thrift-mock."""

import logging
import signal
import sys
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


@click.command()
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
def main(thrift: Path, port: int, transport: str, protocol: str) -> None:
    """Spin up a mock Thrift server from a .thrift IDL file."""
    _configure_logging()

    thrift_module, service_definitions = parse_thrift_file(thrift)

    if not service_definitions:
        logger.error("No services found in %s", thrift)
        sys.exit(1)

    # Use the first service found in the file
    service_name = next(iter(service_definitions))
    service_definition = service_definitions[service_name]

    handler = create_handler(service_definition, thrift_module)
    server = create_mock_server(
        thrift_module=thrift_module,
        service_name=service_name,
        handler=handler,
        port=port,
        transport=transport,
        protocol=protocol,
    )

    def _shutdown(signum, frame):
        logger.info("Shutting down %s server", service_name)
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Serving %s on port %d (transport=%s, protocol=%s)",
        service_name,
        port,
        transport,
        protocol,
    )
    server.serve()
