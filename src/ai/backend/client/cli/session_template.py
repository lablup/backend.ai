import sys

import click
from tabulate import tabulate

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode

from ..session import Session
from .pretty import print_error, print_info, print_warn


@main.group(aliases=["sesstpl"])
def session_template():
    """Set of session template operations"""


@session_template.command()
@click.option(
    "-f",
    "--file",
    "template_path",
    help=(
        "Path to task template file. If not specified, client will try to read config from STDIN. "
    ),
)
@click.option(
    "-d",
    "--domain",
    metavar="DOMAIN_NAME",
    default=None,
    help=(
        "Domain name where the session will be spawned. "
        "If not specified, config's domain name will be used."
    ),
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP_NAME",
    default=None,
    help=(
        "Group name where the session is spawned. "
        "User should be a member of the group to execute the code."
    ),
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Set the owner of the target session explicitly.",
)
def create(template_path, domain, group, owner_access_key):
    """
    Store task template to Backend.AI Manager and return template ID.
    Template can be used when creating new session.
    """

    if template_path:
        with open(template_path, "r") as fr:
            body = fr.read()
    else:
        body = ""
        for line in sys.stdin:
            body += line + "\n"
    with Session() as session:
        try:
            # TODO: Make user select template type when cluster template is implemented
            template = session.SessionTemplate.create(
                body, domain_name=domain, group_name=group, owner_access_key=owner_access_key
            )
            print_info(f"Task template {template.template_id} created and ready")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session_template.command()
@click.argument("template_id", metavar="TEMPLATEID")
@click.option(
    "-f",
    "--format",
    "template_format",
    default="yaml",
    help='Output format for task template. "yaml" and "json" allowed.',
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session explicitly.",
)
def get(template_id, template_format, owner_access_key):
    """
    Print task template associated with given template ID
    """
    with Session() as session:
        try:
            template = session.SessionTemplate(template_id, owner_access_key=owner_access_key)
            body = template.get(body_format=template_format)
            print(body)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session_template.command()
@click.option(
    "-a",
    "--list-all",
    is_flag=True,
    help="List all virtual folders (superadmin privilege is required).",
)
def list(list_all):
    """
    List all available task templates by user.
    """
    fields = [
        ("Name", "name"),
        ("ID", "id"),
        ("Created At", "created_at"),
        ("Owner", "is_owner"),
        ("Type", "type"),
        ("User", "user"),
        ("Group", "group"),
    ]
    with Session() as session:
        try:
            resp = session.SessionTemplate.list_templates(list_all)
            if not resp:
                print("There is no task templates created yet.")
                return
            rows = (tuple(vf[key] for _, key in fields) for vf in resp)
            hdrs = (display_name for display_name, _ in fields)
            print(tabulate(rows, hdrs))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session_template.command()
@click.argument("template_id", metavar="TEMPLATEID")
@click.option(
    "-f",
    "--file",
    "template_path",
    help=(
        "Path to task template file. If not specified, client will try to read config from STDIN. "
    ),
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session explicitly.",
)
def update(template_id, template_path, owner_access_key):
    """
    Update task template stored in Backend.AI Manager.
    """

    if template_path:
        with open(template_path, "r") as fr:
            body = fr.read()
    else:
        body = ""
        for line in sys.stdin:
            body += line + "\n"
    with Session() as session:
        try:
            template = session.SessionTemplate(template_id, owner_access_key=owner_access_key)
            template.put(body)
            print_info(f"Task template {template.template_id} updated")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session_template.command()
@click.argument("template_id", metavar="TEMPLATEID")
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="If specified, delete task template without asking.",
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session explicitly.",
)
def delete(template_id, force, owner_access_key):
    """
    Delete task template from Backend.AI Manager.
    """
    with Session() as session:
        template = session.SessionTemplate(template_id, owner_access_key=owner_access_key)
        if not force:
            print_warn("Are you sure? (y/[n])")
            result = input()
            if result.strip() != "y":
                print_info("Aborting.")
                exit()
        try:
            template.delete()
            print_info(f"Task template {template.template_id} deleted")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
