import sys
import uuid

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from ...output.fields import group_fields, quota_scope_fields, user_fields
from ..pretty import print_error, print_fail
from . import admin

_user_query_fields = (
    user_fields["uuid"],
    user_fields["username"],
)
_project_query_fields = (
    group_fields["id"],
    group_fields["name"],
)


@admin.group()
def quota_scope():
    """Quota scope administration commands."""


def _get_qsid_from_identifier(type: str, domain_name: str, identifier: str, session: Session):
    match type:
        case "user":
            try:
                user_id = uuid.UUID(identifier)
            except ValueError:
                # In case identifier is the user email
                user_info = session.QuotaScope.get_user_qsid(
                    domain_name=domain_name,
                    email=identifier,
                    fields=_user_query_fields,
                )
                if user_info is None:
                    return None
                user_qsid = f"user:{user_info['uuid']}"
            else:
                # In case identifier is the user ID
                user_qsid = f"user:{user_id}"
            return user_qsid

        case "project":
            try:
                project_id = uuid.UUID(identifier)
            except ValueError:
                # In case identifier is the project name
                project_info = session.QuotaScope.get_project_qsid(
                    domain_name=domain_name,
                    name=identifier,
                    fields=_project_query_fields,
                )
                if project_info is None:
                    return None
                project_qsid = f"project:{project_info['id']}"
            else:
                # In case identifier is the project ID
                project_qsid = f"project:{project_id}"
            return project_qsid


@quota_scope.command()
@click.argument("host", type=str)
@click.argument("domain_name", type=str)
@click.argument("identifier", type=str)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["user", "project"]),
    default="user",
    help="Specify per-user quota scope or per-project quota scope",
)
def get(host, domain_name, identifier, type):
    """Get a quota scope.

    \b
    HOST: Name of the host to get quota scope.
    DOMAIN_NAME: Domain name of user or project.
    IDENTIFIER: ID or email for user, ID or name for project.
    """
    qs_query_fields = (
        quota_scope_fields["usage_bytes"],
        quota_scope_fields["usage_count"],
        quota_scope_fields["hard_limit_bytes"],
    )
    with Session() as session:
        try:
            qsid = _get_qsid_from_identifier(
                type=type,
                domain_name=domain_name,
                identifier=identifier,
                session=session,
            )
            if qsid is None:
                print_fail("Identifier is not valid")
                sys.exit(ExitCode.INVALID_ARGUMENT)
            result = session.QuotaScope.get_quota_scope(
                host=host,
                qsid=qsid,
                fields=qs_query_fields,
            )

            print(f"Used {result['usage_bytes']} bytes out of {result['hard_limit_bytes']} bytes.")

        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@quota_scope.command()
@click.argument("host", type=str)
@click.argument("domain_name", type=str)
@click.argument("identifier", type=str)
@click.argument("limit_bytes", type=int)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["user", "project"]),
    default="user",
    help="Specify per-user quota scope or per-project quota scope",
)
def set(host, domain_name, identifier, limit_bytes, type):
    """Set a quota scope.

    \b
    HOST: Name of the host to set quota scope.
    DOMAIN_NAME: Domain name of user or project.
    IDENTIFIER: ID or email for user, ID or name for project.
    LIMIT_BYTES: Size to be allocated to quota scope of a user or project. (in bytes)
    """
    with Session() as session:
        try:
            qsid = _get_qsid_from_identifier(
                type=type,
                domain_name=domain_name,
                identifier=identifier,
                session=session,
            )
            if qsid is None:
                print_fail("Identifier is not valid")
                sys.exit(ExitCode.INVALID_ARGUMENT)
            session.QuotaScope.set_quota_scope(
                host=host,
                qsid=qsid,
                hard_limit_bytes=limit_bytes,
            )

        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@quota_scope.command()
@click.argument("host", type=str)
@click.argument("domain_name", type=str)
@click.argument("identifier", type=str)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["user", "project"]),
    default="user",
    help="Specify per-user quota scope or per-project quota scope",
)
def unset(host, domain_name, identifier, type):
    """Unset a quota scope.

    \b
    HOST: Name of the host to unset quota scope.
    DOMAIN_NAME: Domain name of user or project.
    IDENTIFIER: ID or email for user, ID or name for project.
    """
    with Session() as session:
        try:
            qsid = _get_qsid_from_identifier(
                type=type,
                domain_name=domain_name,
                identifier=identifier,
                session=session,
            )
            if qsid is None:
                print_fail("Identifier is not valid")
                sys.exit(ExitCode.INVALID_ARGUMENT)
            session.QuotaScope.unset_quota_scope(
                host=host,
                qsid=qsid,
            )

        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
