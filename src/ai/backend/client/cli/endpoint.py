import sys

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from ..output.fields import endpoint_fields
from .extensions import pass_ctx_obj
from .params import CommaSeparatedKVListParamType
from .pretty import print_done
from .types import CLIContext


@main.group()
def endpoint():
    """Set of endpoint operations"""


@endpoint.command()
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
            fetch_func = lambda pg_offset, pg_size: session.Endpoint.paginated_list(
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


@endpoint.command()
@pass_ctx_obj
@click.argument("url", metavar="URL", type=str)
@click.argument("image_ref", metavar="IMAGE_REF", type=str)
@click.option("-d", "--domain", type=str, default=None)
@click.option("-p", "--project", type=str, default=None)
@click.option("-r", "--resource-group", type=str, default=None)
@click.option(
    "--resource-slots",
    metavar="KEY=VAL[,KEY=VAL...]",
    type=CommaSeparatedKVListParamType(),
    default=dict,
    help="The resource options",
)
def create(
    ctx: CLIContext,
    url,
    image_ref,
    domain,
    project,
    resource_group,
    resource_slots,
):
    """
    Create a service endpoint with a backing inference session.

    \b
    MODEL: The model ID
    MODEL_VER: The version number or name of a model
    IMAGE_REF: The reference of container image to provide the serving framework
    """

    fields = (
        endpoint_fields["id"],
        endpoint_fields["image"],
        endpoint_fields["model_id"],
        endpoint_fields["domain_name"],
        endpoint_fields["project_id"],
        endpoint_fields["resource_group_name"],
        endpoint_fields["url"],
    )
    with Session() as session:
        try:
            result = session.Endpoint.create(
                image_ref,
                url,
                domain,
                project,
                resource_slots,
                resource_group,
            )
            ctx.output.print_item(
                result,
                fields,
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@endpoint.command()
@pass_ctx_obj
@click.argument("endpoint_id", metavar="ENDPOINT_ID", type=str)
def rm(ctx: CLIContext, endpoint_id):
    """
    Remove the service endpoint.

    \b
    ENDPOINT: The endpoint ID"""
    with Session() as session:
        try:
            session.Endpoint.delete(endpoint_id)
            print_done("Removed.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
