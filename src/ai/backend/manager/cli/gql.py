from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import click
import graphene

from ai.backend.common.logging import BraceStyleAdapter

from ..models.gql import Queries, Mutations

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@click.group()
def cli(args) -> None:
    pass


@cli.command()
@click.pass_obj
def show(cli_ctx: CLIContext) -> None:
    with cli_ctx.logger:
        schema = graphene.Schema(
            query=Queries,
            mutation=Mutations,
            auto_camelcase=False)
        log.info('======== GraphQL API Schema ========')
        print(str(schema))
