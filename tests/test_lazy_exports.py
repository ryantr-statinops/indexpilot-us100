"""Lazy package exports preserve implementation identity and defer loading."""

from types import SimpleNamespace

from indexpilot_us100 import _exports


def test_declared_export_is_loaded_once_and_cached(monkeypatch):
    value = object()
    calls = []

    def load(module_name, package):
        calls.append((module_name, package))
        return SimpleNamespace(Thing=value)

    monkeypatch.setattr(_exports, "import_module", load)
    namespace = {}
    mapping = {"Thing": (".core", "Thing")}
    assert _exports.resolve_export("example", "Thing", mapping, namespace) is value
    assert namespace["Thing"] is value
    assert _exports.resolve_export("example", "Thing", mapping, namespace) is value
    assert calls == [(".core", "example")]


def test_unknown_export_raises_attribute_error_without_importing(monkeypatch):
    import pytest

    def fail_import(*args):
        pytest.fail("unknown exports must not import implementation modules")

    monkeypatch.setattr(_exports, "import_module", fail_import)
    namespace = {}
    with pytest.raises(AttributeError, match="'example'.*'Missing'"):
        _exports.resolve_export("example", "Missing", {"Thing": (".core", "Thing")}, namespace)
    assert namespace == {}


def test_failed_export_load_is_not_cached(monkeypatch):
    import pytest

    calls = []

    def fail_import(*args):
        calls.append(args)
        raise ImportError("implementation unavailable")

    monkeypatch.setattr(_exports, "import_module", fail_import)
    namespace = {}
    mapping = {"Thing": (".core", "Thing")}
    with pytest.raises(ImportError, match="implementation unavailable"):
        _exports.resolve_export("example", "Thing", mapping, namespace)
    assert namespace == {}
    assert calls == [(".core", "example")]
