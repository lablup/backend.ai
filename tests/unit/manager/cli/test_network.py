from __future__ import annotations

from click.testing import CliRunner

from ai.backend.manager.cli.network import cli


def test_network_cli_lists_overlay_key_commands() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "overlay-key-status" in result.output
    assert "rotate-overlay-key" in result.output
    assert "audit" in result.output
    assert "quarantine" in result.output


def test_rotation_requires_explicit_drain_confirmation() -> None:
    result = CliRunner().invoke(cli, ["rotate-overlay-key"])

    assert result.exit_code != 0
    assert "--confirm-drained is required" in result.output


def test_quarantine_requires_explicit_orphan_confirmation() -> None:
    result = CliRunner().invoke(cli, ["quarantine", "network/ipam/vni/100"])

    assert result.exit_code != 0
    assert "--confirm-orphaned is required" in result.output
