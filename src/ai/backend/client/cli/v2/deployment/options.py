"""CLI commands for the per-deployment ``options`` surface."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def options() -> None:
    """Manage per-deployment options (timeouts, etc.)."""


@options.command(name="get")
@click.argument("deployment_id", type=str)
def get_options(deployment_id: str) -> None:
    """Show the current options surface of a deployment."""
    from ai.backend.common.identifier.deployment import DeploymentID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get_options(DeploymentID(UUID(deployment_id)))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


def _parse_timeout_value(raw: str) -> int | None:
    """Parse a handler timeout value string.

    Accepts ``null`` / ``none`` (case-insensitive) for explicit no-timeout,
    or a positive integer (seconds).
    """
    normalized = raw.strip()
    if normalized.lower() in ("null", "none"):
        return None
    value = int(normalized)
    if value < 1:
        raise click.BadParameter(
            f"timeout must be a positive integer or 'null' (got {raw!r})",
        )
    return value


def _parse_default(raw: str | None) -> int | None:
    if raw is None:
        return None
    return _parse_timeout_value(raw)


@options.command(name="replace")
@click.argument("deployment_id", type=str)
@click.option(
    "--default-timeout",
    "default_timeout",
    default=None,
    type=str,
    help=(
        "Fallback timeout in seconds (positive integer), or 'null' to make the "
        "default unbounded. Omit to send null (i.e. unbounded)."
    ),
)
@click.option(
    "--handler",
    "handlers",
    multiple=True,
    help=(
        "Per-handler override in the form 'name=seconds' or 'name=null'. "
        "Repeatable. Duplicate handler names are rejected by the server."
    ),
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=str,
    help=(
        "Load the full request body from a JSON file when prefixed with '@' "
        "(e.g., --config @options.json). Overrides --default-timeout / --handler."
    ),
)
def replace_options(
    deployment_id: str,
    default_timeout: str | None,
    handlers: tuple[str, ...],
    config_path: str | None,
) -> None:
    """Fully replace the options surface of a deployment.

    Primary input: individual --default-timeout and repeated --handler flags.
    Secondary input: a JSON file via --config @file.json containing either
    a ``ReplaceDeploymentOptionsInput`` payload or the bare ``options`` dict.
    """
    from ai.backend.common.dto.manager.v2.deployment.request import (
        ReplaceDeploymentOptionsInput,
    )
    from ai.backend.common.dto.manager.v2.deployment_options import (
        DeploymentHandlerOptionsInput,
        DeploymentOptionsInput,
    )
    from ai.backend.common.dto.manager.v2.session_options import (
        HandlerOptionsEntryInput,
        HandlerOptionsInput,
    )

    if config_path is not None:
        if not config_path.startswith("@"):
            raise click.BadParameter("--config must be a @file.json reference")
        with Path(config_path[1:]).open() as f:
            raw = json.load(f)
        if "options" in raw:
            body = ReplaceDeploymentOptionsInput.model_validate(raw)
        else:
            body = ReplaceDeploymentOptionsInput(
                options=DeploymentOptionsInput.model_validate(raw),
            )
    else:
        entries: list[HandlerOptionsEntryInput] = []
        for spec in handlers:
            if "=" not in spec:
                raise click.BadParameter(
                    f"--handler expects 'name=seconds' or 'name=null' (got {spec!r})",
                )
            name, _, value_str = spec.partition("=")
            entries.append(
                HandlerOptionsEntryInput(
                    handler_name=name.strip(),
                    timeout_sec=_parse_timeout_value(value_str),
                )
            )
        body = ReplaceDeploymentOptionsInput(
            options=DeploymentOptionsInput(
                handler_options=DeploymentHandlerOptionsInput(
                    default=HandlerOptionsInput(timeout_sec=_parse_default(default_timeout)),
                    by_handler=entries,
                ),
            ),
        )

    from ai.backend.common.identifier.deployment import DeploymentID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.replace_options(
                DeploymentID(UUID(deployment_id)), body
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
