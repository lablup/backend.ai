import sys

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.client.session import Session
from ai.backend.client.func.domain import (
    _default_list_fields,
    _default_detail_fields,
)
# from ai.backend.client.output.fields import domain_fields
from . import admin
from ..pretty import print_info

from ..types import CLIContext


@admin.group()
def domain():
    """
    Domain administration commands.
    """


@domain.command()
@click.pass_obj
@click.argument('name', type=str)
def info(ctx: CLIContext, name: str) -> None:
    """
    Show the information about the given domain.
    If name is not give, user's own domain information will be retrieved.
    """
    with Session() as session:
        try:
            item = session.Domain.detail(name=name)
            ctx.output.print_item(item, _default_detail_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@domain.command()
@click.pass_obj
def list(ctx: CLIContext) -> None:
    """
    List and manage domains.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.Domain.list()
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@domain.command()
@click.pass_obj
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new domain')
@click.option('-i', '--inactive', is_flag=True,
              help='New domain will be inactive.')
@click.option('--total-resource-slots', type=str, default='{}',
              help='Set total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
@click.option('--allowed-docker-registries', type=str, multiple=True,
              help='Allowed docker registries.')
def add(ctx: CLIContext, name, description, inactive, total_resource_slots,
        allowed_vfolder_hosts, allowed_docker_registries):
    """
    Add a new domain.

    NAME: Name of new domain.
    """
    with Session() as session:
        try:
            data = session.Domain.create(
                name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name='domain',
                action_name='add',
            )
            sys.exit(1)
        if not data['ok']:
            ctx.output.print_mutation_error(
                msg=data['msg'],
                item_name='domain',
                action_name='add',
            )
            sys.exit(1)
        ctx.output.print_mutation_result(
            data,
            item_name='domain',
        )


@domain.command()
@click.pass_obj
@click.argument('name', type=str, metavar='NAME')
@click.option('--new-name', type=str, help='New name of the domain')
@click.option('--description', type=str, help='Description of the domain')
@click.option('--is-active', type=bool, help='Set domain inactive.')
@click.option('--total-resource-slots', type=str,
              help='Update total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
@click.option('--allowed-docker-registries', type=str, multiple=True,
              help='Allowed docker registries.')
def update(ctx: CLIContext, name, new_name, description, is_active, total_resource_slots,
           allowed_vfolder_hosts, allowed_docker_registries):
    """
    Update an existing domain.

    NAME: Name of new domain.
    """
    with Session() as session:
        try:
            data = session.Domain.update(
                name,
                new_name=new_name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name='domain',
                action_name='update',
            )
            sys.exit(1)
        if not data['ok']:
            ctx.output.print_mutation_error(
                msg=data['msg'],
                item_name='domain',
                action_name='update',
            )
            sys.exit(1)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                'name': name,
            },
        )


@domain.command()
@click.pass_obj
@click.argument('name', type=str, metavar='NAME')
def delete(ctx: CLIContext, name):
    """
    Inactive an existing domain.

    NAME: Name of a domain to inactive.
    """
    with Session() as session:
        try:
            data = session.Domain.delete(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name='domain',
                action_name='deletion',
            )
            sys.exit(1)
        if not data['ok']:
            ctx.output.print_mutation_error(
                msg=data['msg'],
                item_name='domain',
                action_name='deletion',
            )
            sys.exit(1)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                'name': name,
            },
        )


@domain.command()
@click.pass_obj
@click.argument('name', type=str, metavar='NAME')
def purge(ctx: CLIContext, name):
    """
    Delete an existing domain.

    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            data = session.Domain.purge(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name='domain',
                action_name='purge',
            )
            sys.exit(1)
        if not data['ok']:
            ctx.output.print_mutation_error(
                msg=data['msg'],
                item_name='domain',
                action_name='purge',
            )
            sys.exit(1)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                'name': name,
            },
        )
