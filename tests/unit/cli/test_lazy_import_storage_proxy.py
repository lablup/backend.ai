from ai.backend.cli.loader import load_entry_points

from .helper import check_module_loaded


def test_lazy_import_storage_proxy_cli():
    # The CLI commands and the `server` module should use lazy imports of their internal dependencies,
    # to reduce the startup time and avoid unnecessary indirect imports of 3rd-party dependencies.
    # (See lablup/backend.ai#663, lablup/backend.ai#5327)
    load_entry_points(allowlist={"ai.backend.storage"})
    assert not check_module_loaded("ai/backend/storage/volumes"), (
        "ai.backend.storage.volumes should not be loaded when importing ai.backend.storage.cli"
    )
    assert not check_module_loaded("ai/backend/storage/api"), (
        "ai.backend.storage.apj should not be loaded when importing ai.backend.storage.cli"
    )
