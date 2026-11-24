"""CLI commands for the v2 domain resource.

User-facing commands only. Admin commands are in admin/domain.py.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def domain() -> None:
    """Domain commands."""


@domain.command()
@click.argument("domain_name")
def get(domain_name: str) -> None:
    """Get a domain by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.get(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_id", type=click.UUID)
@click.argument("container_registry_ids", type=click.UUID, nargs=-1, required=True)
def create_container_registry_relations(
    domain_id: UUID, container_registry_ids: tuple[UUID, ...]
) -> None:
    """Create relations between a domain and container registries."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        CreateDomainContainerRegistryRelationsInput,
        DomainContainerRegistryRelationInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.create_container_registry_relations(
                CreateDomainContainerRegistryRelationsInput(
                    items=[
                        DomainContainerRegistryRelationInput(
                            domain_id=domain_id, container_registry_id=registry_id
                        )
                        for registry_id in container_registry_ids
                    ]
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_id", type=click.UUID)
@click.argument("container_registry_ids", type=click.UUID, nargs=-1, required=True)
def purge_container_registry_relations(
    domain_id: UUID, container_registry_ids: tuple[UUID, ...]
) -> None:
    """Purge relations between a domain and container registries."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        DomainContainerRegistryRelationInput,
        PurgeDomainContainerRegistryRelationsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.purge_container_registry_relations(
                PurgeDomainContainerRegistryRelationsInput(
                    items=[
                        DomainContainerRegistryRelationInput(
                            domain_id=domain_id, container_registry_id=registry_id
                        )
                        for registry_id in container_registry_ids
                    ]
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
