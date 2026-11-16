from __future__ import annotations

from pathlib import Path

from ai.backend.common.plugin.cli import PluginCLIContext
from ai.backend.logging.types import LogLevel
from ai.backend.manager.cli.context import CLIContext


def test_manager_cli_context_hands_its_config_path_to_plugins() -> None:
    ctx: PluginCLIContext = CLIContext(LogLevel.INFO, Path("/etc/backend.ai/manager.toml"))

    assert isinstance(ctx, PluginCLIContext)
    assert ctx.config_path == Path("/etc/backend.ai/manager.toml")
