import sys
from typing import List

import click

from ai.backend.client.session import Session

from .main import main
from .pretty import print_error


@main.group()
def filebrowser():
    """Set of filebrowser operations"""


@filebrowser.command()
@click.option(
    "-host",
    "--Host",
    help="Host:Volume reference for a filebrowser session.",
    type=str,
    metavar="HOST",
    multiple=False,
)
@click.option(
    "-vf",
    "--vfolders",
    help="Vfolder to be attached for a filebrowser session.",
    type=str,
    metavar="VFOLDERS",
    multiple=True,
)
def create(host: str, vfolders: List[str]) -> None:
    """Create or update filebrowser session"""
    print(host, vfolders)
    vfolder = list(vfolders)

    with Session() as session:
        try:
            session.FileBrowser.create_or_update_browser(host, vfolder)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@filebrowser.command()
@click.option(
    "-cid",
    "--container_id",
    help="Container ID of user filebrowser session.",
    type=str,
    metavar="CID",
)
def destroy(container_id: str) -> None:
    """Destroy filebrowser session using Container ID."""
    with Session() as session:
        try:
            session.FileBrowser.destroy_browser(container_id)
        except Exception as e:
            print_error(e)
            sys.exit(1)
