"""CLI commands for fair share scheduler."""

from __future__ import annotations

import json
import sys
from typing import Optional
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.fair_share import fair_share
from ai.backend.client.cli.types import CLIContext

# =============================================================================
# Domain Fair Share Commands
# =============================================================================


@fair_share.group()
def domain() -> None:
    """Domain-level fair share operations."""


@domain.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def domain_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    as_json: bool,
) -> None:
    """Get domain fair share data."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.get_domain_fair_share(resource_group, domain_name)
            if response.item is None:
                print("No domain fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"Domain: {fs.domain_name}")
                print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                print(
                    f"Lookback: {fs.calculation_snapshot.lookback_start} ~ "
                    f"{fs.calculation_snapshot.lookback_end}"
                )
                print(f"Created: {fs.created_at}")
                print(f"Updated: {fs.updated_at}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@domain.command("list")
@pass_ctx_obj
@click.option("--resource-group", type=str, default=None, help="Filter by resource group")
@click.option("--domain-name", type=str, default=None, help="Filter by domain name")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["fair_share_factor", "domain_name", "created_at"]),
    default="fair_share_factor",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def domain_list_cmd(
    ctx: CLIContext,
    resource_group: Optional[str],
    domain_name: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List domain fair shares."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        DomainFairShareFilter,
        DomainFairShareOrder,
        DomainFairShareOrderField,
        OrderDirection,
        SearchDomainFairSharesRequest,
    )
    from ai.backend.common.dto.manager.query import StringFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or domain_name:
                filter_cond = DomainFairShareFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = DomainFairShareOrder(
                field=DomainFairShareOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchDomainFairSharesRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.FairShare.search_domain_fair_shares(request)

            if as_json:
                print(
                    json.dumps(
                        [fs.model_dump(mode="json") for fs in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No domain fair shares found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for fs in items:
                    print(f"ID: {fs.id}")
                    print(f"Resource Group: {fs.resource_group}")
                    print(f"Domain: {fs.domain_name}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Project Fair Share Commands
# =============================================================================


@fair_share.group()
def project() -> None:
    """Project-level fair share operations."""


@project.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("project_id", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def project_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    project_id: str,
    as_json: bool,
) -> None:
    """Get project fair share data."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.get_project_fair_share(
                resource_group, UUID(project_id)
            )
            if response.item is None:
                print("No project fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                print(
                    f"Lookback: {fs.calculation_snapshot.lookback_start} ~ "
                    f"{fs.calculation_snapshot.lookback_end}"
                )
                print(f"Created: {fs.created_at}")
                print(f"Updated: {fs.updated_at}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@project.command("list")
@pass_ctx_obj
@click.option("--resource-group", type=str, default=None, help="Filter by resource group")
@click.option("--project-id", type=str, default=None, help="Filter by project ID")
@click.option("--domain-name", type=str, default=None, help="Filter by domain name")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["fair_share_factor", "created_at"]),
    default="fair_share_factor",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def project_list_cmd(
    ctx: CLIContext,
    resource_group: Optional[str],
    project_id: Optional[str],
    domain_name: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List project fair shares."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        ProjectFairShareFilter,
        ProjectFairShareOrder,
        ProjectFairShareOrderField,
        SearchProjectFairSharesRequest,
    )
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or project_id or domain_name:
                filter_cond = ProjectFairShareFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    project_id=UUIDFilter(equals=UUID(project_id)) if project_id else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = ProjectFairShareOrder(
                field=ProjectFairShareOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchProjectFairSharesRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.FairShare.search_project_fair_shares(request)

            if as_json:
                print(
                    json.dumps(
                        [fs.model_dump(mode="json") for fs in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No project fair shares found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for fs in items:
                    print(f"ID: {fs.id}")
                    print(f"Resource Group: {fs.resource_group}")
                    print(f"Project ID: {fs.project_id}")
                    print(f"Domain: {fs.domain_name}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# User Fair Share Commands
# =============================================================================


@fair_share.group()
def user() -> None:
    """User-level fair share operations."""


@user.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("project_id", type=str)
@click.argument("user_uuid", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def user_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    project_id: str,
    user_uuid: str,
    as_json: bool,
) -> None:
    """Get user fair share data."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.get_user_fair_share(
                resource_group, UUID(project_id), UUID(user_uuid)
            )
            if response.item is None:
                print("No user fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"User UUID: {fs.user_uuid}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                print(
                    f"Lookback: {fs.calculation_snapshot.lookback_start} ~ "
                    f"{fs.calculation_snapshot.lookback_end}"
                )
                print(f"Created: {fs.created_at}")
                print(f"Updated: {fs.updated_at}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@user.command("list")
@pass_ctx_obj
@click.option("--resource-group", type=str, default=None, help="Filter by resource group")
@click.option("--user-uuid", type=str, default=None, help="Filter by user UUID")
@click.option("--project-id", type=str, default=None, help="Filter by project ID")
@click.option("--domain-name", type=str, default=None, help="Filter by domain name")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["fair_share_factor", "created_at"]),
    default="fair_share_factor",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def user_list_cmd(
    ctx: CLIContext,
    resource_group: Optional[str],
    user_uuid: Optional[str],
    project_id: Optional[str],
    domain_name: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List user fair shares."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        SearchUserFairSharesRequest,
        UserFairShareFilter,
        UserFairShareOrder,
        UserFairShareOrderField,
    )
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or user_uuid or project_id or domain_name:
                filter_cond = UserFairShareFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    user_uuid=UUIDFilter(equals=UUID(user_uuid)) if user_uuid else None,
                    project_id=UUIDFilter(equals=UUID(project_id)) if project_id else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = UserFairShareOrder(
                field=UserFairShareOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchUserFairSharesRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.FairShare.search_user_fair_shares(request)

            if as_json:
                print(
                    json.dumps(
                        [fs.model_dump(mode="json") for fs in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No user fair shares found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for fs in items:
                    print(f"ID: {fs.id}")
                    print(f"Resource Group: {fs.resource_group}")
                    print(f"User UUID: {fs.user_uuid}")
                    print(f"Project ID: {fs.project_id}")
                    print(f"Domain: {fs.domain_name}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
