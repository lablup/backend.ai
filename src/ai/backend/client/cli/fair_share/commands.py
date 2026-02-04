"""CLI commands for fair share scheduler."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
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
                print(f"Resource Group: {fs.resource_group}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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
    resource_group: str | None,
    domain_name: str | None,
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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@domain.command("set-weight")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.option(
    "--weight",
    type=str,
    default=None,
    help="Weight value (omit to use resource group's default_weight)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def domain_set_weight_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    weight: str | None,
    as_json: bool,
) -> None:
    """Set domain fair share weight."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            weight_decimal = Decimal(weight) if weight is not None else None
            response = api_session.FairShare.upsert_domain_fair_share_weight(
                resource_group, domain_name, weight_decimal
            )

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print("Updated domain fair share weight successfully.")
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
                print(f"Updated: {fs.updated_at}")
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
                print(f"Resource Group: {fs.resource_group}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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
    resource_group: str | None,
    project_id: str | None,
    domain_name: str | None,
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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@project.command("set-weight")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("project_id", type=str)
@click.option(
    "--domain",
    "domain_name",
    type=str,
    required=True,
    help="Domain name the project belongs to",
)
@click.option(
    "--weight",
    type=str,
    default=None,
    help="Weight value (omit to use resource group's default_weight)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def project_set_weight_cmd(
    ctx: CLIContext,
    resource_group: str,
    project_id: str,
    domain_name: str,
    weight: str | None,
    as_json: bool,
) -> None:
    """Set project fair share weight."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            weight_decimal = Decimal(weight) if weight is not None else None
            response = api_session.FairShare.upsert_project_fair_share_weight(
                resource_group, UUID(project_id), domain_name, weight_decimal
            )

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print("Updated project fair share weight successfully.")
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
                print(f"Updated: {fs.updated_at}")
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
                print(f"Resource Group: {fs.resource_group}")
                print(f"User UUID: {fs.user_uuid}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@user.command("set-weight")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("project_id", type=str)
@click.argument("user_uuid", type=str)
@click.option(
    "--domain",
    "domain_name",
    type=str,
    required=True,
    help="Domain name the user belongs to",
)
@click.option(
    "--weight",
    type=str,
    default=None,
    help="Weight value (omit to use resource group's default_weight)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def user_set_weight_cmd(
    ctx: CLIContext,
    resource_group: str,
    project_id: str,
    user_uuid: str,
    domain_name: str,
    weight: str | None,
    as_json: bool,
) -> None:
    """Set user fair share weight."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            weight_decimal = Decimal(weight) if weight is not None else None
            response = api_session.FairShare.upsert_user_fair_share_weight(
                resource_group, UUID(project_id), UUID(user_uuid), domain_name, weight_decimal
            )

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print("Updated user fair share weight successfully.")
                print(f"ID: {fs.id}")
                print(f"Resource Group: {fs.resource_group}")
                print(f"User UUID: {fs.user_uuid}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
                print(f"Updated: {fs.updated_at}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Resource Group Fair Share Commands
# =============================================================================


@fair_share.group()
def resource_group() -> None:
    """Resource group fair share operations."""


@resource_group.command("update-spec")
@pass_ctx_obj
@click.argument("name", type=str)
@click.option(
    "--half-life-days",
    type=int,
    default=None,
    help="Half-life for exponential decay in days",
)
@click.option(
    "--lookback-days",
    type=int,
    default=None,
    help="Total lookback period in days",
)
@click.option(
    "--decay-unit-days",
    type=int,
    default=None,
    help="Granularity of decay buckets in days",
)
@click.option(
    "--default-weight",
    type=str,
    default=None,
    help="Default weight for entities",
)
@click.option(
    "--resource-weight",
    "resource_weights",
    type=str,
    multiple=True,
    help="Resource weight in KEY=VALUE format (e.g., cpu=1.0, mem=0.5). Use VALUE=null to remove.",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def resource_group_update_spec_cmd(
    ctx: CLIContext,
    name: str,
    half_life_days: int | None,
    lookback_days: int | None,
    decay_unit_days: int | None,
    default_weight: str | None,
    resource_weights: tuple[str, ...],
    as_json: bool,
) -> None:
    """Update resource group fair share specification."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import ResourceWeightEntryInput

    # Parse resource_weights from "cpu=1.0,mem=null" format
    parsed_weights: list[ResourceWeightEntryInput] | None = None
    if resource_weights:
        parsed_weights = []
        for entry in resource_weights:
            if "=" not in entry:
                ctx.output.print_error(
                    ValueError(
                        f"Invalid resource weight format: {entry}. Expected KEY=VALUE format."
                    )
                )
                sys.exit(ExitCode.FAILURE)
            key, _, value = entry.partition("=")
            weight: Decimal | None = None if value.lower() == "null" else Decimal(value)
            parsed_weights.append(ResourceWeightEntryInput(resource_type=key, weight=weight))

    default_weight_decimal = Decimal(default_weight) if default_weight is not None else None

    with Session() as api_session:
        try:
            response = api_session.FairShare.update_resource_group_fair_share_spec(
                name,
                half_life_days,
                lookback_days,
                decay_unit_days,
                default_weight_decimal,
                parsed_weights,
            )

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                spec = response.item
                print("Updated resource group fair share spec successfully.")
                print(f"Resource Group: {name}")
                print(f"Half Life Days: {spec.half_life_days}")
                print(f"Lookback Days: {spec.lookback_days}")
                print(f"Decay Unit Days: {spec.decay_unit_days}")
                print(f"Default Weight: {spec.default_weight}")
                print("Resource Weights:")
                for entry in spec.resource_weights.entries:
                    print(f"  {entry.resource_type}: {entry.quantity}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@resource_group.command("spec")
@pass_ctx_obj
@click.argument("name", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def resource_group_spec_cmd(
    ctx: CLIContext,
    name: str,
    as_json: bool,
) -> None:
    """Get resource group fair share specification."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.get_resource_group_fair_share_spec(name)

            if as_json:
                print(json.dumps(response.model_dump(mode="json"), indent=2, default=str))
            else:
                print(f"Resource Group: {response.resource_group}")
                spec = response.fair_share_spec
                print(f"Half Life Days: {spec.half_life_days}")
                print(f"Lookback Days: {spec.lookback_days}")
                print(f"Decay Unit Days: {spec.decay_unit_days}")
                print(f"Default Weight: {spec.default_weight}")
                print("Resource Weights:")
                for entry in spec.resource_weights.entries:
                    print(f"  {entry.resource_type}: {entry.quantity}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@resource_group.command("specs")
@pass_ctx_obj
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def resource_group_specs_cmd(
    ctx: CLIContext,
    as_json: bool,
) -> None:
    """List all resource groups with their fair share specifications."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.list_resource_group_fair_share_specs()

            if as_json:
                print(
                    json.dumps(
                        [item.model_dump(mode="json") for item in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                items = response.items
                if not items:
                    print("No resource groups found")
                    return
                print(f"Total: {response.total_count}")
                print()
                for item in items:
                    print(f"Resource Group: {item.resource_group}")
                    spec = item.fair_share_spec
                    print(f"  Half Life Days: {spec.half_life_days}")
                    print(f"  Lookback Days: {spec.lookback_days}")
                    print(f"  Decay Unit Days: {spec.decay_unit_days}")
                    print(f"  Default Weight: {spec.default_weight}")
                    print("  Resource Weights:")
                    for entry in spec.resource_weights.entries:
                        print(f"    {entry.resource_type}: {entry.quantity}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# RG-Scoped Domain Fair Share Commands (Resource Group Scope)
# =============================================================================


@fair_share.group("rg-domain")
def rg_domain() -> None:
    """Domain fair share operations within resource group scope."""


@rg_domain.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def rg_domain_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    as_json: bool,
) -> None:
    """Get domain fair share data within resource group scope."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.rg_get_domain_fair_share(resource_group, domain_name)
            if response.item is None:
                print("No domain fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"Resource Group: {fs.resource_group}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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


@rg_domain.command("list")
@pass_ctx_obj
@click.argument("resource_group", type=str)
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
def rg_domain_list_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List domain fair shares within resource group scope."""
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
            if domain_name:
                filter_cond = DomainFairShareFilter(
                    domain_name=StringFilter(equals=domain_name),
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
            response = api_session.FairShare.rg_search_domain_fair_shares(resource_group, request)

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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# RG-Scoped Project Fair Share Commands (Resource Group Scope)
# =============================================================================


@fair_share.group("rg-project")
def rg_project() -> None:
    """Project fair share operations within resource group scope."""


@rg_project.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.argument("project_id", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def rg_project_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    project_id: str,
    as_json: bool,
) -> None:
    """Get project fair share data within resource group scope."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.rg_get_project_fair_share(
                resource_group, domain_name, UUID(project_id)
            )
            if response.item is None:
                print("No project fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"Resource Group: {fs.resource_group}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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


@rg_project.command("list")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.option("--project-id", type=str, default=None, help="Filter by project ID")
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
def rg_project_list_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    project_id: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List project fair shares within resource group scope."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        ProjectFairShareFilter,
        ProjectFairShareOrder,
        ProjectFairShareOrderField,
        SearchProjectFairSharesRequest,
    )
    from ai.backend.common.dto.manager.query import UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if project_id:
                filter_cond = ProjectFairShareFilter(
                    project_id=UUIDFilter(equals=UUID(project_id)),
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
            response = api_session.FairShare.rg_search_project_fair_shares(
                resource_group, domain_name, request
            )

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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# RG-Scoped User Fair Share Commands (Resource Group Scope)
# =============================================================================


@fair_share.group("rg-user")
def rg_user() -> None:
    """User fair share operations within resource group scope."""


@rg_user.command("get")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.argument("project_id", type=str)
@click.argument("user_uuid", type=str)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def rg_user_get_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    project_id: str,
    user_uuid: str,
    as_json: bool,
) -> None:
    """Get user fair share data within resource group scope."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as api_session:
        try:
            response = api_session.FairShare.rg_get_user_fair_share(
                resource_group, domain_name, UUID(project_id), UUID(user_uuid)
            )
            if response.item is None:
                print("No user fair share found")
                return

            if as_json:
                print(json.dumps(response.item.model_dump(mode="json"), indent=2, default=str))
            else:
                fs = response.item
                print(f"Resource Group: {fs.resource_group}")
                print(f"User UUID: {fs.user_uuid}")
                print(f"Project ID: {fs.project_id}")
                print(f"Domain: {fs.domain_name}")
                print(f"Weight: {fs.spec.weight}")
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


@rg_user.command("list")
@pass_ctx_obj
@click.argument("resource_group", type=str)
@click.argument("domain_name", type=str)
@click.argument("project_id", type=str)
@click.option("--user-uuid", type=str, default=None, help="Filter by user UUID")
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
def rg_user_list_cmd(
    ctx: CLIContext,
    resource_group: str,
    domain_name: str,
    project_id: str,
    user_uuid: str | None,
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """List user fair shares within resource group scope."""
    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.fair_share import (
        OrderDirection,
        SearchUserFairSharesRequest,
        UserFairShareFilter,
        UserFairShareOrder,
        UserFairShareOrderField,
    )
    from ai.backend.common.dto.manager.query import UUIDFilter

    with Session() as api_session:
        try:
            filter_cond = None
            if user_uuid:
                filter_cond = UserFairShareFilter(
                    user_uuid=UUIDFilter(equals=UUID(user_uuid)),
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
            response = api_session.FairShare.rg_search_user_fair_shares(
                resource_group, domain_name, UUID(project_id), request
            )

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
                    print(f"Weight: {fs.spec.weight}")
                    print(f"Fair Share Factor: {fs.calculation_snapshot.fair_share_factor}")
                    print(f"Normalized Usage: {fs.calculation_snapshot.normalized_usage}")
                    print(f"Created: {fs.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
