"""Admin CLI commands for resource group management (superadmin only)."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="resource-group")
def resource_group() -> None:
    """Admin resource group commands."""


@resource_group.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter resource groups whose name contains this substring.",
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
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search resource groups (superadmin only)."""
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        AdminSearchResourceGroupsInput,
        ResourceGroupFilter,
        ResourceGroupOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_group.types import ResourceGroupOrderField

    filter_dto: ResourceGroupFilter | None = None
    if name_contains is not None or is_active is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ResourceGroupFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            is_active=is_active,
        )

    orders = (
        parse_order_options(order_by, ResourceGroupOrderField, ResourceGroupOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.search(
                AdminSearchResourceGroupsInput(
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


@resource_group.command()
@click.argument("name", type=str)
def get(name: str) -> None:
    """Get a resource group by name (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command()
@click.option("--name", required=True, help="Resource group name.")
@click.option("--domain-name", required=True, help="Domain name.")
@click.option("--description", default=None, help="Description.")
def create(name: str, domain_name: str, description: str | None) -> None:
    """Create a new resource group (superadmin only)."""
    from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.create(
                CreateResourceGroupInput(
                    name=name,
                    domain_name=domain_name,
                    description=description,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command()
@click.argument("name", type=str)
def delete(name: str) -> None:
    """Delete a resource group by name (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.delete(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="resource-info")
@click.argument("name", type=str)
def resource_info(name: str) -> None:
    """Get resource information for a resource group (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_resource_info(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# Allow / Disallow commands


@resource_group.command(name="allowed-for-domain")
@click.argument("domain_name", type=str)
def allowed_for_domain(domain_name: str) -> None:
    """Get allowed resource groups for a domain (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_allowed_resource_groups_for_domain(
                domain_name
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allow-for-domain")
@click.argument("domain_name", type=str)
@click.option("--add", multiple=True, help="Resource group names to allow.")
@click.option("--remove", multiple=True, help="Resource group names to disallow.")
def allow_for_domain(domain_name: str, add: tuple[str, ...], remove: tuple[str, ...]) -> None:
    """Update allowed resource groups for a domain (superadmin only)."""
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        UpdateAllowedResourceGroupsForDomainInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.update_allowed_resource_groups_for_domain(
                domain_name,
                UpdateAllowedResourceGroupsForDomainInput(
                    domain_name=domain_name,
                    add=list(add) or None,
                    remove=list(remove) or None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allowed-for-project")
@click.argument("project_id", type=str)
def allowed_for_project(project_id: str) -> None:
    """Get allowed resource groups for a project (superadmin only)."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_allowed_resource_groups_for_project(
                UUID(project_id)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allow-for-project")
@click.argument("project_id", type=str)
@click.option("--add", multiple=True, help="Resource group names to allow.")
@click.option("--remove", multiple=True, help="Resource group names to disallow.")
def allow_for_project(project_id: str, add: tuple[str, ...], remove: tuple[str, ...]) -> None:
    """Update allowed resource groups for a project (superadmin only)."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.resource_group.request import (
        UpdateAllowedResourceGroupsForProjectInput,
    )

    pid = UUID(project_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.update_allowed_resource_groups_for_project(
                pid,
                UpdateAllowedResourceGroupsForProjectInput(
                    project_id=pid,
                    add=list(add) or None,
                    remove=list(remove) or None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allowed-domains")
@click.argument("resource_group_name", type=str)
def allowed_domains(resource_group_name: str) -> None:
    """Get allowed domains for a resource group (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_allowed_domains_for_resource_group(
                resource_group_name
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allow-domains")
@click.argument("resource_group_name", type=str)
@click.option("--add", multiple=True, help="Domain names to allow.")
@click.option("--remove", multiple=True, help="Domain names to disallow.")
def allow_domains(resource_group_name: str, add: tuple[str, ...], remove: tuple[str, ...]) -> None:
    """Update allowed domains for a resource group (superadmin only)."""
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        UpdateAllowedDomainsForResourceGroupInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.update_allowed_domains_for_resource_group(
                resource_group_name,
                UpdateAllowedDomainsForResourceGroupInput(
                    resource_group_name=resource_group_name,
                    add=list(add) or None,
                    remove=list(remove) or None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allowed-projects")
@click.argument("resource_group_name", type=str)
def allowed_projects(resource_group_name: str) -> None:
    """Get allowed projects for a resource group (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_allowed_projects_for_resource_group(
                resource_group_name
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="allow-projects")
@click.argument("resource_group_name", type=str)
@click.option("--add", multiple=True, help="Project UUIDs to allow.")
@click.option("--remove", multiple=True, help="Project UUIDs to disallow.")
def allow_projects(resource_group_name: str, add: tuple[str, ...], remove: tuple[str, ...]) -> None:
    """Update allowed projects for a resource group (superadmin only)."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.resource_group.request import (
        UpdateAllowedProjectsForResourceGroupInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.update_allowed_projects_for_resource_group(
                resource_group_name,
                UpdateAllowedProjectsForResourceGroupInput(
                    resource_group_name=resource_group_name,
                    add=[UUID(x) for x in add] or None,
                    remove=[UUID(x) for x in remove] or None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# default-options (DeploymentOptions) sub-group
# ---------------------------------------------------------------------------


@resource_group.group(name="default-options")
def default_options() -> None:
    """Manage ``default_deployment_options`` for a resource group (superadmin only)."""


@default_options.command(name="get")
@click.argument("name", type=str)
def default_options_get(name: str) -> None:
    """Show the current ``default_deployment_options`` surface."""
    from ai.backend.common.identifier.resource_group import ResourceGroupName

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.admin_get_default_deployment_options(
                ResourceGroupName(name)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


def _parse_timeout_value(raw: str) -> int | None:
    normalized = raw.strip()
    if normalized.lower() in ("null", "none"):
        return None
    value = int(normalized)
    if value < 1:
        raise click.BadParameter(
            f"timeout must be a positive integer or 'null' (got {raw!r})",
        )
    return value


@default_options.command(name="replace")
@click.argument("name", type=str)
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
def default_options_replace(
    name: str,
    default_timeout: str | None,
    handlers: tuple[str, ...],
    config_path: str | None,
) -> None:
    """Fully replace a resource group's ``default_deployment_options`` (superadmin only)."""
    import json
    from pathlib import Path

    from ai.backend.common.dto.manager.v2.deployment_options import (
        DeploymentHandlerOptionsInput,
        DeploymentOptionsInput,
    )
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        ReplaceResourceGroupDefaultDeploymentOptionsInput,
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
            body = ReplaceResourceGroupDefaultDeploymentOptionsInput.model_validate(raw)
        else:
            body = ReplaceResourceGroupDefaultDeploymentOptionsInput(
                options=DeploymentOptionsInput.model_validate(raw),
            )
    else:
        entries: list[HandlerOptionsEntryInput] = []
        for spec in handlers:
            if "=" not in spec:
                raise click.BadParameter(
                    f"--handler expects 'name=seconds' or 'name=null' (got {spec!r})",
                )
            handler_name, _, value_str = spec.partition("=")
            entries.append(
                HandlerOptionsEntryInput(
                    handler_name=handler_name.strip(),
                    timeout_sec=_parse_timeout_value(value_str),
                )
            )
        default_value = (
            _parse_timeout_value(default_timeout) if default_timeout is not None else None
        )
        body = ReplaceResourceGroupDefaultDeploymentOptionsInput(
            options=DeploymentOptionsInput(
                handler_options=DeploymentHandlerOptionsInput(
                    default=HandlerOptionsInput(timeout_sec=default_value),
                    by_handler=entries,
                ),
            ),
        )

    from ai.backend.common.identifier.resource_group import ResourceGroupName

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.admin_replace_default_deployment_options(
                ResourceGroupName(name), body
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# default-session-options (DefaultSessionOptions) sub-group
# ---------------------------------------------------------------------------


@resource_group.group(name="default-session-options")
def default_session_options() -> None:
    """Manage ``default_session_options`` for a resource group (superadmin only)."""


@default_session_options.command(name="get")
@click.argument("name", type=str)
def default_session_options_get(name: str) -> None:
    """Show the current ``default_session_options`` surface."""
    from ai.backend.common.identifier.resource_group import ResourceGroupName

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.admin_get_default_session_options(
                ResourceGroupName(name)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@default_session_options.command(name="replace")
@click.argument("name", type=str)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=str,
    help=(
        "Load the full request body from a JSON file when prefixed with '@' "
        "(e.g., --config @session-options.json). The JSON may be the inner "
        "``DefaultSessionOptionsInput`` payload or the full "
        "``ReplaceResourceGroupDefaultSessionOptionsInput`` envelope."
    ),
)
def default_session_options_replace(
    name: str,
    config_path: str | None,
) -> None:
    """Fully replace a resource group's ``default_session_options`` (superadmin only).

    ``DefaultSessionOptions`` is a non-trivial nested structure
    (handler_options, default kernel spec, scheduling policy, ...). The CLI therefore
    accepts the full payload as a JSON file rather than per-field
    flags; use the ``get`` command to read the current shape as a
    starting template.
    """
    import json
    from pathlib import Path

    from ai.backend.common.dto.manager.v2.resource_group.request import (
        ReplaceResourceGroupDefaultSessionOptionsInput,
    )
    from ai.backend.common.dto.manager.v2.session_options import (
        DefaultSessionOptionsInput,
    )

    if config_path is None:
        raise click.BadParameter(
            "--config @file.json is required for default-session-options replace"
        )
    if not config_path.startswith("@"):
        raise click.BadParameter("--config must be a @file.json reference")
    with Path(config_path[1:]).open() as f:
        raw = json.load(f)
    if "options" in raw:
        body = ReplaceResourceGroupDefaultSessionOptionsInput.model_validate(raw)
    else:
        body = ReplaceResourceGroupDefaultSessionOptionsInput(
            options=DefaultSessionOptionsInput.model_validate(raw),
        )

    from ai.backend.common.identifier.resource_group import ResourceGroupName

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.admin_replace_default_session_options(
                ResourceGroupName(name), body
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
