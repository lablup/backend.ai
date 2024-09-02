import sys
import uuid
from typing import Any, Iterable

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session

from ..output.fields import network_fields
from .pretty import print_done

_default_list_fields = (
    network_fields["name"],
    network_fields["ref_name"],
    network_fields["driver"],
    network_fields["created_at"],
)


@main.group()
def network():
    """Set of inter-container network operations"""


@network.command()
@pass_ctx_obj
@click.argument("project", type=str, metavar="PROJECT_ID_OR_NAME")
@click.argument("name", type=str, metavar="NAME")
@click.option("-d", "--driver", default=None, help="Set the network driver.")
def create(ctx: CLIContext, project, name, driver):
    """Create a new network interface."""

    with Session() as session:
        proj_id: str | None = None

        try:
            uuid.UUID(project)
        except ValueError:
            pass
        else:
            if session.Group.detail(project):
                proj_id = project

        if not proj_id:
            projects = session.Group.from_name(project)
            if not projects:
                ctx.output.print_fail(f"Project '{project}' not found.")
                sys.exit(ExitCode.FAILURE)
            proj_id = projects[0]["id"]

        try:
            network = session.Network.create(proj_id, name, driver=driver)
            print_done(f"Network {name} (ID {network.network_id}) created.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@network.command()
@pass_ctx_obj
@click.option(
    "-f",
    "--format",
    default=None,
    help="Display only specified fields.  When specifying multiple fields separate them with comma (,).",
)
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, format, filter_, order, offset, limit):
    """List all available network interfaces."""

    if format:
        try:
            fields = [network_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = None
    with Session() as session:
        try:
            fetch_func = lambda pg_offset, pg_size: session.Network.paginated_list(
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
                fields=fields,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@network.command()
@pass_ctx_obj
@click.argument("network", type=str, metavar="NETWORK_ID_OR_NAME")
@click.option(
    "-f",
    "--format",
    default=None,
    help="Display only specified fields.  When specifying multiple fields separate them with comma (,).",
)
def get(ctx: CLIContext, network, format):
    fields: Iterable[Any]
    if format:
        try:
            fields = [network_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = _default_list_fields

    with Session() as session:
        try:
            network_info = session.Network(uuid.UUID(network)).get(fields=fields)
        except (ValueError, BackendAPIError):
            networks = session.Network.paginated_list(filter=f'name == "{network}"', fields=fields)
            if networks.total_count == 0:
                ctx.output.print_fail(f"Network {network} not found.")
                sys.exit(ExitCode.FAILURE)
            if networks.total_count > 1:
                ctx.output.print_fail(
                    f"One or more networks found with name {network}. Try mentioning network ID instead of name to resolve the issue."
                )
                sys.exit(ExitCode.FAILURE)
            network_info = networks.items[0]

        ctx.output.print_item(network_info, fields)


@network.command()
@pass_ctx_obj
@click.argument("network", type=str, metavar="NETWORK_ID_OR_NAME")
def delete(ctx: CLIContext, network):
    with Session() as session:
        try:
            network_info = session.Network(uuid.UUID(network)).get(fields=[network_fields["id"]])
        except (ValueError, BackendAPIError):
            networks = session.Network.paginated_list(
                filter=f'name == "{network}"', fields=[network_fields["id"]]
            )
            if networks.total_count == 0:
                ctx.output.print_fail(f"Network {network} not found.")
                sys.exit(ExitCode.FAILURE)
            if networks.total_count > 1:
                ctx.output.print_fail(
                    f"One or more networks found with name {network}. Try mentioning network ID instead of name to resolve the issue."
                )
                sys.exit(ExitCode.FAILURE)
            network_info = networks.items[0]

        try:
            session.Network(uuid.UUID(network_info["row_id"])).delete()
            print_done(f"Network {network} has been deleted.")
        except BackendAPIError as e:
            ctx.output.print_fail(f"Failed to delete network {network}:")
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
