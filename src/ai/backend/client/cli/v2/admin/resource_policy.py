"""Admin CLI commands for the v2 resource policy resource."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


def _load_input(
    json_str: str | None,
    file_path: str | None,
    **kwargs: object,
) -> dict[str, Any]:
    """Resolve input from --json, --file, or click options (mutually exclusive)."""
    sources = sum([json_str is not None, file_path is not None])
    if sources > 1:
        click.echo("Error: --json and --file are mutually exclusive.", err=True)
        sys.exit(1)
    if json_str is not None:
        try:
            result: dict[str, Any] = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            click.echo(f"Invalid JSON: {e}", err=True)
            sys.exit(1)
    if file_path is not None:
        try:
            with Path(file_path).open() as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError) as e:
            click.echo(f"Error reading file: {e}", err=True)
            sys.exit(1)
    return {k: v for k, v in kwargs.items() if v is not None}


def _build_dto(dto_cls: type, data: dict[str, Any]) -> Any:
    """Build a Pydantic DTO from a dict, catching validation errors."""
    from pydantic import ValidationError

    try:
        return dto_cls(**data)
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            click.echo(f"  {field}: {err['msg']}", err=True)
        sys.exit(1)


def _run_async(coro_fn: Any) -> None:
    """Run an async function with SDK error handling."""
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group()
def resource_policy() -> None:
    """Admin resource policy commands."""


# ── Keypair Resource Policy ──


@resource_policy.group()
def keypair() -> None:
    """Keypair resource policy commands."""


@keypair.command(name="search")
@click.option("--limit", default=20, help="Maximum number of results.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option("--name-contains", default=None, help="Filter by name containing this string.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., name:asc).")
@click.option("--json", "json_str", default=None, help="Full search input as JSON string.")
def keypair_search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search keypair resource policies."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        AdminSearchKeypairResourcePoliciesInput,
        KeypairResourcePolicyFilter,
        KeypairResourcePolicyOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_policy.types import (
        KeypairResourcePolicyOrderField,
    )

    if json_str is not None:
        search_input = _build_dto(AdminSearchKeypairResourcePoliciesInput, json.loads(json_str))
    else:
        filter_dto = None
        if name_contains is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = KeypairResourcePolicyFilter(name=StringFilter(contains=name_contains))

        orders = (
            parse_order_options(
                order_by, KeypairResourcePolicyOrderField, KeypairResourcePolicyOrder
            )
            if order_by
            else None
        )
        search_input = AdminSearchKeypairResourcePoliciesInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_search_keypair_resource_policies(
                search_input
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@keypair.command(name="get")
@click.argument("name")
def keypair_get(name: str) -> None:
    """Get a keypair resource policy by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_get_keypair_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@keypair.command(name="create")
