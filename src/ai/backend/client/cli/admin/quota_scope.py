import sys
import uuid

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session
from ai.backend.common.types import QuotaScopeID, QuotaScopeType

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


def _get_qsid_from_identifier(
    type_: QuotaScopeType,
    identifier: str,
    *,
    domain_name: str,
    session: Session,
) -> QuotaScopeID | None:
    match type_:
        case QuotaScopeType.USER:
            try:
                user_id = uuid.UUID(identifier)
            except ValueError:
                # In case identifier is the user email
                user_info = session.QuotaScope.get_user_info(
                    domain_name=domain_name,
                    email=identifier,
                    fields=_user_query_fields,
                )
                if user_info is None:
                    return None
                user_id = user_info["uuid"]
            else:
                # Use the user_id as-is if it's already a valid uuid.
                pass
            return QuotaScopeID(type_, user_id)
        case QuotaScopeType.PROJECT:
            try:
                project_id = uuid.UUID(identifier)
            except ValueError:
                # In case identifier is the project name
                project_info = session.QuotaScope.get_project_info(
                    domain_name=domain_name,
                    name=identifier,
                    fields=_project_query_fields,
                )
                if project_info is None:
                    return None
                project_id = project_info["id"]
            else:
                # Use the project_id as-is if it's already a valid uuid.
                pass
            return QuotaScopeID(type_, project_id)


@quota_scope.command()
@click.argument("host", type=str)
@click.argument("domain_name", type=str)
@click.argument("identifier", type=str)
@click.option(
    "-t",
    "--type",
    "type_",
    type=click.Choice([*QuotaScopeType], case_sensitive=False),
    default=QuotaScopeType.USER,
    help="Specify per-user quota scope or per-project quota scope",
)
def get(
    host: str,
    domain_name: str,
    identifier: str,
    type_: QuotaScopeType,
) -> None:
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
                type_,
                identifier,
                domain_name=domain_name,
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


@quota_scope.command(name="set")
@click.argument("host", type=str)
@click.argument("domain_name", type=str)
@click.argument("identifier", type=str)
@click.argument("limit_bytes", type=int)
@click.option(
    "-t",
    "--type",
    "type_",
    type=click.Choice([*QuotaScopeType], case_sensitive=False),
    default=QuotaScopeType.USER,
    help="Specify per-user quota scope or per-project quota scope",
)
def set_(
    host: str,
    domain_name: str,
    identifier: str,
    limit_bytes: int,
    type_: QuotaScopeType,
) -> None:
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
                type_,
                identifier,
                domain_name=domain_name,
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
    "type_",
    type=click.Choice([*QuotaScopeType], case_sensitive=False),
    default=QuotaScopeType.USER,
    help="Specify per-user quota scope or per-project quota scope",
)
def unset(
    host: str,
    domain_name: str,
    identifier: str,
    type_: QuotaScopeType,
) -> None:
    """Unset a quota scope.

    \b
    HOST: Name of the host to unset quota scope.
    DOMAIN_NAME: Domain name of user or project.
    IDENTIFIER: ID or email for user, ID or name for project.
    """
    with Session() as session:
        try:
            qsid = _get_qsid_from_identifier(
                type_,
                identifier,
                domain_name=domain_name,
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
