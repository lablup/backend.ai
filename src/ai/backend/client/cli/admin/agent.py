from __future__ import annotations

import sys

import click

from ai.backend.client.session import Session
from ai.backend.client.output.fields import agent_fields
from ..types import CLIContext
from . import admin


@admin.group()
def agent():
    """
    Agent administration commands.
    """


@agent.command()
@click.pass_obj
@click.argument('agent_id')
def info(ctx: CLIContext, agent_id: str) -> None:
    """
    Show the information about the given agent.
    """
    fields = [
        agent_fields['id'],
        agent_fields['status'],
        agent_fields['region'],
        agent_fields['architecture'],
        agent_fields['first_contact'],
        agent_fields['cpu_cur_pct'],
        agent_fields['available_slots'],
        agent_fields['occupied_slots'],
        agent_fields['hardware_metadata'],
        agent_fields['live_stat'],
    ]
    with Session() as session:
        try:
            item = session.Agent.detail(agent_id=agent_id, fields=fields)
            ctx.output.print_item(item, fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@agent.command()
@click.pass_obj
@click.option('-s', '--status', type=str, default='ALIVE',
              help='Filter agents by the given status.')
@click.option('--scaling-group', '--sgroup', type=str, default=None,
              help='Filter agents by the scaling group.')
@click.option('--filter', 'filter_', default=None,
              help='Set the query filter expression.')
@click.option('--order', default=None,
              help='Set the query ordering expression.')
@click.option('--offset', default=0,
              help='The index of the current page start for pagination.')
@click.option('--limit', default=None,
              help='The page size for pagination.')
def list(
    ctx: CLIContext,
    status: str,
    scaling_group: str | None,
    filter_: str | None,
    order: str | None,
    offset: int,
    limit: int | None,
) -> None:
    """
    List agents.
    (super-admin privilege required)
    """
    fields = [
        agent_fields['id'],
        agent_fields['status'],
        agent_fields['architecture'],
        agent_fields['scaling_group'],
        agent_fields['region'],
        agent_fields['first_contact'],
        agent_fields['cpu_cur_pct'],
        agent_fields['mem_cur_bytes'],
        agent_fields['available_slots'],
        agent_fields['occupied_slots'],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.Agent.paginated_list(
                status,
                scaling_group,
                fields=fields,
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
        sys.exit(1)


@admin.group()
def watcher():
    """
    Agent watcher commands.

    Available only for Linux-based agents.
    """


@watcher.command()
@click.pass_obj
@click.argument('agent', type=str)
def status(ctx: CLIContext, agent: str) -> None:
    """
    Get agent and watcher status.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    """
    with Session() as session:
        try:
            status = session.AgentWatcher.get_status(agent)
            print(status)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@watcher.command()
@click.pass_obj
@click.argument('agent', type=str)
def agent_start(ctx: CLIContext, agent: str) -> None:
    """
    Start agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    """
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_start(agent)
            print(status)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@watcher.command()
@click.pass_obj
@click.argument('agent', type=str)
def agent_stop(ctx: CLIContext, agent: str) -> None:
    """
    Stop agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    """
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_stop(agent)
            print(status)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@watcher.command()
@click.pass_obj
@click.argument('agent', type=str)
def agent_restart(ctx: CLIContext, agent: str) -> None:
    """
    Restart agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    """
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_restart(agent)
            print(status)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)