@click.option("--name", required=False, help="Policy name.")
@click.option(
    "--default-for-unspecified",
    type=click.Choice(["LIMITED", "UNLIMITED"]),
    help="Default for unspecified slots.",
)
@click.option("--max-concurrent-sessions", type=int, help="Maximum concurrent sessions.")
@click.option("--max-containers-per-session", type=int, help="Maximum containers per session.")
@click.option("--idle-timeout", type=int, help="Idle timeout in seconds.")
@click.option(
    "--max-session-lifetime", type=int, default=0, help="Maximum session lifetime in seconds."
)
@click.option(
    "--max-concurrent-sftp-sessions", type=int, default=1, help="Maximum concurrent SFTP sessions."
)
@click.option(
    "--max-pending-session-count", type=int, default=None, help="Maximum pending sessions."
)
@click.option(
    "--total-resource-slots",
    type=str,
    default=None,
    help='Resource slots as JSON array: \'[{"resource_type":"cpu","quantity":"4"}]\'',
)
@click.option(
    "--allowed-vfolder-hosts",
    type=str,
    default=None,
    help='VFolder hosts as JSON array: \'[{"host":"default","permissions":["mount-in-session"]}]\'',
)
@click.option("--json", "json_str", default=None, help="Full input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read input from a JSON file.",
)
def keypair_create(
    name: str | None,
    default_for_unspecified: str | None,
    max_concurrent_sessions: int | None,
    max_containers_per_session: int | None,
    idle_timeout: int | None,
    max_session_lifetime: int | None,
    max_concurrent_sftp_sessions: int | None,
    max_pending_session_count: int | None,
    total_resource_slots: str | None,
    allowed_vfolder_hosts: str | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Create a keypair resource policy.

    \b
    Examples:
      # Using options:
      ./bai admin resource-policy keypair create \\
        --name my-policy --default-for-unspecified LIMITED \\
        --max-concurrent-sessions 10 --max-containers-per-session 1 \\
        --idle-timeout 3600

      # Using --json:
      ./bai admin resource-policy keypair create \\
        --json '{"name":"my-policy","default_for_unspecified":"LIMITED",...}'

      # Using --file:
      ./bai admin resource-policy keypair create --file policy.json
    """
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        CreateKeypairResourcePolicyInput,
    )

    opts: dict[str, Any] = {}
    if name is not None:
        opts["name"] = name
    if default_for_unspecified is not None:
        opts["default_for_unspecified"] = default_for_unspecified
    if max_concurrent_sessions is not None:
        opts["max_concurrent_sessions"] = max_concurrent_sessions
    if max_containers_per_session is not None:
        opts["max_containers_per_session"] = max_containers_per_session
    if idle_timeout is not None:
        opts["idle_timeout"] = idle_timeout
    if max_session_lifetime is not None:
        opts["max_session_lifetime"] = max_session_lifetime
    if max_concurrent_sftp_sessions is not None:
        opts["max_concurrent_sftp_sessions"] = max_concurrent_sftp_sessions
    if max_pending_session_count is not None:
        opts["max_pending_session_count"] = max_pending_session_count
    if total_resource_slots is not None:
        opts["total_resource_slots"] = json.loads(total_resource_slots)
    if allowed_vfolder_hosts is not None:
        opts["allowed_vfolder_hosts"] = json.loads(allowed_vfolder_hosts)

    data = _load_input(json_str, file_path, **opts)
    dto = _build_dto(CreateKeypairResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_create_keypair_resource_policy(dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@keypair.command(name="update")
@click.argument("name")
@click.option(
    "--max-concurrent-sessions", type=int, default=None, help="Updated max concurrent sessions."
)
@click.option(
    "--max-containers-per-session",
    type=int,
    default=None,
    help="Updated max containers per session.",
)
@click.option("--idle-timeout", type=int, default=None, help="Updated idle timeout.")
@click.option(
    "--max-session-lifetime", type=int, default=None, help="Updated max session lifetime."
)
@click.option(
    "--max-concurrent-sftp-sessions", type=int, default=None, help="Updated max SFTP sessions."
)
@click.option(
    "--max-pending-session-count", type=int, default=None, help="Updated max pending sessions."
)
@click.option("--json", "json_str", default=None, help="Full update input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read update input from a JSON file.",
)
def keypair_update(
    name: str,
    max_concurrent_sessions: int | None,
    max_containers_per_session: int | None,
    idle_timeout: int | None,
    max_session_lifetime: int | None,
    max_concurrent_sftp_sessions: int | None,
    max_pending_session_count: int | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Update a keypair resource policy."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        UpdateKeypairResourcePolicyInput,
    )

    data = _load_input(
        json_str,
        file_path,
        max_concurrent_sessions=max_concurrent_sessions,
        max_containers_per_session=max_containers_per_session,
        idle_timeout=idle_timeout,
        max_session_lifetime=max_session_lifetime,
        max_concurrent_sftp_sessions=max_concurrent_sftp_sessions,
        max_pending_session_count=max_pending_session_count,
    )

    dto = _build_dto(UpdateKeypairResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_update_keypair_resource_policy(name, dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@keypair.command(name="delete")
@click.argument("name")
def keypair_delete(name: str) -> None:
    """Delete a keypair resource policy."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_delete_keypair_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


# ── User Resource Policy ──


@resource_policy.group(name="user")
def user_rp() -> None:
    """User resource policy commands."""


@user_rp.command(name="search")
@click.option("--limit", default=20, help="Maximum number of results.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option("--name-contains", default=None, help="Filter by name containing this string.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., name:asc).")
@click.option("--json", "json_str", default=None, help="Full search input as JSON string.")
def user_search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search user resource policies."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        AdminSearchUserResourcePoliciesInput,
        UserResourcePolicyFilter,
        UserResourcePolicyOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_policy.types import UserResourcePolicyOrderField

    if json_str is not None:
        search_input = _build_dto(AdminSearchUserResourcePoliciesInput, json.loads(json_str))
    else:
        filter_dto = None
        if name_contains is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = UserResourcePolicyFilter(name=StringFilter(contains=name_contains))

        orders = (
            parse_order_options(order_by, UserResourcePolicyOrderField, UserResourcePolicyOrder)
            if order_by
            else None
        )
        search_input = AdminSearchUserResourcePoliciesInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_search_user_resource_policies(
                search_input
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@user_rp.command(name="get")
@click.argument("name")
def user_get(name: str) -> None:
    """Get a user resource policy by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_get_user_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@user_rp.command(name="create")
@click.option("--name", required=False, help="Policy name.")
@click.option("--max-vfolder-count", type=int, help="Maximum vfolders.")
@click.option("--max-quota-scope-size", type=int, help="Maximum quota scope size in bytes.")
@click.option(
    "--max-session-count-per-model-session", type=int, help="Maximum sessions per model session."
)
@click.option("--max-customized-image-count", type=int, help="Maximum customized images.")
@click.option("--json", "json_str", default=None, help="Full input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read input from a JSON file.",
)
def user_create(
    name: str | None,
    max_vfolder_count: int | None,
    max_quota_scope_size: int | None,
    max_session_count_per_model_session: int | None,
    max_customized_image_count: int | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Create a user resource policy.

    \b
    Examples:
      ./bai admin resource-policy user create \\
        --name my-policy --max-vfolder-count 10 \\
        --max-quota-scope-size 0 --max-session-count-per-model-session 3 \\
        --max-customized-image-count 5
    """
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        CreateUserResourcePolicyInput,
    )

    data = _load_input(
        json_str,
        file_path,
        name=name,
        max_vfolder_count=max_vfolder_count,
        max_quota_scope_size=max_quota_scope_size,
        max_session_count_per_model_session=max_session_count_per_model_session,
        max_customized_image_count=max_customized_image_count,
    )
    dto = _build_dto(CreateUserResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_create_user_resource_policy(dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@user_rp.command(name="update")
@click.argument("name")
@click.option("--max-vfolder-count", type=int, default=None, help="Updated max vfolder count.")
@click.option(
    "--max-quota-scope-size", type=int, default=None, help="Updated max quota scope size."
)
@click.option(
    "--max-session-count-per-model-session",
    type=int,
    default=None,
    help="Updated max sessions per model session.",
)
@click.option(
    "--max-customized-image-count", type=int, default=None, help="Updated max customized images."
)
@click.option("--json", "json_str", default=None, help="Full update input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read update input from a JSON file.",
)
def user_update(
    name: str,
    max_vfolder_count: int | None,
    max_quota_scope_size: int | None,
    max_session_count_per_model_session: int | None,
    max_customized_image_count: int | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Update a user resource policy."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        UpdateUserResourcePolicyInput,
    )

    data = _load_input(
        json_str,
        file_path,
        max_vfolder_count=max_vfolder_count,
        max_quota_scope_size=max_quota_scope_size,
        max_session_count_per_model_session=max_session_count_per_model_session,
        max_customized_image_count=max_customized_image_count,
    )

    dto = _build_dto(UpdateUserResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_update_user_resource_policy(name, dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@user_rp.command(name="delete")
@click.argument("name")
def user_delete(name: str) -> None:
    """Delete a user resource policy."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_delete_user_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


# ── Project Resource Policy ──


@resource_policy.group()
def project() -> None:
    """Project resource policy commands."""


@project.command(name="search")
@click.option("--limit", default=20, help="Maximum number of results.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option("--name-contains", default=None, help="Filter by name containing this string.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., name:asc).")
@click.option("--json", "json_str", default=None, help="Full search input as JSON string.")
def project_search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search project resource policies."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        AdminSearchProjectResourcePoliciesInput,
        ProjectResourcePolicyFilter,
        ProjectResourcePolicyOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_policy.types import (
        ProjectResourcePolicyOrderField,
    )

    if json_str is not None:
        search_input = _build_dto(AdminSearchProjectResourcePoliciesInput, json.loads(json_str))
    else:
        filter_dto = None
        if name_contains is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = ProjectResourcePolicyFilter(name=StringFilter(contains=name_contains))

        orders = (
            parse_order_options(
                order_by, ProjectResourcePolicyOrderField, ProjectResourcePolicyOrder
            )
            if order_by
            else None
        )
        search_input = AdminSearchProjectResourcePoliciesInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_search_project_resource_policies(
                search_input
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@project.command(name="get")
@click.argument("name")
def project_get(name: str) -> None:
    """Get a project resource policy by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_get_project_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@project.command(name="create")
@click.option("--name", required=False, help="Policy name.")
@click.option("--max-vfolder-count", type=int, help="Maximum vfolders.")
@click.option("--max-quota-scope-size", type=int, help="Maximum quota scope size in bytes.")
@click.option("--max-network-count", type=int, help="Maximum networks. -1 for unlimited.")
@click.option("--json", "json_str", default=None, help="Full input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read input from a JSON file.",
)
def project_create(
    name: str | None,
    max_vfolder_count: int | None,
    max_quota_scope_size: int | None,
    max_network_count: int | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Create a project resource policy.

    \b
    Examples:
      ./bai admin resource-policy project create \\
        --name my-policy --max-vfolder-count 10 \\
        --max-quota-scope-size 0 --max-network-count 5
    """
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        CreateProjectResourcePolicyInput,
    )

    data = _load_input(
        json_str,
        file_path,
        name=name,
        max_vfolder_count=max_vfolder_count,
        max_quota_scope_size=max_quota_scope_size,
        max_network_count=max_network_count,
    )

    dto = _build_dto(CreateProjectResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_create_project_resource_policy(dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@project.command(name="update")
@click.argument("name")
@click.option("--max-vfolder-count", type=int, default=None, help="Updated max vfolder count.")
@click.option(
    "--max-quota-scope-size", type=int, default=None, help="Updated max quota scope size."
)
@click.option("--max-network-count", type=int, default=None, help="Updated max network count.")
@click.option("--json", "json_str", default=None, help="Full update input as JSON string.")
@click.option(
    "--file",
    "file_path",
    default=None,
    type=click.Path(exists=True),
    help="Read update input from a JSON file.",
)
def project_update(
    name: str,
    max_vfolder_count: int | None,
    max_quota_scope_size: int | None,
    max_network_count: int | None,
    json_str: str | None,
    file_path: str | None,
) -> None:
    """Update a project resource policy."""
    from ai.backend.common.dto.manager.v2.resource_policy.request import (
        UpdateProjectResourcePolicyInput,
    )

    data = _load_input(
        json_str,
        file_path,
        max_vfolder_count=max_vfolder_count,
        max_quota_scope_size=max_quota_scope_size,
        max_network_count=max_network_count,
    )

    dto = _build_dto(UpdateProjectResourcePolicyInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_update_project_resource_policy(name, dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@project.command(name="delete")
@click.argument("name")
def project_delete(name: str) -> None:
    """Delete a project resource policy."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.admin_delete_project_resource_policy(name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
