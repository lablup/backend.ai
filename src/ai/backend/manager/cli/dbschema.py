from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import click
import sqlalchemy as sa

from ai.backend.common.logging import BraceStyleAdapter

from ..models.base import metadata
if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@click.group()
def cli(args) -> None:
    pass


@cli.command()
@click.option('-f', '--alembic-config',
              default='alembic.ini', metavar='PATH',
              help='The path to Alembic config file. '
                   '[default: alembic.ini]')
@click.pass_obj
def show(cli_ctx: CLIContext, alembic_config) -> None:
    '''Show the current schema information.'''
    with cli_ctx.logger:
        alembic_cfg = Config(alembic_config)
        sa_url = alembic_cfg.get_main_option('sqlalchemy.url')
        engine = sa.create_engine(sa_url)
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        script = ScriptDirectory.from_config(alembic_cfg)
        heads = script.get_heads()
        head_rev = heads[0] if len(heads) > 0 else None
        print(f'Current database revision: {current_rev}')
        print(f'The head revision of available migrations: {head_rev}')


@cli.command()
@click.option('-f', '--alembic-config', default='alembic.ini', metavar='PATH',
              help='The path to Alembic config file. '
                   '[default: alembic.ini]')
@click.pass_obj
def oneshot(cli_ctx: CLIContext, alembic_config) -> None:
    '''
    Set up your database with one-shot schema migration instead of
    iterating over multiple revisions if there is no existing database.
    It uses alembic.ini to configure database connection.

    Reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
               #building-an-up-to-date-database-from-scratch
    '''
    with cli_ctx.logger:
        alembic_cfg = Config(alembic_config)
        sa_url = alembic_cfg.get_main_option('sqlalchemy.url')

        engine = sa.create_engine(sa_url)
        engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        if current_rev is None:
            # For a fresh clean database, create all from scratch.
            # (it will raise error if tables already exist.)
            log.info('Detected a fresh new database.')
            log.info('Creating tables...')
            with engine.begin() as connection:
                alembic_cfg.attributes['connection'] = connection
                metadata.create_all(engine, checkfirst=False)
                log.info('Stamping alembic version to head...')
                command.stamp(alembic_cfg, 'head')
        else:
            # If alembic version info is already available, perform incremental upgrade.
            log.info('Detected an existing database.')
            log.info('Performing schema upgrade to head...')
            with engine.begin() as connection:
                alembic_cfg.attributes['connection'] = connection
                command.upgrade(alembic_cfg, 'head')

        log.info("If you don't need old migrations, delete them and set "
                 "\"down_revision\" value in the earliest migration to \"None\".")
