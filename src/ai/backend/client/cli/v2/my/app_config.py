"""Self-service CLI commands for the caller's own merged app config."""

from __future__ import annotations

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
    run_async,
)


@click.group()
def app_config() -> None:
    """My app config commands."""


@app_config.command()
@click.argument("config_names", nargs=-1, required=True)
def get(config_names: tuple[str, ...]) -> None:
    """Read my merged config for CONFIG_NAMES, answered in that order.

    Public, my domain's and my own fragments are deep-merged by allow-list rank, so this is
    the config as it applies to me. ``fragments`` in the answer holds the ones that
    contributed, in that same order, to show where each value came from.

    A name nothing visible to me contributes to is answered with an empty merge rather than
    dropped, so the result lines up position by position with CONFIG_NAMES.
    """
    from ai.backend.common.dto.manager.v2.app_config.request import MyGetAppConfigsInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_get_app_configs(
                MyGetAppConfigsInput(config_names=list(config_names))
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
