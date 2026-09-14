"""Admin CLI commands for the v2 domain resource."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def domain() -> None:
    """Admin domain commands."""


@domain.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter domains whose name contains this substring.",
)
@click.option(
    "--is-active/--no-is-active",
    default=None,
    help="Filter by active status.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search domains (superadmin only)."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        AdminSearchDomainsInput,
        DomainFilter,
        DomainOrder,
    )
    from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField

    # Build filter only if any filter option is provided
    filter_dto: DomainFilter | None = None
    if name_contains is not None or is_active is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = DomainFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            is_active=is_active,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, DomainOrderField, DomainOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_search(
                AdminSearchDomainsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
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
    import json
    import sys

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
@click.option("--name", default=None, help="New domain name.")
@click.option("--description", default=None, help="Updated description.")
@click.option(
    "--set-null-description",
    is_flag=True,
    default=False,
    help="Clear the description. Mutually exclusive with --description.",
)
@click.option(
    "--set-active/--unset-active",
    "is_active",
    default=None,
    help="Whether the domain is active.",
)
@click.option(
    "--allowed-docker-registry",
    "allowed_docker_registries",
    multiple=True,
    help="Allowed Docker registry URL. Repeat to set several; replaces the whole list.",
)
@click.option("--integration-name", default=None, help="Updated external integration identifier.")
@click.option(
    "--set-null-integration-name",
    is_flag=True,
    default=False,
    help="Clear the integration name. Mutually exclusive with --integration-name.",
)
def update(
    domain_name: str,
    name: str | None,
    description: str | None,
    set_null_description: bool,
    is_active: bool | None,
    allowed_docker_registries: tuple[str, ...],
    integration_name: str | None,
    set_null_integration_name: bool,
) -> None:
    """Update a domain (superadmin only). Omitted options keep their current value."""
    from ai.backend.common.dto.manager.v2.domain.request import UpdateDomainInput
    from ai.backend.common.tristate.unset import UNSET, Unset

    if description is not None and set_null_description:
        raise click.UsageError("--description and --set-null-description are mutually exclusive.")
    if integration_name is not None and set_null_integration_name:
        raise click.UsageError(
            "--integration-name and --set-null-integration-name are mutually exclusive."
        )

    # An option the user did not pass stays UNSET so the field is left unchanged.
    description_value: str | None | Unset = UNSET
    if set_null_description:
        description_value = None
    elif description is not None:
        description_value = description
    integration_name_value: str | None | Unset = UNSET
    if set_null_integration_name:
        integration_name_value = None
    elif integration_name is not None:
        integration_name_value = integration_name

    input_dto = UpdateDomainInput(
        name=name if name is not None else UNSET,
        description=description_value,
        is_active=is_active if is_active is not None else UNSET,
        allowed_docker_registries=(
            list(allowed_docker_registries) if allowed_docker_registries else UNSET
        ),
        integration_name=integration_name_value,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_update(domain_name, input_dto)
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
