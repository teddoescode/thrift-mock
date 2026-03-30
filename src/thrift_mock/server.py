"""Server lifecycle — create and manage mock Thrift servers."""

import logging
from typing import Any

from thriftpy2.protocol import (
    TBinaryProtocolFactory,
    TCompactProtocolFactory,
)
from thriftpy2.rpc import make_server
from thriftpy2.transport import (
    TBufferedTransportFactory,
    TFramedTransportFactory,
)

logger = logging.getLogger(__name__)

_TRANSPORT_FACTORIES = {
    "buffered": TBufferedTransportFactory,
    "framed": TFramedTransportFactory,
}

_PROTOCOL_FACTORIES = {
    "binary": TBinaryProtocolFactory,
    "compact": TCompactProtocolFactory,
}


def create_mock_server(
    thrift_module: Any,
    service_name: str,
    handler: object,
    port: int,
    host: str = "127.0.0.1",
    transport: str = "buffered",
    protocol: str = "binary",
    timeout_seconds: int = 60,
) -> Any:
    """Create a thriftpy2 server for the given service and handler."""
    service = getattr(thrift_module, service_name)

    transport_factory = _TRANSPORT_FACTORIES[transport]()
    protocol_factory = _PROTOCOL_FACTORIES[protocol]()

    logger.info(
        "Creating server for %s on %s:%d (transport=%s, protocol=%s, timeout=%ds)",
        service_name,
        host,
        port,
        transport,
        protocol,
        timeout_seconds,
    )

    server = make_server(
        service,
        handler,
        host=host,
        port=port,
        trans_factory=transport_factory,
        proto_factory=protocol_factory,
        client_timeout=timeout_seconds * 1000,
    )

    return server
