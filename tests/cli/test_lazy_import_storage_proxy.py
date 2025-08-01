from ai.backend.cli.loader import load_entry_points

from .helper import check_module_loaded


def test_lazy_import_storage_proxy_cli():
    load_entry_points(allowlist={"ai.backend.storage"})
    assert not check_module_loaded("ai/backend/storage/volumes"), (
        "ai.backend.storage.volumes should not be loaded when importing ai.backend.storage.cli"
    )
