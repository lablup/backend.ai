from ai.backend.cli.loader import load_entry_points

from .helper import check_module_loaded


def test_lazy_import_agent_cli():
    # The CLI commands and the `server` module should use lazy imports of their internal dependencies,
    # to reduce the startup time and avoid unnecessary indirect imports of 3rd-party dependencies.
    # (See lablup/backend.ai#663, lablup/backend.ai#5327)
    load_entry_points(allowlist={"ai.backend.agent"})
    assert not check_module_loaded("ai/backend/agent/docker"), (
        "ai.backend.agent.docker should not be loaded when importing ai.backend.agent.cli"
    )
    assert not check_module_loaded("ai/backend/agent/dummy"), (
        "ai.backend.agent.dummy should not be loaded when importing ai.backend.agent.cli"
    )
    assert not check_module_loaded("ai/backend/agent/kubernetes"), (
        "ai.backend.agent.kubernetes should not be loaded when importing ai.backend.agent.cli"
    )
    assert not check_module_loaded("ai/backend/agent/stage"), (
        "ai.backend.agent.stage should not be loaded when importing ai.backend.agent.cli"
    )
