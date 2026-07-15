"""Smoke tests for the ``ag kernel`` command wiring (no live agent needed)."""

from __future__ import annotations

from click.testing import CliRunner

from ai.backend.agent.cli.kernel import cli


def test_kernel_group_lists_all_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for name in (
        "create",
        "destroy",
        "inspect",
        "check-running",
        "pull",
        "assign-port",
        "local-network",
    ):
        assert name in result.output


def test_local_network_subgroup() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["local-network", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "destroy" in result.output


def test_create_help_renders() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["create", "--help"])
    assert result.exit_code == 0
    assert "--spec" in result.output
    assert "--image" in result.output
    assert "--manager-keypair" in result.output
