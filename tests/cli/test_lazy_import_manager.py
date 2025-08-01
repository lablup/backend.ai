from ai.backend.cli.loader import load_entry_points

from .helper import check_module_loaded


def test_lazy_import_manager_cli():
    load_entry_points(allowlist={"ai.backend.manager"})
    assert not check_module_loaded("ai/backend/manager/models"), (
        "ai.backend.manager.models should not be loaded when importing ai.backend.manager.cli"
    )
