"""Guards the import side effect that the `backendai_cli_v10` `_` entry point exists for."""

import click


def test_client_command_groups_stay_registered(cli_entrypoint: click.Group) -> None:
    """
    Loading the `_` entry point imports `ai.backend.client.cli`, whose `__init__` registers
    every client group onto `ai.backend.cli.main:main`. Nothing else triggers that import,
    so a cleanup of `client/cli/main.py` would silently empty the CLI without this test.
    """
    assert {"service", "admin", "vfolder", "session", "app", "apps"} <= set(cli_entrypoint.commands)
