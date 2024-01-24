import sys

import click
import uuid

from ai.backend.client.session import Session
from ai.backend.cli.types import ExitCode

from . import admin
from ..pretty import print_error
from ...output.fields import quota_scope_fields, user_fields, group_fields


@admin.group()
def quota_scope():
    """Quota scope administration commands."""


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
    user_query_fields = (
        user_fields["uuid"],
        user_fields["username"],
    )
    project_query_fields = (
        group_fields["id"],
        group_fields["name"],
    )
    qs_query_fields = (
        quota_scope_fields["usage_bytes"],
        quota_scope_fields["usage_count"],
        quota_scope_fields["hard_limit_bytes"]
    )
    with Session() as session:
        try:
            match type:
                case "user":
                    try:
                        user_id = uuid.UUID(identifier)
                    except ValueError:
                        # In case the user has entered the user email
                        user_info = session.QuotaScope.get_user_qsid(
                            domain_name=domain_name,
                            email=identifier,
                            fields=user_query_fields,
                        )
                        user_qsid = f"user:{user_info['uuid']}"
                    else:
                        # In case the user has entered the user ID
                        user_qsid = f"user:{user_id}"
                    finally:
                        result = session.QuotaScope.get_quota_scope(
                            host=host,
                            qsid=user_qsid,
                            fields=qs_query_fields,
                        )

                case "project":
                    try:
                        project_id = uuid.UUID(identifier)
                    except ValueError:
                        # In case the user has entered the project name
                        project_info = session.QuotaScope.get_project_qsid(
                            domain_name=domain_name,
                            name=identifier,
                            fields=project_query_fields,
                        )
                        project_qsid = f"project:{project_info['id']}"
                    else:
                        # In case the user has entered the project ID
                        project_qsid = f"project:{project_id}"
                    finally:
                        result = session.QuotaScope.get_quota_scope(
                            host=host,
                            qsid=project_qsid,
                            fields=qs_query_fields,
                        )

            print(f"Used {result['usage_bytes']} bytes out of {result['hard_limit_bytes']} bytes.")

        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
