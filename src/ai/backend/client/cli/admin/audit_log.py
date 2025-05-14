from __future__ import annotations

import asyncio
from typing import Literal

import click

from ai.backend.client.session import AsyncSession

from ..types import CLIContext
from . import admin


@admin.group()
def audit_log():
    """
    AuditLog administration commands.
    """
    pass


@audit_log.command()
@click.pass_obj
@click.argument("schema_type", type=click.Choice(["entity_type", "action_type"]))
@click.option(
    "--entity-type",
    "-e",
    metavar="ENTITY",
    help="Entity type to filter action types when schema_type is action_type.",
)
def dump_schema(
    cli_ctx: CLIContext, schema_type: Literal["entity_type", "action_type"], entity_type: str | None
) -> None:
    """
    Dump audit_log schema for the specified type.

    Examples:
        # List entity types
        backend ai audit-log dump-schema entity_type
        # List all action types
        backend ai audit-log dump-schema action_type
        # List action types for a specific entity
        backend ai audit-log dump-schema action_type --entity-type session
    """
    if entity_type and schema_type != "action_type":
        raise click.UsageError(
            "--entity-type option can be used only when schema_type is action_type."
        )

    async def _dump() -> None:
        async with AsyncSession() as session:
            resp = await session.AuditLog.fetch_schema()
            match schema_type:
                case "entity_type":
                    print("\n".join(resp.entity_type_variants))
                case "action_type":
                    result = []
                    for variant in resp.action_types:
                        if entity_type and variant.entity_type != entity_type:
                            continue
                        for action_type in variant.action_types:
                            result.append(f"{variant.entity_type}:{action_type}")
                    print("\n".join(result))

    asyncio.run(_dump())
