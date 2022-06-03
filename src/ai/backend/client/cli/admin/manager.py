import json
from pathlib import Path
import sys
import time

import appdirs
import click
from tabulate import tabulate

from ai.backend.cli.interaction import ask_yn

from . import admin
from ..pretty import print_done, print_error, print_fail, print_info, print_wait
from ..session import Session


@admin.group()
def manager():
    """Set of manager control operations."""


@manager.command()
def status():
    """Show the manager's current status."""
    try:
        with Session() as session:
            resp = session.Manager.status()
            print(tabulate([('Status', 'Active Sessions'),
                            (resp['status'], resp['active_sessions'])],
                           headers='firstrow'))
    except Exception as e:
        print_error(e)
        sys.exit(1)


@manager.command()
@click.option('--wait', is_flag=True,
              help='Hold up freezing the manager until '
                   'there are no running sessions in the manager.')
@click.option('--force-kill', is_flag=True,
              help='Kill all running sessions immediately and freeze the manager.')
def freeze(wait, force_kill):
    """Freeze manager."""
    if wait and force_kill:
        print('You cannot use both --wait and --force-kill options '
              'at the same time.', file=sys.stderr)
        return
    try:
        with Session() as session:
            if wait:
                while True:
                    resp = session.Manager.status()
                    active_sessions_num = resp['active_sessions']
                    if active_sessions_num == 0:
                        break
                    print_wait('Waiting for all sessions terminated... ({0} left)'
                               .format(active_sessions_num))
                    time.sleep(3)
                print_done('All sessions are terminated.')

            if force_kill:
                print_wait('Killing all sessions...')

            session.Manager.freeze(force_kill=force_kill)

            if force_kill:
                print_done('All sessions are killed.')

            print('Manager is successfully frozen.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@manager.command()
def unfreeze():
    """Unfreeze manager."""
    try:
        with Session() as session:
            session.Manager.unfreeze()
            print('Manager is successfully unfrozen.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@admin.group()
def announcement():
    """Global announcement related commands"""


@announcement.command()
def get():
    """Get current announcement."""
    try:
        with Session() as session:
            result = session.Manager.get_announcement()
            if result.get('enabled', False):
                msg = result.get('message')
                print(msg)
            else:
                print('No announcements.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@announcement.command()
@click.option('-m', '--message', default=None, type=click.STRING)
def update(message):
    """
    Post new announcement.

    MESSAGE: Announcement message.
    """
    try:
        with Session() as session:
            if message is None:
                message = click.edit(
                    "<!-- Use Markdown format to edit the announcement message -->",
                )
            if message is None:
                print_info('Cancelled')
                sys.exit(1)
            session.Manager.update_announcement(enabled=True, message=message)
        print_done('Posted new announcement.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@announcement.command()
def delete():
    """Delete current announcement."""
    if not ask_yn():
        print_info('Cancelled.')
        sys.exit(1)
    try:
        with Session() as session:
            session.Manager.update_announcement(enabled=False)
        print_done('Deleted announcement.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@announcement.command()
def dismiss():
    """Do not show the same announcement again."""
    if not ask_yn():
        print_info('Cancelled.')
        sys.exit(1)
    try:
        local_state_path = Path(appdirs.user_state_dir('backend.ai', 'Lablup'))
        with open(local_state_path / 'announcement.json', 'rb') as f:
            state = json.load(f)
        state['dismissed'] = True
        with open(local_state_path / 'announcement.json', 'w') as f:
            json.dump(state, f)
        print_done('Dismissed the last shown announcement.')
    except (IOError, json.JSONDecodeError):
        print_fail('No announcements seen yet.')
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


@manager.group()
def scheduler():
    """
    The scheduler operation command group.
    """
    pass


@scheduler.command()
@click.argument('agent_ids', nargs=-1)
def include_agents(agent_ids):
    """
    Include agents in scheduling, meaning that the given agents
    will be considered to be ready for creating new session containers.
    """
    try:
        with Session() as session:
            session.Manager.scheduler_op('include-agents', agent_ids)
        print_done('The given agents now accepts new sessions.')
    except Exception as e:
        print_error(e)
        sys.exit(1)


@scheduler.command()
@click.argument('agent_ids', nargs=-1)
def exclude_agents(agent_ids):
    """
    Exclude agents from scheduling, meaning that the given agents
    will no longer start new sessions unless they are "included" again,
    regardless of their restarts and rejoining events.
    """
    try:
        with Session() as session:
            session.Manager.scheduler_op('exclude-agents', agent_ids)
        print_done('The given agents will no longer start new sessions.')
    except Exception as e:
        print_error(e)
        sys.exit(1)
