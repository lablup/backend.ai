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
def allow_container_registries(domain_id: UUID, container_registry_ids: tuple[UUID, ...]) -> None:
    """Allow container registries for a domain."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        AllowDomainContainerRegistriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.allow_container_registries(
                AllowDomainContainerRegistriesInput(
                    domain_id=domain_id, container_registry_ids=list(container_registry_ids)
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_id", type=click.UUID)
@click.argument("container_registry_ids", type=click.UUID, nargs=-1, required=True)
def disallow_container_registries(
    domain_id: UUID, container_registry_ids: tuple[UUID, ...]
) -> None:
    """Disallow container registries for a domain."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        DisallowDomainContainerRegistriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.disallow_container_registries(
                DisallowDomainContainerRegistriesInput(
                    domain_id=domain_id, container_registry_ids=list(container_registry_ids)
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
