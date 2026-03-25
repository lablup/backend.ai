"""CLI commands for the v2 domain resource."""

from __future__ import annotations

import asyncio
import json
import sys

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
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new domain (superadmin only).

    BODY is a JSON string with domain creation fields.
    """
    from ai.backend.common.dto.manager.v2.domain.request import CreateDomainInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_create(CreateDomainInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_name")
@click.argument("body", type=str)
def update(domain_name: str, body: str) -> None:
    """Update a domain (superadmin only).

    BODY is a JSON string with fields to update.
    """
    from ai.backend.common.dto.manager.v2.domain.request import UpdateDomainInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_update(domain_name, UpdateDomainInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_name")
def delete(domain_name: str) -> None:
    """Soft-delete a domain (superadmin only)."""
    from ai.backend.common.dto.manager.v2.domain.request import DeleteDomainInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_delete(DeleteDomainInput(name=domain_name))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domain.command()
@click.argument("domain_name")
def purge(domain_name: str) -> None:
    """Permanently purge a domain (superadmin only)."""
    from ai.backend.common.dto.manager.v2.domain.request import PurgeDomainInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_purge(PurgeDomainInput(name=domain_name))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
