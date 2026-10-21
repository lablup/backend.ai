import sys
import time

import click
from tabulate import tabulate

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.pretty import print_done, print_error, print_wait

from . import admin


@admin.group()
def manager() -> None:
    """Set of manager control operations."""


@manager.command()
def status() -> None:
    """Show the manager's current status."""
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            resp = session.Manager.status()
            print(
                tabulate(
                    [("Status", "Active Sessions"), (resp["status"], resp["active_sessions"])],
                    headers="firstrow",
                )
            )
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@manager.command()
@click.option(
    "--wait",
    is_flag=True,
    help="Hold up freezing the manager until there are no running sessions in the manager.",
)
@click.option(
    "--force-kill",
    is_flag=True,
    help="Kill all running sessions immediately and freeze the manager.",
)
def freeze(wait: bool, force_kill: bool) -> None:
    """Freeze manager."""
    from ai.backend.client.cli.session.lifecycle import Session

    if wait and force_kill:
        print(
            "You cannot use both --wait and --force-kill options at the same time.",
            file=sys.stderr,
        )
        return
    try:
        with Session() as session:
            if wait:
                while True:
                    resp = session.Manager.status()
                    active_sessions_num = resp["active_sessions"]
                    if active_sessions_num == 0:
                        break
                    print_wait(
                        f"Waiting for all sessions terminated... ({active_sessions_num} left)"
                    )
                    time.sleep(3)
                print_done("All sessions are terminated.")

            if force_kill:
                print_wait("Killing all sessions...")

            _ = session.Manager.freeze(force_kill=force_kill)

            if force_kill:
                print_done("All sessions are killed.")

            print("Manager is successfully frozen.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@manager.command()
def unfreeze() -> None:
    """Unfreeze manager."""
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            _ = session.Manager.unfreeze()
            print("Manager is successfully unfrozen.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@manager.group()
def scheduler() -> None:
    """
    The scheduler operation command group.
    """
    pass


@scheduler.command()
@click.argument("agent_ids", nargs=-1)
def include_agents(agent_ids: tuple[str, ...]) -> None:
    """
    Include agents in scheduling, meaning that the given agents
    will be considered to be ready for creating new session containers.
    """
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            _ = session.Manager.scheduler_op("include-agents", agent_ids)
        print_done("The given agents now accepts new sessions.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@scheduler.command()
@click.argument("agent_ids", nargs=-1)
def exclude_agents(agent_ids: tuple[str, ...]) -> None:
    """
    Exclude agents from scheduling, meaning that the given agents
    will no longer start new sessions unless they are "included" again,
    regardless of their restarts and rejoining events.
    """
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            _ = session.Manager.scheduler_op("exclude-agents", agent_ids)
        print_done("The given agents will no longer start new sessions.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)
