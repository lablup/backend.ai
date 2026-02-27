"""CLI commands for deployment system."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.deployment import (
    BlueGreenConfigInput,
    CreateDeploymentPolicyRequest,
    RollingUpdateConfigInput,
    UpdateDeploymentPolicyRequest,
)

from .extensions import pass_ctx_obj
from .pretty import print_done
from .types import CLIContext

if TYPE_CHECKING:
    pass


@click.group()
def deployment() -> None:
    """Set of deployment operations (deployments, revisions, routes, policies)"""


# Deployment commands


@deployment.command("create")
@pass_ctx_obj
@click.option(
    "-f",
    "--file",
    "config_file",
    type=click.Path(exists=True),
    required=True,
    help="Path to JSON configuration file for deployment",
)
def create_deployment_cmd(
    ctx: CLIContext,
    config_file: str,
) -> None:
    """Create a new deployment from a JSON configuration file.

    The configuration file should contain the following structure:
    {
        "metadata": {
            "project_id": "uuid",
            "domain_name": "string",
            "name": "optional string",
            "tags": ["optional", "list"]
        },
        "network_access": {
            "open_to_public": false,
            "preferred_domain_name": "optional string"
        },
        "default_deployment_strategy": {
            "type": "ROLLING",
            "rollback_on_failure": false
        },
        "desired_replica_count": 1,
        "initial_revision": {
            "name": "optional string",
            "cluster_config": {"mode": "single-node", "size": 1},
            "resource_config": {"resource_group": "string", "resource_slots": {}},
            "image": {"name": "string", "architecture": "x86_64"},
            "model_runtime_config": {"runtime_variant": "CUSTOM"},
            "model_mount_config": {"vfolder_id": "uuid", "definition_path": "string"}
        }
    }
    """
    import json

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.deployment import CreateDeploymentRequest

    from .pretty import print_done

    with Session() as session:
        try:
            config_file_path = Path(config_file)
            with config_file_path.open(encoding="utf-8") as f:
                config_data = json.load(f)

            request = CreateDeploymentRequest.model_validate(config_data)
            result = session.Deployment.create(request)
            print_done(f"Deployment created: {result.deployment.id}")
            print(json.dumps(result.deployment.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@deployment.command("list")
@pass_ctx_obj
@click.option("--project-id", type=str, default=None, help="Filter by project ID")
@click.option("--limit", type=int, default=50, help="Maximum items to return")
@click.option("--offset", type=int, default=0, help="Number of items to skip")
def list_deployments_cmd(
    ctx: CLIContext,
    project_id: str | None,
    limit: int,
    offset: int,
) -> None:
    """List all deployments."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.deployment import (
        DeploymentFilter,
        SearchDeploymentsRequest,
    )

    with Session() as session:
        try:
            filter_cond = None
            if project_id:
                filter_cond = DeploymentFilter(project_id=UUID(project_id))

            request = SearchDeploymentsRequest(filter=filter_cond, limit=limit, offset=offset)
            result = session.Deployment.search(request)

            deployments = result.deployments
            if not deployments:
                print("No deployments found")
                return

            for dep in deployments:
                print(f"ID: {dep.id}")
                print(f"Name: {dep.name}")
                print(f"Status: {dep.status}")
                print(f"Project: {dep.project_id}")
                print(f"Replicas: {dep.replica_state.desired_replica_count}")
                print(f"Created: {dep.created_at}")
                print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@deployment.command("info")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
