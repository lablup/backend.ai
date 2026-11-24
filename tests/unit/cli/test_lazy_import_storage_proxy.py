from ai.backend.cli.loader import load_entry_points

from .helper import modules_loaded_by_cli


def test_lazy_import_storage_proxy_cli() -> None:
    # The CLI commands and the `server` module should use lazy imports of their internal dependencies,
    # to reduce the startup time and avoid unnecessary indirect imports of 3rd-party dependencies.
    # (See lablup/backend.ai#663, lablup/backend.ai#5327)
    loaded_modules = modules_loaded_by_cli(load_entry_points, "ai.backend.storage")
    assert "ai.backend.storage.volumes" not in loaded_modules, (
        "ai.backend.storage.volumes should not be loaded when importing ai.backend.storage.cli"
    )
    assert "ai.backend.storage.api" not in loaded_modules, (
        "ai.backend.storage.api should not be loaded when importing ai.backend.storage.cli"
    )
