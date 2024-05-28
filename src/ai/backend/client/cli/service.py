import json
import sys
from typing import Literal, Optional, Sequence
from uuid import UUID

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.session.execute import (
    prepare_env_arg,
    prepare_mount_arg,
    prepare_resource_arg,
)
from ai.backend.client.compat import asyncio_run
from ai.backend.client.session import AsyncSession, Session
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import ClusterMode

from ..output.fields import routing_fields, service_fields
from ..output.types import FieldSpec
from .extensions import pass_ctx_obj
from .pretty import ProgressViewer, print_done, print_fail, print_warn
from .types import CLIContext

_default_detail_fields: Sequence[FieldSpec] = (
    service_fields["endpoint_id"],
    service_fields["name"],
    service_fields["image"],
    service_fields["desired_session_count"],
    service_fields["routings"],
    service_fields["session_owner"],
    service_fields["url"],
    service_fields["open_to_public"],
)


_default_routing_fields: Sequence[FieldSpec] = (
    routing_fields["status"],
    routing_fields["traffic_ratio"],
    routing_fields["session"],
    routing_fields["endpoint"],
)


def get_service_id(session: Session, name_or_id: str):
    try:
        session.Service(name_or_id).info()
        return name_or_id
    except Exception:
        services = session.Service.list(name=name_or_id)
        try:
            return services[0]["id"]
        except Exception as e:
            if isinstance(e, KeyError) or isinstance(e, IndexError):
                raise RuntimeError(f"Service {name_or_id} not found")
            else:
                raise e


@main.group()
def service():
    """Set of service operations"""


