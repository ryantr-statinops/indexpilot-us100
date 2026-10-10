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
