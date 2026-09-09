from __future__ import annotations

from click.testing import CliRunner

from ai.backend.agent.cli.__main__ import main


def test_agent_cli_lists_privnet_daemon() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "start-privnet" in result.output


def test_privnet_daemon_help_renders() -> None:
    result = CliRunner().invoke(main, ["start-privnet", "--help"])

    assert result.exit_code == 0
    assert "privileged session-network daemon" in result.output
