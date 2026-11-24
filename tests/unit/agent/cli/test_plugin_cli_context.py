from __future__ import annotations

from pathlib import Path

from ai.backend.agent.cli.context import CLIContext
from ai.backend.common.plugin.cli import PluginCLIContext
from ai.backend.logging.types import LogLevel


def test_agent_cli_context_hands_its_config_path_to_plugins() -> None:
    ctx: PluginCLIContext = CLIContext(LogLevel.INFO, Path("/etc/backend.ai/agent.toml"))

    assert isinstance(ctx, PluginCLIContext)
    assert ctx.config_path == Path("/etc/backend.ai/agent.toml")
