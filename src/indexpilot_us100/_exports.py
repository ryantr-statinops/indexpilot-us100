"""Resolve package facade exports without eagerly importing implementation modules."""

from collections.abc import Mapping, MutableMapping
from importlib import import_module
from typing import Any


def resolve_export(
    package: str,
    name: str,
    exports: Mapping[str, tuple[str, str]],
    namespace: MutableMapping[str, Any],
) -> Any:
    """Load a declared export once and cache the original implementation object."""
    try:
        module_name, attribute = exports[name]
    except KeyError:
        raise AttributeError(f"module {package!r} has no attribute {name!r}") from None
    if name in namespace:
        return namespace[name]
    module = import_module(module_name, package)
    value = getattr(module, attribute)
    namespace[name] = value
    return value
