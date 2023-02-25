import sys

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from ..output.fields import service_fields
from ..output.types import FieldSpec
from .extensions import pass_ctx_obj
from .params import CommaSeparatedKVListParamType
from .pretty import print_done, print_error
from .types import CLIContext


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
@click.argument("service_id", metavar="SERVICE_ID", type=str)
def info(ctx: CLIContext, service_id: str):
    """
    Display the detail of a service endpoint with its backing inference session.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            result = session.Service.info(service_id)
            ctx.output.print_item(
                result,
                [
                    FieldSpec("service_id"),
                ],
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("model_id", metavar="MODEL", type=str)
@click.argument("model_version", metavar="MODEL_VER", type=str)
@click.argument("image_ref", metavar="IMAGE_REF", type=str)
@click.option("-t", "--name", metavar="NAME", type=str, default=None)
@click.option("-e", "--endpoint", type=str, default=None)
@click.option("-p", "--project", type=str, default=None)
@click.option(
    "--resource-opts",
    metavar="KEY=VAL[,KEY=VAL...]",
    type=CommaSeparatedKVListParamType(),
    default=dict,
    help="The resource options",
)
def create(
    ctx: CLIContext,
    model_id,
    model_version,
    image_ref,
    name,
    endpoint,
    project,
    resource_opts,
):
    """
    Create a service endpoint with a backing inference session.

    \b
    MODEL: The model ID
    MODEL_VER: The version number or name of a model
    IMAGE_REF: The reference of container image to provide the serving framework
    """
    with Session() as session:
        try:
            result = session.Service.create(
                model_id=model_id,
                model_version=model_version,
                image_ref=image_ref,
                project=project,
                resource_opts=resource_opts,
                endpoint_id=endpoint,
                service_name=name,
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
@click.argument("service_id", metavar="SERVICE_ID", type=str)
def start(ctx: CLIContext, service_id):
    """
    Start or resume the service endpoint to handle the incoming traffic.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            session.Service.start(service_id)
            print_done("Started.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_id", metavar="SERVICE_ID", type=str)
def stop(ctx: CLIContext, service_id):
    """
    Stop the service endpoint without destroying it.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            session.Service.stop(service_id)
            print_done("Stopped.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@service.command()
@pass_ctx_obj
@click.argument("service_id", metavar="SERVICE_ID", type=str)
def rm(ctx: CLIContext, service_id):
    """
    Remove the service endpoint.

    \b
    ENDPOINT: The endpoint ID"""
    with Session() as session:
        try:
            session.Service.delete(service_id)
            print_done("Removed.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


def _invoke_cmd(docs: str = None):
    @click.argument("service_id", metavar="SERVICE_ID", type=str)
    @click.option(
        "--input-args",
        metavar="KEY=VAL[,KEY=VAL...]",
        type=CommaSeparatedKVListParamType(),
        default=None,
        help="The input arguments",
    )
    def invoke(service_id, input_args):
        """
        Invoke the service endpoint using the given parameters.

        \b
        ENDPOINT: The endpoint ID
        """
        with Session() as session:
            try:
                session.Service.invoke(service_id, input_args)
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)

    if docs is not None:
        invoke.__doc__ = docs
    return invoke


main.command(aliases=["predict"])(_invoke_cmd(docs='Alias of "service invoke"'))
service.command()(_invoke_cmd())
