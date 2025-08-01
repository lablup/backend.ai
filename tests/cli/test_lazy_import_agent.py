from ai.backend.cli.loader import load_entry_points

from .helper import check_module_loaded


def test_lazy_import_agent_cli():
    load_entry_points(allowlist={"ai.backend.agent"})
    assert not check_module_loaded("ai/backend/agent/docker"), (
        "ai.backend.agent.docker should not be loaded when importing ai.backend.agent.cli"
    )
