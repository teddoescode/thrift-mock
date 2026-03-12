"""Generate default (zero) values for Thrift types.

thriftpy2 type spec format (from thrift_spec dicts):
    Simple:  (type_code, field_name, required)
    Struct:  (TType.STRUCT, field_name, struct_class, required)
    Enum:    (TType.I32, field_name, enum_class, required)
    List:    (TType.LIST, field_name, element_type_code, required)
    Map:     (TType.MAP, field_name, (key_type, val_type), required)
"""

import logging
from typing import Any

from thriftpy2.thrift import TType

logger = logging.getLogger(__name__)

_SIMPLE_DEFAULTS: dict[int, Any] = {
    TType.BOOL: False,
    TType.BYTE: 0,
    TType.I16: 0,
    TType.I32: 0,
    TType.I64: 0,
    TType.DOUBLE: 0.0,
    TType.STRING: "",
    TType.BINARY: b"",
}


def generate_default_value(type_spec: tuple | None) -> Any:
    """Generate a default value for a thriftpy2 type specification."""
    if type_spec is None:
        return None

    type_code = type_spec[0]

    # Enums are encoded as I32 with the enum class as the third element
    if type_code == TType.I32 and len(type_spec) >= 4 and isinstance(type_spec[2], type):
        return _generate_default_enum(type_spec[2])

    if type_code in _SIMPLE_DEFAULTS:
        return _SIMPLE_DEFAULTS[type_code]

    if type_code == TType.STRUCT:
        return _generate_default_struct(type_spec)

    if type_code == TType.LIST:
        return []

    if type_code == TType.SET:
        return set()

    if type_code == TType.MAP:
        return {}

    logger.warning("Unknown type code %s, returning None", type_code)
    return None


def _generate_default_enum(enum_class: type) -> int:
    """Return the first defined value of an enum class."""
    enum_values = [
        (name, value)
        for name, value in vars(enum_class).items()
        if not name.startswith("_") and isinstance(value, int)
    ]
    if enum_values:
        # Sort by value to get the first defined
        enum_values.sort(key=lambda pair: pair[1])
        return enum_values[0][1]
    return 0


def _generate_default_struct(type_spec: tuple) -> Any:
    """Create a struct instance with all fields set to their default values."""
    struct_class = type_spec[2]
    instance = struct_class()

    if hasattr(struct_class, "thrift_spec"):
        for field_spec in struct_class.thrift_spec.values():
            field_name = field_spec[1]
            field_default = generate_default_value(field_spec)
            setattr(instance, field_name, field_default)

    return instance
