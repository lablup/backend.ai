from __future__ import annotations

import sys
import uuid
from typing import Any, Dict, List

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.output.fields import session_fields, session_fields_v5
from ai.backend.client.output.types import FieldSpec
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..pretty import print_fail
from ..session.lifecycle import session as user_session
from ..types import CLIContext
from . import admin

SessionItem = Dict[str, Any]


@admin.group()
def session() -> None:
    """
    Session administration commands.
    """


def _list_cmd(name: str = "list", docs: str = None):
    @pass_ctx_obj
    @click.option(
        "-s",
        "--status",
        default=None,
        type=click.Choice([
            "PENDING",
            "SCHEDULED",
            "PULLING",
            "PREPARING",
            "RUNNING",
            "RESTARTING",
            "RUNNING_DEGRADED",
            "TERMINATING",
            "TERMINATED",
            "ERROR",
            "CANCELLED",
            "ALL",  # special case
        ]),
        help="Filter by the given status",
    )
    @click.option(
        "--access-key",
        type=str,
        default=None,
        help="Get sessions for a specific access key (only works if you are a super-admin)",
    )
    @click.option("--name-only", is_flag=True, help="Display session names only.")
    @click.option(
        "--dead", is_flag=True, help="Filter only dead sessions. Ignores --status option."
    )
    @click.option(
        "--running",
        is_flag=True,
        help="Filter only scheduled and running sessions. Ignores --status option.",
    )
    @click.option("--detail", is_flag=True, help="Show more details using more columns.")
    @click.option("-f", "--format", default=None, help="Display only specified fields.")
    @click.option(
        "--plain",
        is_flag=True,
        help="Display the session list without decorative line drawings and the header.",
    )
    @click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
    @click.option("--order", default=None, help="Set the query ordering expression.")
    @click.option(
        "--offset", default=0, type=int, help="The index of the current page start for pagination."
    )
    @click.option("--limit", default=None, type=int, help="The page size for pagination.")
    @click.option(
        "-a",
        "--all",
        is_flag=True,
        default=False,
        help=(
            'Alias of "backend.ai ps --status=ALL" listing all sessions regardless of status.'
            " Ignores --status option."
        ),
    )
    def list(
        ctx: CLIContext,
        status: str | None,
        access_key: str | None,
        name_only: str | None,
        dead: bool,
        running: bool,
        detail: bool,
        format: str | None,
        plain: bool,
        filter_: str | None,
        order: str | None,
        offset: int,
        limit: int | None,
        all: bool,
    ) -> None:
        """
        List and manage compute sessions.
        """
        fields: List[FieldSpec] = []
        with Session() as session:
            is_admin = session.KeyPair(session.config.access_key).info()["is_admin"]
            try:
                fields.append(session_fields["name"])
                if is_admin:
                    fields.append(session_fields["access_key"])
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)
            if name_only:
                pass
            elif format is not None:
                options = format.split(",")
                for opt in options:
                    if opt not in session_fields or opt == "containers":
                        ctx.output.print_fail(f"There is no such format option: {opt}")
                        sys.exit(ExitCode.INVALID_ARGUMENT)
                fields = [session_fields[opt] for opt in options]
            else:
                if session.api_version[0] >= 6:
                    fields.append(session_fields["session_id"])
                fields.extend([
                    session_fields["group_name"],
                    session_fields["main_kernel_id"],
                    session_fields["image"],
                    session_fields["type"],
                    session_fields["status"],
                    session_fields["status_info"],
                    session_fields["status_changed"],
                    session_fields["result"],
                ])
                if detail:
                    fields.extend([
                        session_fields["tag"],
                        session_fields["created_at"],
                        session_fields["occupying_slots"],
                    ])

        no_match_name = None
        if status is None:
            status = ",".join([
                "PENDING",
                "SCHEDULED",
                "PULLING",
                "PREPARING",
                "RUNNING",
                "RUNNING_DEGRADED",
                "TERMINATING",
                "ERROR",
            ])
            no_match_name = "active"
        if running:
            status = ",".join([
                "PREPARING",
                "RUNNING",
                "RUNNING_DEGRADED",
            ])
            no_match_name = "running"
        if dead:
            status = ",".join([
                "CANCELLED",
                "TERMINATED",
            ])
            no_match_name = "dead"
        if status == "ALL" or all:
            status = ",".join([
                "PENDING",
                "SCHEDULED",
                "PULLING",
                "PREPARING",
                "RUNNING",
                "RESTARTING",
                "RUNNING_DEGRADED",
                "TERMINATING",
                "TERMINATED",
                "ERROR",
                "CANCELLED",
            ])
            no_match_name = "in any status"
        if no_match_name is None:
            no_match_name = status.lower()

        try:
            with Session() as session:
                fetch_func = lambda pg_offset, pg_size: session.ComputeSession.paginated_list(
                    status,
                    access_key,
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
                    plain=plain,
                )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)

    list.__name__ = name
    if docs is not None:
        list.__doc__ = docs
    return list


# Make it available as:
# - backend.ai ps
# - backend.ai admin session list
main.command()(_list_cmd(name="ps", docs='Alias of "session list"'))
user_session.command()(_list_cmd(docs='Alias of "admin session list"'))
session.command()(_list_cmd())


def _info_cmd(docs: str = None):
    @pass_ctx_obj
    @click.argument("session_id", metavar="SESSID")
    def info(ctx: CLIContext, session_id: str) -> None:
        """
        Show detailed information for a running compute session.
        """
        with Session() as session_:
            fields = [
                session_fields["name"],
            ]
            if session_.api_version[0] >= 6:
                fields.append(session_fields["session_id"])
                fields.append(session_fields["main_kernel_id"])
            fields.extend([
                session_fields["image"],
                session_fields["tag"],
                session_fields["created_at"],
                session_fields["terminated_at"],
                session_fields["status"],
                session_fields["status_info"],
                session_fields["status_data"],
                session_fields["occupying_slots"],
                session_fields["idle_checks"],
            ])
            if session_.api_version[0] >= 6:
                fields.append(session_fields["containers"])
            else:
                fields.append(session_fields_v5["containers"])
            fields.append(session_fields["dependencies"])
            q = "query($id: UUID!) {  compute_session(id: $id) {    $fields  }}"
            try:
                uuid.UUID(session_id)
            except ValueError:
                print_fail("In API v5 or later, the session ID must be given in the UUID format.")
                sys.exit(ExitCode.FAILURE)
            v = {"id": session_id}
            q = q.replace("$fields", " ".join(f.field_ref for f in fields))
            try:
                resp = session_.Admin.query(q, v)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)
            if resp["compute_session"] is None:
                if session_.api_version[0] < 5:
                    ctx.output.print_fail("There is no such running compute session.")
                else:
                    ctx.output.print_fail("There is no such compute session.")
                sys.exit(ExitCode.FAILURE)
            ctx.output.print_item(resp["compute_session"], fields)

    if docs is not None:
        info.__doc__ = docs
    return info


main.command()(_info_cmd(docs='Alias of "session info"'))
user_session.command()(_info_cmd(docs='Alias of "admin session info"'))
session.command()(_info_cmd())
