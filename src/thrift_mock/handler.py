"""Dynamic handler creation for mock Thrift services."""

import logging
from typing import Any

from thrift_mock.defaults import generate_default_value

logger = logging.getLogger(__name__)


class ResponseStrategy:
    """Base interface for response resolution. Currently only static defaults."""

    def resolve(self, service_name: str, method_name: str, type_spec: tuple) -> Any:
        """Return the response for a given method call."""
        return generate_default_value(type_spec)


def create_handler(
    service_definition: dict[str, Any],
    thrift_module: Any,
    response_strategy: ResponseStrategy | None = None,
) -> object:
    """Create a handler object that implements all methods of a Thrift service.

    Each method returns the default value for its return type.
    """
    if response_strategy is None:
        response_strategy = ResponseStrategy()

    methods = service_definition["methods"]
    service_name = service_definition["thrift_service"].__name__

    handler_methods = {}
    for method_name, method_info in methods.items():
        return_type = method_info["return_type"]
        handler_methods[method_name] = _make_method(
            service_name, method_name, return_type, response_strategy
        )

    handler_class = type(f"{service_name}Handler", (), handler_methods)
    return handler_class()


def _make_method(
    service_name: str,
    method_name: str,
    return_type: tuple | None,
    response_strategy: ResponseStrategy,
):
    """Create a handler method that logs the call and returns the default value."""

    def method(self, *args, **kwargs):
        logger.info("CALL %s.%s(%s)", service_name, method_name, _format_args(args, kwargs))
        result = response_strategy.resolve(service_name, method_name, return_type)
        logger.info("RESPONSE %s.%s → %r", service_name, method_name, result)
        return result

    method.__name__ = method_name
    return method


def _format_args(args: tuple, kwargs: dict) -> str:
    """Format call arguments for logging."""
    parts = [repr(a) for a in args]
    parts.extend(f"{k}={v!r}" for k, v in kwargs.items())
    return ", ".join(parts)
