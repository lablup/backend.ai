"""CLI commands for self-service effective permissions queries."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="effective-permissions")
def effective_permissions() -> None:
    """My effective permissions commands."""


@effective_permissions.command()
@click.option(
    "--element-type",
    type=str,
    required=True,
    help="Target element type (e.g., session, vfolder).",
)
@click.option(
    "--entity-id",
    type=str,
    multiple=True,
    required=True,
    help="Target entity ID(s). Repeat for multiple.",
)
@click.option(
    "--permission-entity-type",
    type=str,
    default=None,
    help="Optional permission entity type override.",
)
def resolve(
    element_type: str,
    entity_id: tuple[str, ...],
    permission_entity_type: str | None,
) -> None:
    """Resolve my effective permissions on target entities."""
    from ai.backend.common.dto.manager.v2.rbac.request import (
        ResolveEffectivePermissionsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.my_resolve_effective_permissions(
                ResolveEffectivePermissionsInput(
                    target_element_type=element_type,
                    target_entity_ids=list(entity_id),
                    permission_entity_type=permission_entity_type,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
