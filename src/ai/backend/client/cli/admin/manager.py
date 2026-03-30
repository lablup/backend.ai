import json
import sys
import time
from pathlib import Path

import appdirs
import click
from tabulate import tabulate

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.pretty import print_done, print_error, print_fail, print_info, print_wait

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


@admin.group()
def announcement() -> None:
    """Global announcement related commands"""


@announcement.command()
def get() -> None:
    """Get current announcement."""
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            result = session.Manager.get_announcement()
            if result.get("enabled", False):
                msg = result.get("message")
                print(msg)
            else:
                print("No announcements.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@announcement.command()
@click.option("-m", "--message", default=None, type=click.STRING)
def update(message: str | None) -> None:
    """
    Post new announcement.

    MESSAGE: Announcement message.
    """
    from ai.backend.client.cli.session.lifecycle import Session

    try:
        with Session() as session:
            if message is None:
                message = click.edit(
                    "<!-- Use Markdown format to edit the announcement message -->",
                )
            if message is None:
                print_info("Cancelled")
                sys.exit(ExitCode.FAILURE)
            _ = session.Manager.update_announcement(enabled=True, message=message)
        print_done("Posted new announcement.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@announcement.command()
def delete() -> None:
    """Delete current announcement."""
    from ai.backend.client.cli.session.lifecycle import Session

    if not ask_yn():
        print_info("Cancelled.")
        sys.exit(ExitCode.FAILURE)
    try:
        with Session() as session:
            _ = session.Manager.update_announcement(enabled=False)
        print_done("Deleted announcement.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@announcement.command()
def dismiss() -> None:
    """Do not show the same announcement again."""
    if not ask_yn():
        print_info("Cancelled.")
        sys.exit(ExitCode.FAILURE)
    try:
        local_state_path = Path(appdirs.user_state_dir("backend.ai", "Lablup"))
        announcement_path = local_state_path / "announcement.json"
        with announcement_path.open("rb") as f:
            state = json.load(f)
        state["dismissed"] = True
        with announcement_path.open("w") as f:
            json.dump(state, f)
        print_done("Dismissed the last shown announcement.")
    except (OSError, json.JSONDecodeError):
        print_fail("No announcements seen yet.")
        sys.exit(ExitCode.FAILURE)
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
