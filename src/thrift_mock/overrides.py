"""Config loading and override application for mock Thrift servers."""

import logging
from pathlib import Path
from typing import Any

import yaml
from thriftpy2.thrift import TType

from thrift_mock.defaults import generate_default_value
from thrift_mock.handler import ResponseStrategy

logger = logging.getLogger(__name__)


def load_overrides(config_path: Path) -> dict[str, Any]:
    """Load a YAML overrides config and return the services override dict."""
    logger.debug("Loading overrides from %s", config_path)
    with open(config_path) as f:
        config = yaml.safe_load(f)
    services = config.get("services", {})
    logger.info("Loaded overrides for services: %s", list(services.keys()))
    return services


class OverrideResponseStrategy(ResponseStrategy):
    """Returns configured override values, falling back to generated defaults."""

    def __init__(self, service_overrides: dict[str, Any], thrift_module: Any) -> None:
        self._service_overrides = service_overrides
        self._thrift_module = thrift_module

    def resolve(self, service_name: str, method_name: str, type_spec: tuple | None) -> Any:
        method_config = (
            self._service_overrides
            .get(service_name, {})
            .get(method_name, {})
        )

        if "throw" in method_config:
            self._raise_configured_exception(method_config["throw"])

        if "return" in method_config:
            raw_value = method_config["return"]
            logger.debug("Override for %s.%s → %r", service_name, method_name, raw_value)
            return self._coerce_value(raw_value, type_spec)

        return generate_default_value(type_spec)

    def _raise_configured_exception(self, exception_name: str) -> None:
        exception_class = getattr(self._thrift_module, exception_name, None)
        if exception_class is None:
            raise ValueError(f"Exception {exception_name!r} not found in thrift module")
        logger.debug("Raising configured exception %s", exception_name)
        raise exception_class()

    def _coerce_value(self, raw_value: Any, type_spec: tuple | None) -> Any:
        """Convert a raw config value to the appropriate Thrift type."""
        if type_spec is None or raw_value is None:
            return raw_value

        type_code = type_spec[0]

        if type_code == TType.STRUCT and isinstance(raw_value, dict):
            struct_class = type_spec[2]
            return self._build_struct(raw_value, struct_class)

        return raw_value

    def _build_struct(self, data: dict, struct_class: type) -> Any:
        """Construct a Thrift struct instance from a dict of field values."""
        instance = struct_class()

        if not hasattr(struct_class, "thrift_spec"):
            return instance

        for field_spec in struct_class.thrift_spec.values():
            field_name = field_spec[1]
            if field_name in data:
                setattr(instance, field_name, self._coerce_value(data[field_name], field_spec))
            else:
                setattr(instance, field_name, generate_default_value(field_spec))

        return instance