@service.command()
@pass_ctx_obj
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, filter_, order, offset, limit):
    """
    List the service endpoints.
    """

    with Session() as session:
        try:
            fetch_func = lambda pg_offset, pg_size: session.Service.paginated_list(
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
def info(ctx: CLIContext, service_name_or_id: str):
    """
    Display the detail of a service endpoint with its backing inference session.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            result = session.Service.detail(service_id, fields=_default_detail_fields)
            routes = result["routings"]
            ctx.output.print_item(
                result,
                _default_detail_fields,
            )
            print()
            for route in routes:
                print(f"Route {route['routing_id']}: ")
                ctx.output.print_item(
                    route,
                    _default_routing_fields,
                )
                print()
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("image", metavar="IMAGE", type=str)
@click.argument("model_name_or_id", metavar="MODEL_NAME_OR_ID", type=str)
@click.argument("initial_session_count", metavar="COUNT", type=int)
@click.option("-t", "--name", metavar="NAME", type=str, default=None)
@click.option("--model-version", metavar="VERSION", type=str, default=None)
@click.option("--model-mount-destination", metavar="PATH", type=str, default="/models")
# execution environment
@click.option(
    "-e",
    "--env",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help="Environment variable (may appear multiple times)",
)
@click.option(
    "-v",
    "--volume",
    "-m",
    "--mount",
    "mount",
    metavar="NAME[=PATH] or NAME[:PATH]",
    type=str,
    multiple=True,
    help=(
        "Name or ID of virtual folders to mount."
        "If path is not provided, virtual folder will be mounted under /home/work. "
        "When the target path is relative, it is placed under /home/work "
        "with auto-created parent directories if any. "
        "Absolute paths are mounted as-is, but it is prohibited to "
        "override the predefined Linux system directories."
    ),
)
# extra options
@click.option(
    "--bootstrap-script",
    metavar="PATH",
    type=click.File("r"),
    default=None,
    help="A user-defined script to execute on startup.",
)
@click.option(
    "-c",
    "--startup-command",
    metavar="COMMAND",
    default=None,
    help="Set the command to execute for batch-type sessions.",
)
@click.option(
    "-r",
    "--resources",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help=(
        "Set computation resources used by the session "
        "(e.g: -r cpu=2 -r mem=256 -r gpu=1)."
        "1 slot of cpu/gpu represents 1 core. "
        "The unit of mem(ory) is MiB."
    ),
)
@click.option(
    "--resource-opts",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help="Resource options for creating compute session (e.g: shmem=64m)",
)
@click.option(
    "--cluster-size",
    metavar="NUMBER",
    type=int,
    default=1,
    help="The size of cluster in number of containers.",
)
@click.option(
    "--cluster-mode",
    metavar="MODE",
    type=click.Choice([*ClusterMode], case_sensitive=False),
    default=ClusterMode.SINGLE_NODE,
    help="The mode of clustering.",
)
@click.option("-d", "--domain", type=str, default="default")
@click.option("-p", "--project", type=str, default="default")
# extra options
@click.option(
    "--bootstrap-script",
    metavar="PATH",
    type=click.File("r"),
    default=None,
    help="A user-defined script to execute on startup.",
)
# extra options
@click.option("--tag", type=str, default=None, help="User-defined tag string to annotate sessions.")
@click.option(
    "--arch",
    "--architecture",
    "architecture",
    metavar="ARCH_NAME",
    type=str,
    default=DEFAULT_IMAGE_ARCH,
    help="Architecture of the image to use.",
)
@click.option(
    "--scaling-group",
    "--sgroup",
    type=str,
    default="default",
    help=(
        "The scaling group to execute session. If not specified, "
        "all available scaling groups are included in the scheduling."
    ),
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    metavar="ACCESS_KEY",
    default=None,
    help="Set the owner of the target session explicitly.",
)
@click.option(
    "--model-definition-path",
    metavar="PATH",
    default=None,
    help="Relative path to model definition file. Defaults to `model-definition.yaml`.",
)
@click.option(
    "--public",
    "--expose-to-public",
    is_flag=True,
    help=(
        "Visibility of API Endpoint which serves inference workload."
        "If set to true, no authentication will be required to access the endpoint."
    ),
)
def create(
    ctx: CLIContext,
    image: str,
    model_name_or_id: str,
    initial_session_count: int,
    *,
    name: Optional[str],
    model_version: Optional[str],
    model_mount_destination: Optional[str],
    env: Sequence[str],
    mount: Sequence[str],
    startup_command: Optional[str],
    resources: Sequence[str],
    resource_opts: Sequence[str],
    cluster_size: int,
    cluster_mode: Literal["single-node", "multi-node"],
    domain: Optional[str],
    project: Optional[str],
    bootstrap_script: Optional[str],
    tag: Optional[str],
    architecture: Optional[str],
    scaling_group: Optional[str],
    owner: Optional[str],
    model_definition_path: Optional[str],
    public: bool,
):
    """
    Create a service endpoint with a backing inference session.

    \b
    MODEL_ID: The model ID

    """
    envs = prepare_env_arg(env)
    mount, mount_map, mount_options = prepare_mount_arg(mount, escape=True)
    parsed_resources = prepare_resource_arg(resources)
    parsed_resource_opts = prepare_resource_arg(resource_opts)
    body = {
        "service_name": name,
        "model_version": model_version,
        "envs": envs,
        "extra_mounts": mount,
        "extra_mount_map": mount_map,
        "extra_mount_options": mount_options,
        "startup_command": startup_command,
        "resources": parsed_resources,
        "resource_opts": parsed_resource_opts,
        "cluster_size": cluster_size,
        "cluster_mode": cluster_mode,
        "bootstrap_script": bootstrap_script,
        "tag": tag,
        "architecture": architecture,
        "scaling_group": scaling_group,
        "expose_to_public": public,
        "model_definition_path": model_definition_path,
    }
    if model_mount_destination:
        body["model_mount_destination"] = model_mount_destination
    if domain:
        body["domain_name"] = domain
    if project:
        body["group_name"] = project
    if owner:
        body["owner_access_key"] = owner

    with Session() as session:
        try:
            result = session.Service.create(
                image,
                model_name_or_id,
                initial_session_count,
                **body,
            )
            ctx.output.print_item(
                result,
                [*service_fields.values()],
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("image", metavar="IMAGE", type=str)
@click.argument("model_name_or_id", metavar="MODEL_NAME_OR_ID", type=str)
@click.option("-t", "--name", metavar="NAME", type=str, default=None)
@click.option("--model-version", metavar="VERSION", type=int, default=1)
@click.option("--model-mount-destination", metavar="PATH", type=str, default="/models")
# execution environment
@click.option(
    "-e",
    "--env",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help="Environment variable (may appear multiple times)",
)
# extra options
@click.option(
    "--bootstrap-script",
    metavar="PATH",
    type=click.File("r"),
    default=None,
    help="A user-defined script to execute on startup.",
)
@click.option(
    "-c",
    "--startup-command",
    metavar="COMMAND",
    default=None,
    help="Set the command to execute for batch-type sessions.",
)
@click.option(
    "-r",
    "--resources",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help=(
        "Set computation resources used by the session "
        "(e.g: -r cpu=2 -r mem=256 -r gpu=1)."
        "1 slot of cpu/gpu represents 1 core. "
        "The unit of mem(ory) is MiB."
    ),
)
@click.option(
    "--resource-opts",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help="Resource options for creating compute session (e.g: shmem=64m)",
)
@click.option(
    "--cluster-size",
    metavar="NUMBER",
    type=int,
    default=1,
    help="The size of cluster in number of containers.",
)
@click.option(
    "--cluster-mode",
    metavar="MODE",
    type=click.Choice([*ClusterMode], case_sensitive=False),
    default=ClusterMode.SINGLE_NODE,
    help="The mode of clustering.",
)
@click.option("-d", "--domain", type=str, default="default")
@click.option("-p", "--project", type=str, default="default")
# extra options
@click.option(
    "--bootstrap-script",
    metavar="PATH",
    type=click.File("r"),
    default=None,
    help="A user-defined script to execute on startup.",
)
# extra options
@click.option("--tag", type=str, default=None, help="User-defined tag string to annotate sessions.")
@click.option(
    "--arch",
    "--architecture",
    "architecture",
    metavar="ARCH_NAME",
    type=str,
    default=DEFAULT_IMAGE_ARCH,
    help="Architecture of the image to use.",
)
@click.option(
    "--scaling-group",
    "--sgroup",
    type=str,
    default="default",
    help=(
        "The scaling group to execute session. If not specified, "
        "all available scaling groups are included in the scheduling."
    ),
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    metavar="ACCESS_KEY",
    default=None,
    help="Set the owner of the target session explicitly.",
)
@click.option(
    "--public",
    "--expose-to-public",
    is_flag=True,
    help=(
        "Visibility of API Endpoint which serves inference workload."
        "If set to true, no authentication will be required to access the endpoint."
    ),
)
def try_start(
    ctx: CLIContext,
    image: str,
    model_name_or_id: str,
    *,
    name: Optional[str],
    model_version: int,
    model_mount_destination: Optional[str],
    env: Sequence[str],
    startup_command: Optional[str],
    resources: Sequence[str],
    resource_opts: Sequence[str],
    cluster_size: int,
    cluster_mode: Literal["single-node", "multi-node"],
    domain: Optional[str],
    project: Optional[str],
    bootstrap_script: Optional[str],
    tag: Optional[str],
    architecture: Optional[str],
    scaling_group: Optional[str],
    owner: Optional[str],
    public: bool,
):
    """
    Tries to create a model service session and return whether the server has successfully started or not.

    \b
    MODEL_ID: The model ID

    """
    envs = prepare_env_arg(env)
    parsed_resources = prepare_resource_arg(resources)
    parsed_resource_opts = prepare_resource_arg(resource_opts)
    body = {
        "service_name": name,
        "model_version": model_version,
        "envs": envs,
        "startup_command": startup_command,
        "resources": parsed_resources,
        "resource_opts": parsed_resource_opts,
        "cluster_size": cluster_size,
        "cluster_mode": cluster_mode,
        "bootstrap_script": bootstrap_script,
        "tag": tag,
        "architecture": architecture,
        "scaling_group": scaling_group,
        "expose_to_public": public,
    }
    if model_mount_destination:
        body["model_mount_destination"] = model_mount_destination
    if domain:
        body["domain_name"] = domain
    if project:
        body["group_name"] = project
    if owner:
        body["owner_access_key"] = owner

    with Session() as session:
        try:
            result = session.Service.try_start(
                image,
                model_name_or_id,
                **body,
            )
            ctx.output.print_item(
                result,
                [*service_fields.values()],
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)

    async def try_start_tracker(bgtask_id):
        async with AsyncSession() as session:
            try:
                bgtask = session.BackgroundTask(bgtask_id)
                completion_msg_func = lambda: print_done("Model service validation started.")
                async with (
                    bgtask.listen_events() as response,
                    ProgressViewer("Starting the session...") as viewer,
                ):
                    async for ev in response:
                        data = json.loads(ev.data)
                        if ev.event == "bgtask_updated":
                            print(data["message"])
                            if viewer.tqdm is None:
                                pbar = await viewer.to_tqdm()
                            else:
                                pbar.total = data["total_progress"]
                                pbar.update(data["current_progress"] - pbar.n)
                        elif ev.event == "bgtask_failed":
                            error_msg = data["message"]
                            completion_msg_func = lambda: print_fail(
                                f"Error during the operation: {error_msg}",
                            )
                        elif ev.event == "bgtask_cancelled":
                            completion_msg_func = lambda: print_warn(
                                "The operation has been cancelled in the middle. "
                                "(This may be due to server shutdown.)",
                            )
            finally:
                completion_msg_func()

    asyncio_run(try_start_tracker(result["task_id"]))


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
def rm(ctx: CLIContext, service_name_or_id):
    """
    Remove the service endpoint.

    \b
    SERVICE_ID: The endpoint ID"""
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            session.Service(service_id).delete()
            print_done("Removed.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
def sync(ctx: CLIContext, service_name_or_id: str):
    """
    Sync route status with AppProxy.

    \b
    SERVICE_ID: The endpoint ID
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            session.Service(service_id).sync()
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
@click.argument("target_count", metavar="COUNT", type=int)
def scale(ctx: CLIContext, service_name_or_id: str, target_count: int):
    """
    Start or resume the service endpoint to handle the incoming traffic.

    \b
    SERVICE_ID: The endpoint ID
    COUNT: Number of desired sessions in an endpoint
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            session.Service(service_id).scale(target_count)
            print_done("Triggered scaling.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
@click.argument("duration", metavar="DURATION", type=str)
@click.option("-q", "--quiet", is_flag=True)
def generate_token(ctx: CLIContext, service_name_or_id: str, duration: str, quiet: bool):
    """
    Generate an API token to communicate with inference endpoint.

    \b
    SERVICE_ID: The endpoint ID
    DURATION: Total amount of time for token to be alive
              in short format (e.g. 3d, 2h, ...)
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            resp = session.Service(service_id).generate_api_token(duration)
            if quiet:
                print(resp["token"])
            else:
                print_done(f"Generated API token {resp['token']}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
def get_endpoint(ctx: CLIContext, service_name_or_id: str):
    """
    Returns API Endpoint URL of the service.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            result = session.Service.detail(service_id, fields=_default_detail_fields)
            print(result["url"])
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
@click.argument("route_id", metavar="ROUTE_ID", type=str)
@click.argument("ratio", metavar="RATIO", type=float)
def update_traffic_ratio(ctx: CLIContext, service_name_or_id: str, route_id: str, ratio: float):
    """
    Update traffic ratio of single route.

    \b
    SERVICE_ID: The endpoint ID
    ROUTE_ID: The route ID
    RATIO: Target traffic ratio
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            session.Service(service_id).update_traffic_ratio(UUID(route_id), ratio)
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_name_or_id", metavar="SERVICE_NAME_OR_ID", type=str)
@click.argument("route_id", metavar="ROUTE_ID", type=str)
@click.argument("ratio", metavar="RATIO", type=float)
def downscale_route(ctx: CLIContext, service_name_or_id: str, route_id: str):
    """
    Destroy route and its associated session and
    decrement desired session count of endpoint

    \b
    SERVICE_ID: The endpoint ID
    ROUTE_ID: Route ID to destroy
    """
    with Session() as session:
        try:
            service_id = get_service_id(session, service_name_or_id)
            session.Service(service_id).downscale_single_route(UUID(route_id))
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
