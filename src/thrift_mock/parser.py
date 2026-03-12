"""Thrift IDL parsing — extracts service definitions and method signatures."""

import logging
from pathlib import Path
from typing import Any

import thriftpy2

logger = logging.getLogger(__name__)


def parse_thrift_file(
    thrift_file_path: Path,
) -> tuple[Any, dict[str, dict[str, Any]]]:
    """Parse a .thrift file and return the loaded module and service definitions.

    Returns:
        A tuple of (thrift_module, services) where services is a dict like:
        {
            "SimpleService": {
                "methods": {
                    "getAge": {"return_type": <thrift type spec>},
                    "ping": {"return_type": None},
                    ...
                },
                "thrift_service": <thriftpy2 service class>,
            }
        }
    """
    thrift_path = Path(thrift_file_path)
    logger.debug("Parsing thrift file: %s", thrift_path)

    thrift_module = thriftpy2.load(str(thrift_path))
    services = {}

    for attribute_name in dir(thrift_module):
        attribute = getattr(thrift_module, attribute_name)
        if _is_thrift_service(attribute):
            service_name = attribute_name
            methods = _extract_methods(attribute)
            services[service_name] = {
                "methods": methods,
                "thrift_service": attribute,
            }
            logger.debug(
                "Found service %s with methods: %s",
                service_name,
                list(methods.keys()),
            )

    return thrift_module, services


def _is_thrift_service(attribute: Any) -> bool:
    """Check if a module attribute is a thriftpy2 service class."""
    return isinstance(attribute, type) and hasattr(attribute, "thrift_services")


def _extract_methods(service_class: type) -> dict[str, dict[str, Any]]:
    """Extract method names and return type info from a thriftpy2 service class."""
    methods = {}
    for method_name in service_class.thrift_services:
        # Result classes are nested on the service class, not the module
        result_class = getattr(service_class, f"{method_name}_result", None)

        return_type = None
        if result_class is not None and hasattr(result_class, "thrift_spec"):
            thrift_spec = result_class.thrift_spec
            # Field 0 is the return value ("success")
            if 0 in thrift_spec:
                return_type = thrift_spec[0]

        methods[method_name] = {
            "return_type": return_type,
        }

    return methods
