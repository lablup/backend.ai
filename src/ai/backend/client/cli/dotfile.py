import sys

import click
from tabulate import tabulate

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode

from ..session import Session
from .pretty import print_error, print_fail, print_info, print_warn


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
    "-j",
    "--project",
    metavar="PROJECT",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d)"
    ),
)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d). "
        "This option is deprecated, use `--project` option instead."
    ),
)
def create(path, permission, dotfile_path, owner_access_key, domain, project, group):
    """
    Store dotfile to Backend.AI Manager.
    Dotfiles will be automatically loaded when creating kernels.

    PATH: Where dotfiles will be created when starting kernel
    """

    if group:
        print_warn("`--group` option is deprecated. Use `--project` option instead.")
        if not project:
            project = group
        else:
            print_fail("Cannot use `--project` and `--group` options simultaneously.")
            sys.exit(ExitCode.FAILURE)

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
                project=project,
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
    "-p",
    "--project",
    metavar="PROJECT",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d)"
    ),
)
def get(path, owner_access_key, domain, project):
    """
    Print dotfile content.
    """
    with Session() as session:
        try:
            dotfile_ = session.Dotfile(
                path, owner_access_key=owner_access_key, domain=domain, project=project
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
    "-p",
    "--project",
    metavar="PROJECT",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d)"
    ),
)
def list(owner_access_key, domain, project):
    """
    List availabe user/domain/project dotfiles.
    """
    fields = [
        ("Path", "path", None),
        ("Data", "data", lambda v: v[:30].splitlines()[0]),
        ("Permission", "permission", None),
    ]
    with Session() as session:
        try:
            resp = session.Dotfile.list_dotfiles(
                owner_access_key=owner_access_key, domain=domain, project=project
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
    "-p",
    "--project",
    metavar="RPOJECT",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d)"
    ),
)
def update(path, permission, dotfile_path, owner_access_key, domain, project):
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
                path, owner_access_key=owner_access_key, domain=domain, project=project
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
    "-p",
    "--project",
    metavar="PROJECT",
    help=(
        "Sepcify the project name or id of project dotfiles. "
        "(If project name is provided, domain name must be specified with option -d)"
    ),
)
def delete(path, force, owner_access_key, domain, project):
    """
    Delete dotfile from Backend.AI Manager.
    """
    with Session() as session:
        dotfile_ = session.Dotfile(
            path, owner_access_key=owner_access_key, domain=domain, project=project
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