def info_deployment_cmd(ctx: CLIContext, deployment_id: str) -> None:
    """Display detailed information of a deployment."""
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as session:
        try:
            result = session.Deployment.get(UUID(deployment_id))
            deployment = result.deployment
            print(json.dumps(deployment.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@deployment.command("update")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.option("--name", type=str, default=None, help="Update deployment name")
@click.option("--replicas", type=int, default=None, help="Update desired replica count")
def update_deployment_cmd(
    ctx: CLIContext,
    deployment_id: str,
    name: str | None,
    replicas: int | None,
) -> None:
    """Update a deployment."""
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.deployment import UpdateDeploymentRequest

    from .pretty import print_done

    with Session() as session:
        try:
            request = UpdateDeploymentRequest(name=name, desired_replicas=replicas)
            result = session.Deployment.update(UUID(deployment_id), request)
            print_done(f"Deployment updated: {deployment_id}")
            print(json.dumps(result.deployment.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@deployment.command("destroy")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.confirmation_option(prompt="Are you sure you want to destroy this deployment?")
def destroy_deployment_cmd(ctx: CLIContext, deployment_id: str) -> None:
    """Destroy a deployment."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    from .pretty import print_done, print_fail

    with Session() as session:
        try:
            result = session.Deployment.destroy(UUID(deployment_id))
            if result.deleted:
                print_done(f"Deployment destroyed: {deployment_id}")
            else:
                print_fail(f"Failed to destroy deployment: {deployment_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Revision commands


@deployment.group()
def revision() -> None:
    """Manage deployment revisions"""


@revision.command("list")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.option("--limit", type=int, default=50, help="Maximum items to return")
@click.option("--offset", type=int, default=0, help="Number of items to skip")
def list_revisions_cmd(
    ctx: CLIContext,
    deployment_id: str,
    limit: int,
    offset: int,
) -> None:
    """List revisions for a deployment."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.deployment import SearchRevisionsRequest

    with Session() as session:
        try:
            request = SearchRevisionsRequest(limit=limit, offset=offset)
            result = session.Deployment.search_revisions(UUID(deployment_id), request)

            revisions = result.revisions
            if not revisions:
                print("No revisions found")
                return

            for rev in revisions:
                print(f"ID: {rev.id}")
                print(f"Name: {rev.name}")
                print(f"Image: {rev.image_id}")
                print(f"Created: {rev.created_at}")
                print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@revision.command("info")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.argument("revision_id", type=str)
def info_revision_cmd(ctx: CLIContext, deployment_id: str, revision_id: str) -> None:
    """Display detailed information of a revision."""
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    with Session() as session:
        try:
            result = session.Deployment.get_revision(UUID(deployment_id), UUID(revision_id))
            print(json.dumps(result.revision.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@revision.command("activate")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.argument("revision_id", type=str)
def activate_revision_cmd(ctx: CLIContext, deployment_id: str, revision_id: str) -> None:
    """Activate a revision."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    from .pretty import print_done, print_fail

    with Session() as session:
        try:
            result = session.Deployment.activate_revision(UUID(deployment_id), UUID(revision_id))
            if result.success:
                print_done(f"Revision activated: {revision_id}")
            else:
                print_fail(f"Failed to activate revision: {revision_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@revision.command("deactivate")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.argument("revision_id", type=str)
def deactivate_revision_cmd(ctx: CLIContext, deployment_id: str, revision_id: str) -> None:
    """Deactivate a revision."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session

    from .pretty import print_done, print_fail

    with Session() as session:
        try:
            result = session.Deployment.deactivate_revision(UUID(deployment_id), UUID(revision_id))
            if result.success:
                print_done(f"Revision deactivated: {revision_id}")
            else:
                print_fail(f"Failed to deactivate revision: {revision_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Route commands


@deployment.group()
def route() -> None:
    """Manage deployment routes"""


@route.command("list")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.option("--limit", type=int, default=50, help="Maximum items to return")
@click.option("--offset", type=int, default=0, help="Number of items to skip")
def list_routes_cmd(
    ctx: CLIContext,
    deployment_id: str,
    limit: int,
    offset: int,
) -> None:
    """List routes for a deployment."""
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.deployment import SearchRoutesRequest

    with Session() as session:
        try:
            request = SearchRoutesRequest(limit=limit, offset=offset)
            result = session.Deployment.search_routes(UUID(deployment_id), request)

            routes = result.routes
            if not routes:
                print("No routes found")
                return

            for rt in routes:
                print(f"ID: {rt.id}")
                print(f"Status: {rt.status}")
                print(f"Traffic Status: {rt.traffic_status}")
                print(f"Traffic Ratio: {rt.traffic_ratio}")
                print(f"Session: {rt.session_id or 'N/A'}")
                print(f"Created: {rt.created_at}")
                print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@route.command("traffic")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.argument("route_id", type=str)
@click.option("--activate", "traffic_status", flag_value="active", help="Enable traffic")
@click.option("--deactivate", "traffic_status", flag_value="inactive", help="Disable traffic")
def update_route_traffic_cmd(
    ctx: CLIContext,
    deployment_id: str,
    route_id: str,
    traffic_status: str | None,
) -> None:
    """Update route traffic status."""
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.data.model_deployment.types import RouteTrafficStatus
    from ai.backend.common.dto.manager.deployment import UpdateRouteTrafficStatusRequest

    from .pretty import print_done, print_fail

    if not traffic_status:
        print_fail("Must specify either --activate or --deactivate")
        sys.exit(ExitCode.FAILURE)

    with Session() as session:
        try:
            request = UpdateRouteTrafficStatusRequest(
                traffic_status=RouteTrafficStatus(traffic_status)
            )
            result = session.Deployment.update_route_traffic_status(
                UUID(deployment_id), UUID(route_id), request
            )
            print_done(f"Route traffic status updated: {route_id}")
            print(json.dumps(result.route.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Policy commands


@deployment.group()
def policy() -> None:
    """Manage deployment policies"""


@policy.command("info")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
def info_policy_cmd(ctx: CLIContext, deployment_id: str) -> None:
    """Display the deployment policy."""
    with Session() as session:
        try:
            result = session.Deployment.get_policy(UUID(deployment_id))
            print(
                json.dumps(result.deployment_policy.model_dump(mode="json"), indent=2, default=str)
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@policy.command("create")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.option(
    "--strategy",
    type=click.Choice(["ROLLING", "BLUE_GREEN"], case_sensitive=False),
    required=True,
    help="Deployment strategy type",
)
@click.option(
    "--rollback-on-failure",
    is_flag=True,
    default=False,
    help="Automatically rollback on failure",
)
@click.option("--max-surge", type=int, default=None, help="Max surge for rolling update")
@click.option(
    "--max-unavailable", type=int, default=None, help="Max unavailable for rolling update"
)
@click.option("--auto-promote", is_flag=True, default=False, help="Auto promote for blue-green")
@click.option(
    "--promote-delay", type=int, default=None, help="Promote delay seconds for blue-green"
)
def create_policy_cmd(
    ctx: CLIContext,
    deployment_id: str,
    strategy: str,
    rollback_on_failure: bool,
    max_surge: int | None,
    max_unavailable: int | None,
    auto_promote: bool,
    promote_delay: int | None,
) -> None:
    """Create a deployment policy."""
    rolling_update = None
    blue_green = None
    strategy_enum = DeploymentStrategy(strategy)

    if strategy_enum == DeploymentStrategy.ROLLING:
        rolling_kwargs: dict[str, int] = {}
        if max_surge is not None:
            rolling_kwargs["max_surge"] = max_surge
        if max_unavailable is not None:
            rolling_kwargs["max_unavailable"] = max_unavailable
        if rolling_kwargs:
            rolling_update = RollingUpdateConfigInput(**rolling_kwargs)
    elif strategy_enum == DeploymentStrategy.BLUE_GREEN:
        bg_kwargs: dict[str, int | bool] = {}
        if auto_promote:
            bg_kwargs["auto_promote"] = auto_promote
        if promote_delay is not None:
            bg_kwargs["promote_delay_seconds"] = promote_delay
        if bg_kwargs:
            blue_green = BlueGreenConfigInput(**bg_kwargs)

    with Session() as session:
        try:
            request = CreateDeploymentPolicyRequest(
                strategy=strategy_enum,
                rollback_on_failure=rollback_on_failure,
                rolling_update=rolling_update,
                blue_green=blue_green,
            )
            result = session.Deployment.create_policy(UUID(deployment_id), request)
            print_done(f"Deployment policy created for: {deployment_id}")
            print(
                json.dumps(result.deployment_policy.model_dump(mode="json"), indent=2, default=str)
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@policy.command("update")
@pass_ctx_obj
@click.argument("deployment_id", type=str)
@click.option(
    "--strategy",
    type=click.Choice(["ROLLING", "BLUE_GREEN"], case_sensitive=False),
    default=None,
    help="Deployment strategy type",
)
@click.option(
    "--rollback-on-failure/--no-rollback-on-failure",
    is_flag=True,
    default=None,
    help="Automatically rollback on failure",
)
@click.option("--max-surge", type=int, default=None, help="Max surge for rolling update")
@click.option(
    "--max-unavailable", type=int, default=None, help="Max unavailable for rolling update"
)
@click.option("--auto-promote", is_flag=True, default=False, help="Auto promote for blue-green")
@click.option(
    "--promote-delay", type=int, default=None, help="Promote delay seconds for blue-green"
)
def update_policy_cmd(
    ctx: CLIContext,
    deployment_id: str,
    strategy: str | None,
    rollback_on_failure: bool | None,
    max_surge: int | None,
    max_unavailable: int | None,
    auto_promote: bool,
    promote_delay: int | None,
) -> None:
    """Update a deployment policy. Only provided fields are updated."""
    strategy_enum = DeploymentStrategy(strategy) if strategy else None

    rolling_update = None
    blue_green = None
    if max_surge is not None or max_unavailable is not None:
        rolling_kwargs: dict[str, int] = {}
        if max_surge is not None:
            rolling_kwargs["max_surge"] = max_surge
        if max_unavailable is not None:
            rolling_kwargs["max_unavailable"] = max_unavailable
        rolling_update = RollingUpdateConfigInput(**rolling_kwargs)
    if auto_promote or promote_delay is not None:
        bg_kwargs: dict[str, int | bool] = {}
        if auto_promote:
            bg_kwargs["auto_promote"] = auto_promote
        if promote_delay is not None:
            bg_kwargs["promote_delay_seconds"] = promote_delay
        blue_green = BlueGreenConfigInput(**bg_kwargs)

    with Session() as session:
        try:
            request = UpdateDeploymentPolicyRequest(
                strategy=strategy_enum,
                rollback_on_failure=rollback_on_failure,
                rolling_update=rolling_update,
                blue_green=blue_green,
            )
            result = session.Deployment.update_policy(UUID(deployment_id), request)
            print_done(f"Deployment policy updated for: {deployment_id}")
            print(
                json.dumps(result.deployment_policy.model_dump(mode="json"), indent=2, default=str)
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
