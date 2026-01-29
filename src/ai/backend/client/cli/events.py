from __future__ import annotations

import enum
import json
import sys
from typing import Optional
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.compat import asyncio_run
from ai.backend.client.session import AsyncSession

from .extensions import pass_ctx_obj
from .pretty import print_error
from .types import CLIContext


class SubscribableEvents(enum.StrEnum):
    KERNEL_CANCELLED = "kernel_cancelled"
    KERNEL_CREATING = "kernel_creating"
    KERNEL_STARTED = "kernel_started"
    KERNEL_TERMINATED = "kernel_terminated"
    KERNEL_TERMINATING = "kernel_terminating"
    SESSION_FAILURE = "session_failure"
    SESSION_STARTED = "session_started"
    SESSION_SUCCESS = "session_success"
    SESSION_TERMINATED = "session_terminated"

    # Virtual event representing either success or failure for batch sessions
    BATCH_SESSION_RESULT = "batch_session_result"


@click.group()
def events() -> None:
    """Set of event streaming operations"""


@events.command()
@pass_ctx_obj
@click.option(
    "--session-name",
    "-s",
    metavar="SESSION_NAME",
    default="*",
    help="Session name to filter events. Use '*' for all sessions (default).",
)
@click.option(
    "--session-id",
    "-i",
    metavar="SESSION_ID",
    type=click.UUID,
    default=None,
    help="Session ID to filter events. If provided, overrides session-name.",
)
@click.option(
    "--owner-access-key",
    "-o",
    metavar="ACCESS_KEY",
    default=None,
    help="Access key of the session owner.",
)
@click.option(
    "--group-name",
    "-g",
    metavar="GROUP_NAME",
    default="*",
    help="Group name to filter events. Use '*' for all groups (default).",
)
@click.option(
    "--scope",
    metavar="SCOPE",
    default="*",
    help="Event scope: 'session', 'kernel', or 'session,kernel' (default: '*' includes both).",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress output except for event data.",
)
@click.option(
    "--wait",
    "-w",
    metavar="EVENT",
    type=click.Choice([*SubscribableEvents], case_sensitive=False),
    default=None,
    help="Wait until the specified event is received and exit.",
)
def listen_session(
    ctx: CLIContext,
    session_name: str,
    session_id: Optional[UUID],
    owner_access_key: Optional[str],
    group_name: str,
    scope: str,
    quiet: bool,
    wait: Optional[str],
) -> None:
    """
    Listen to session and kernel lifecycle events.

    This command streams real-time events for sessions and their kernels,
    providing updates about status changes and lifecycle transitions.

    \b
    Examples:
        # Listen to all session events
        backend.ai events listen-session

        # Listen to events for a specific session
        backend.ai events listen-session --session-name my-session

        # Listen to events for a specific session ID
        backend.ai events listen-session --session-id 12345678-1234-1234-1234-123456789012

        # Listen to kernel events only
        backend.ai events listen-session --scope kernel

        # Wait until session completes (for batch sessions)
        backend.ai events listen-session --session-name batch-job --wait batch_session_result
    """

    def print_event(ev):
        if ev.event:
            click.echo(
                click.style(ev.event, fg="cyan", bold=True)
                + ": "
                + json.dumps(json.loads(ev.data), indent=None)
            )
        else:
            click.echo(json.dumps(json.loads(ev.data), indent=None))

    async def _run_events():
        async with AsyncSession() as session:
            async with session.Events.listen_session_events(
                session_name=session_name,
                session_id=session_id,
                owner_access_key=owner_access_key,
                group_name=group_name,
                scope=scope,
            ) as response:
                if not quiet:
                    click.echo(f"Listening to events (scope: {scope})...")
                async for ev in response:
                    if not quiet:
                        print_event(ev)
                    else:
                        # In quiet mode, just output the data
                        click.echo(ev.data)

                    # Handle wait condition
                    if wait:
                        match wait:
                            case SubscribableEvents.BATCH_SESSION_RESULT:
                                # Stop at batch session completion
                                if ev.event == SubscribableEvents.SESSION_SUCCESS:
                                    sys.exit(0)
                                elif ev.event == SubscribableEvents.SESSION_FAILURE:
                                    sys.exit(1)
                            case ev.event:
                                # Stop at specific event
                                sys.exit(0)

    try:
        asyncio_run(_run_events())
    except KeyboardInterrupt:
        if not quiet:
            click.echo("\nStopped listening to events.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@events.command()
@pass_ctx_obj
@click.argument("task_id", metavar="TASK_ID", type=click.UUID)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress output except for event data.",
)
def listen_background_task(
    ctx: CLIContext,
    task_id: UUID,
    quiet: bool,
) -> None:
    """
    Listen to background task events.

    This command streams real-time events for a specific background task,
    providing updates about its progress and completion status.

    \b
    TASK_ID: The UUID of the background task to monitor.

    \b
    Examples:
        # Listen to background task events
        backend.ai events listen-background-task 12345678-1234-1234-1234-123456789012

        # Listen quietly (only output event data)
        backend.ai events listen-background-task 12345678-1234-1234-1234-123456789012 --quiet
    """

    def print_event(ev):
        if ev.event:
            click.echo(
                click.style(ev.event, fg="cyan", bold=True)
                + ": "
                + json.dumps(json.loads(ev.data), indent=None)
            )
        else:
            click.echo(json.dumps(json.loads(ev.data), indent=None))

    async def _run_events():
        async with AsyncSession() as session:
            if not quiet:
                click.echo(f"Listening to background task events (task_id: {task_id})...")
            async with session.Events.listen_background_task_events(task_id) as response:
                async for ev in response:
                    if not quiet:
                        print_event(ev)
                    else:
                        # In quiet mode, just output the data
                        click.echo(ev.data)

                    # Auto-exit on close event
                    if ev.event == "server_close":
                        break

    try:
        asyncio_run(_run_events())
        if not quiet:
            click.echo("Background task completed.")
    except KeyboardInterrupt:
        if not quiet:
            click.echo("\nStopped listening to events.")
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)
