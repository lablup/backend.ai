from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import click
import graphene

from ..models.gql import Mutations, Queries

if TYPE_CHECKING:
    from .context import CLIContext

log = logging.getLogger(__spec__.name)  # type: ignore[name-defined]


@click.group()
def cli(args) -> None:
    pass


@cli.command()
@click.pass_obj
def dump_gql_schema(cli_ctx: CLIContext) -> None:
    schema = graphene.Schema(query=Queries, mutation=Mutations, auto_camelcase=False)
    log.info("======== GraphQL API Schema ========")
    print(str(schema))
