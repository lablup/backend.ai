import sys

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from .extensions import pass_ctx_obj
from .params import CommaSeparatedKVListParamType
from .pretty import print_error
from .types import CLIContext


@main.group()
def serve():
    """Set of service operations"""


@serve.command()
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
            fetch_func = lambda pg_offset, pg_size: session.Serve.paginated_list(
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
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@serve.command()
@click.argument("endpoint_id", metavar="ENDPOINT", type=str)
def info(endpoint_id):
    """
    Display the detail of a service endpoint

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            result = session.Serve(endpoint_id).info()
            print("Serve info")
            print("- Endpoint ID: {0}".format(result["endpoint_id"]))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@serve.command()
@click.argument("endpoint_id", metavar="ENDPOINT", type=str)
@click.argument("model_id", metavar="MODEL", type=str)
@click.argument("model_version", metavar="MODEL_VER", type=str)
@click.argument("image_ref", metavar="IMAGE_REF", type=str)
@click.option("-p", "--project", type=str, default=None)
@click.option(
    "--resource-opts", metavar="KEY=VAL", type=CommaSeparatedKVListParamType(), default=None
)
def create(endpoint_id, model_id, model_version, image_ref, project, resource_opts):
    """
    Create a service endpoint.

    \b
    ENDPOINT: The endpoint ID
    MODEL: The model ID
    MODEL_VER: The version number or name of a model
    IMAGE_REF: The reference of container image to provide the serving framework
    """
    with Session() as session:
        try:
            serving = session.Serve(endpoint_id)
            serving.create(
                model_id=model_id,
                model_version=model_version,
                image_ref=image_ref,
                project=project,
                resource_opts=resource_opts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@serve.command()
@click.argument("endpoint_id", metavar="ENDPOINT", type=str)
def start(endpoint_id):
    """
    Start or resume the service endpoint to handle the incoming traffic.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            serving = session.Serve(endpoint_id)
            serving.start()
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@serve.command()
@click.argument("endpoint_id", metavar="ENDPOINT", type=str)
def stop(endpoint_id):
    """
    Stop the service endpoint without destroying it.

    \b
    ENDPOINT: The endpoint ID
    """
    with Session() as session:
        try:
            serving = session.Serve(endpoint_id)
            serving.stop()
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@serve.command()
@click.argument("endpoint_id", metavar="ENDPOINT", type=str)
def rm(endpoint_id):
    """
    Remove the service endpoint.

    \b
    ENDPOINT: The endpoint ID"""
    with Session() as session:
        try:
            serving = session.Serve(endpoint_id)
            serving.delete()
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


def _invoke_cmd(name: str = "predict", docs: str = None):
    @click.argument("endpoint_id", metavar="ENDPOINT", type=str)
    @click.option(
        "--input-args", metavar="KEY=VAL", type=CommaSeparatedKVListParamType(), default=None
    )
    def invoke(endpoint_id, input_args):
        """
        Invoke the service endpoint using the given parameters.

        \b
        ENDPOINT: The endpoint ID
        """
        with Session() as session:
            try:
                serving = session.Serve(endpoint_id)
                serving.invoke(input_args)
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)

    invoke.__name__ = name
    if docs is not None:
        invoke.__doc__ = docs
    return invoke


main.command()(_invoke_cmd(name="predict", docs='Alias of "serve invoke"'))
serve.command()(_invoke_cmd())
