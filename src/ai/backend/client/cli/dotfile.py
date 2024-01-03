import sys

import click
from tabulate import tabulate

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode

from ..session import Session
from .pretty import print_error, print_info, print_warn


@main.group()
def dotfile():
    """Provides dotfile operations."""


@dotfile.command()
@click.argument("path", metavar="PATH")
@click.option(
    "--perm",
    "permission",
    help="Linux permission represented in octal number (e.g. 755) Defaults to 755 if not specified",
)
@click.option(
    "-f",
    "--file",
    "dotfile_path",
    help="Path to dotfile to upload. If not specified, client will try to read file from STDIN. ",
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session of user dotfiles.",
)
@click.option(
    "-d", "--domain", "domain", metavar="DOMAIN", help="Specify the domain name of domain dotfiles."
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Specify the group name or id of group dotfiles. "
        "(If group name is provided, domain name must be specified with option -d)"
    ),
)
def create(path, permission, dotfile_path, owner_access_key, domain, group):
    """
    Store dotfile to Backend.AI Manager.
    Dotfiles will be automatically loaded when creating kernels.

    PATH: Where dotfiles will be created when starting kernel
    """

    if dotfile_path:
        with open(dotfile_path, "r") as fr:
            body = fr.read()
    else:
        body = ""
        for line in sys.stdin:
            body += line + "\n"
    with Session() as session:
        try:
            if not permission:
                permission = "755"
            dotfile_ = session.Dotfile.create(
                body,
                path,
                permission,
                owner_access_key=owner_access_key,
                domain=domain,
                group=group,
            )
            print_info(f"Dotfile {dotfile_.path} created and ready")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@dotfile.command()
@click.argument("path", metavar="PATH")
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session of user dotfiles.",
)
@click.option(
    "-d", "--domain", "domain", metavar="DOMAIN", help="Specify the domain name of domain dotfiles."
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Specify the group name or id of group dotfiles. "
        "(If group name is provided, domain name must be specified with option -d)"
    ),
)
def get(path, owner_access_key, domain, group):
    """
    Print dotfile content.
    """
    with Session() as session:
        try:
            dotfile_ = session.Dotfile(
                path, owner_access_key=owner_access_key, domain=domain, group=group
            )
            body = dotfile_.get()
            print(body["data"])
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@dotfile.command()
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session of user dotfiles.",
)
@click.option(
    "-d", "--domain", "domain", metavar="DOMAIN", help="Specify the domain name of domain dotfiles."
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Specify the group name or id of group dotfiles. "
        "(If group name is provided, domain name must be specified with option -d)"
    ),
)
def list(owner_access_key, domain, group):
    """
    List available user/domain/group dotfiles.
    """
    fields = [
        ("Path", "path", None),
        ("Data", "data", lambda v: v[:30].splitlines()[0]),
        ("Permission", "permission", None),
    ]
    with Session() as session:
        try:
            resp = session.Dotfile.list_dotfiles(
                owner_access_key=owner_access_key, domain=domain, group=group
            )
            if not resp:
                print("There is no dotfiles created yet.")
                return
            rows = (
                tuple(
                    item[key] if transform is None else transform(item[key])
                    for _, key, transform in fields
                )
                for item in resp
            )
            hdrs = (display_name for display_name, _, _ in fields)
            print(tabulate(rows, hdrs))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@dotfile.command()
@click.argument("path", metavar="PATH")
@click.option(
    "--perm",
    "permission",
    help="Linux permission represented in octal number (e.g. 755) Defaults to 755 if not specified",
)
@click.option(
    "-f",
    "--file",
    "dotfile_path",
    help="Path to dotfile to upload. If not specified, client will try to read file from STDIN. ",
)
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session of user dotfiles.",
)
@click.option(
    "-d", "--domain", "domain", metavar="DOMAIN", help="Specify the domain name of domain dotfiles."
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Specify the group name or id of group dotfiles. "
        "(If group name is provided, domain name must be specified with option -d)"
    ),
)
def update(path, permission, dotfile_path, owner_access_key, domain, group):
    """
    Update dotfile stored in Backend.AI Manager.
    """

    if dotfile_path:
        with open(dotfile_path, "r") as fr:
            body = fr.read()
    else:
        body = ""
        for line in sys.stdin:
            body += line + "\n"
    with Session() as session:
        try:
            if not permission:
                permission = "755"
            dotfile_ = session.Dotfile(
                path, owner_access_key=owner_access_key, domain=domain, group=group
            )
            dotfile_.update(body, permission)
            print_info(f"Dotfile {dotfile_.path} updated")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@dotfile.command()
@click.argument("path", metavar="PATH")
@click.option("-f", "--force", is_flag=True, help="Delete dotfile without confirmation.")
@click.option(
    "-o",
    "--owner",
    "--owner-access-key",
    "owner_access_key",
    metavar="ACCESS_KEY",
    help="Specify the owner of the target session of user dotfiles.",
)
@click.option(
    "-d", "--domain", "domain", metavar="DOMAIN", help="Specify the domain name of domain dotfiles."
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Specify the group name or id of group dotfiles. "
        "(If group name is provided, domain name must be specified with option -d)"
    ),
)
def delete(path, force, owner_access_key, domain, group):
    """
    Delete dotfile from Backend.AI Manager.
    """
    with Session() as session:
        dotfile_ = session.Dotfile(
            path, owner_access_key=owner_access_key, domain=domain, group=group
        )
        if not force:
            print_warn("Are you sure? (y/[n])")
            result = input()
            if result.strip() != "y":
                print_info("Aborting.")
                exit()
        try:
            dotfile_.delete()
            print_info(f"Dotfile {dotfile_.path} deleted")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
