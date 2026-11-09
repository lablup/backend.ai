from unittest.mock import MagicMock

import click
import pytest

from ai.backend.cli import loader


def _entrypoint(name: str, command: click.Command) -> MagicMock:
    entrypoint = MagicMock()
    entrypoint.name = name
    entrypoint.load.return_value = command
    return entrypoint


@pytest.fixture
def fresh_main(monkeypatch: pytest.MonkeyPatch) -> click.Group:
    group = click.Group("backend.ai")
    monkeypatch.setattr(loader, "main", group)
    return group


def _scanning(monkeypatch: pytest.MonkeyPatch, *entrypoints: MagicMock) -> None:
    monkeypatch.setattr(loader, "scan_entrypoints", lambda *args, **kwargs: iter(entrypoints))


class TestLoadEntryPoints:
    def test_a_subcommand_scanned_before_its_group_still_joins_it(
        self, monkeypatch: pytest.MonkeyPatch, fresh_main: click.Group
    ) -> None:
        mgr = click.Group("mgr")
        network = click.Command("network")
        _scanning(monkeypatch, _entrypoint("mgr.network", network), _entrypoint("mgr", mgr))

        loader.load_entry_points()

        assert fresh_main.commands["mgr"] is mgr
        assert mgr.commands["network"] is network

    def test_a_subcommand_whose_group_is_not_installed_is_left_out(
        self, monkeypatch: pytest.MonkeyPatch, fresh_main: click.Group
    ) -> None:
        _scanning(monkeypatch, _entrypoint("mgr.network", click.Command("network")))

        loader.load_entry_points()

        assert "mgr" not in fresh_main.commands

    def test_the_underscore_group_is_merged_at_the_top(
        self, monkeypatch: pytest.MonkeyPatch, fresh_main: click.Group
    ) -> None:
        extras = click.Group("_", commands={"hello": click.Command("hello")})
        _scanning(monkeypatch, _entrypoint("_", extras))

        loader.load_entry_points()

        assert "hello" in fresh_main.commands
