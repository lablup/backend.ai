from ai.backend.cli.loader import load_entry_points

from .helper import modules_loaded_by_cli


def test_lazy_import_agent_cli() -> None:
    # The CLI commands and the `server` module should use lazy imports of their internal dependencies,
    # to reduce the startup time and avoid unnecessary indirect imports of 3rd-party dependencies.
    # (See lablup/backend.ai#663, lablup/backend.ai#5327)
    loaded_modules = modules_loaded_by_cli(load_entry_points, "ai.backend.agent")
    assert "ai.backend.agent.docker" not in loaded_modules, (
        "ai.backend.agent.docker should not be loaded when importing ai.backend.agent.cli"
    )
    assert "ai.backend.agent.dummy" not in loaded_modules, (
        "ai.backend.agent.dummy should not be loaded when importing ai.backend.agent.cli"
    )
    assert "ai.backend.agent.kubernetes" not in loaded_modules, (
        "ai.backend.agent.kubernetes should not be loaded when importing ai.backend.agent.cli"
    )
    assert "ai.backend.agent.stage" not in loaded_modules, (
        "ai.backend.agent.stage should not be loaded when importing ai.backend.agent.cli"
    )
