"""CLI commands for resource usage history."""

from __future__ import annotations

import json
import sys
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.resource_usage import resource_usage
from ai.backend.client.cli.types import CLIContext

# =============================================================================
# Domain Usage Bucket Commands
# =============================================================================


@resource_usage.group()
def domain() -> None:
    """Domain-level resource usage operations."""


@domain.command("list")
@pass_ctx_obj
@click.option("--resource-group", type=str, default=None, help="Filter by resource group")
@click.option("--domain-name", type=str, default=None, help="Filter by domain name")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["period_start"]),
    default="period_start",
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
    resource_group: str | None,
    domain_name: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List domain usage buckets."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        DomainUsageBucketFilter,
        DomainUsageBucketOrder,
        DomainUsageBucketOrderField,
        OrderDirection,
        SearchDomainUsageBucketsRequest,
    )
    from ai.backend.common.dto.manager.query import StringFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or domain_name:
                filter_cond = DomainUsageBucketFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = DomainUsageBucketOrder(
                field=DomainUsageBucketOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchDomainUsageBucketsRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.ResourceUsage.search_domain_usage_buckets(request)

            if as_json:
                print(
                    json.dumps(
                        [b.model_dump(mode="json") for b in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No domain usage buckets found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for b in items:
                    print(f"ID: {b.id}")
                    print(f"Resource Group: {b.resource_group}")
                    print(f"Domain: {b.domain_name}")
                    print(f"Period: {b.period_start} ~ {b.period_end}")
                    print(f"Decay Unit: {b.decay_unit_days} days")
                    print(f"Resource Usage: {b.resource_usage}")
                    print(f"Created: {b.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Project Usage Bucket Commands
# =============================================================================


@resource_usage.group()
def project() -> None:
    """Project-level resource usage operations."""


@project.command("list")
@pass_ctx_obj
@click.option("--resource-group", type=str, default=None, help="Filter by resource group")
@click.option("--project-id", type=str, default=None, help="Filter by project ID")
@click.option("--domain-name", type=str, default=None, help="Filter by domain name")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["period_start"]),
    default="period_start",
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
    resource_group: str | None,
    project_id: str | None,
    domain_name: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List project usage buckets."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        ProjectUsageBucketFilter,
        ProjectUsageBucketOrder,
        ProjectUsageBucketOrderField,
        SearchProjectUsageBucketsRequest,
    )
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or project_id or domain_name:
                filter_cond = ProjectUsageBucketFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    project_id=UUIDFilter(equals=UUID(project_id)) if project_id else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = ProjectUsageBucketOrder(
                field=ProjectUsageBucketOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchProjectUsageBucketsRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.ResourceUsage.search_project_usage_buckets(request)

            if as_json:
                print(
                    json.dumps(
                        [b.model_dump(mode="json") for b in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No project usage buckets found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for b in items:
                    print(f"ID: {b.id}")
                    print(f"Resource Group: {b.resource_group}")
                    print(f"Project ID: {b.project_id}")
                    print(f"Domain: {b.domain_name}")
                    print(f"Period: {b.period_start} ~ {b.period_end}")
                    print(f"Decay Unit: {b.decay_unit_days} days")
                    print(f"Resource Usage: {b.resource_usage}")
                    print(f"Created: {b.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# User Usage Bucket Commands
# =============================================================================


@resource_usage.group()
def user() -> None:
    """User-level resource usage operations."""


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
    type=click.Choice(["period_start"]),
    default="period_start",
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
    resource_group: str | None,
    user_uuid: str | None,
    project_id: str | None,
    domain_name: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List user usage buckets."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        SearchUserUsageBucketsRequest,
        UserUsageBucketFilter,
        UserUsageBucketOrder,
        UserUsageBucketOrderField,
    )
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if resource_group or user_uuid or project_id or domain_name:
                filter_cond = UserUsageBucketFilter(
                    resource_group=StringFilter(equals=resource_group) if resource_group else None,
                    user_uuid=UUIDFilter(equals=UUID(user_uuid)) if user_uuid else None,
                    project_id=UUIDFilter(equals=UUID(project_id)) if project_id else None,
                    domain_name=StringFilter(equals=domain_name) if domain_name else None,
                )

            order_spec = UserUsageBucketOrder(
                field=UserUsageBucketOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchUserUsageBucketsRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.ResourceUsage.search_user_usage_buckets(request)

            if as_json:
                print(
                    json.dumps(
                        [b.model_dump(mode="json") for b in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No user usage buckets found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for b in items:
                    print(f"ID: {b.id}")
                    print(f"Resource Group: {b.resource_group}")
                    print(f"User UUID: {b.user_uuid}")
                    print(f"Project ID: {b.project_id}")
                    print(f"Domain: {b.domain_name}")
                    print(f"Period: {b.period_start} ~ {b.period_end}")
                    print(f"Decay Unit: {b.decay_unit_days} days")
                    print(f"Resource Usage: {b.resource_usage}")
                    print(f"Created: {b.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
