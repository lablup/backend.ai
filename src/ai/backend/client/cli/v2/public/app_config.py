"""Anonymous CLI commands for the public merged app config."""

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
    """Public app config commands."""


@app_config.command()
@click.argument("config_names", nargs=-1, required=True)
def get(config_names: tuple[str, ...]) -> None:
    """Read the public merged config for CONFIG_NAMES, answered in that order.

    Only public fragments contribute, so this is the pre-login view: it needs no
    credentials, and it answers the same for everyone. Use ``my app-config get`` for the
    view that also carries your domain's and your own fragments.

    A name nothing public contributes to is answered with an empty merge rather than
    dropped, so the result lines up position by position with CONFIG_NAMES.
    """
    from ai.backend.common.dto.manager.v2.app_config.request import PublicGetAppConfigsInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.public_get_app_configs(
                PublicGetAppConfigsInput(config_names=list(config_names))
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
