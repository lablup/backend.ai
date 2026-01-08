from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from . import __version__
from .types import Accelerator, CliArgs, InstallModes


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--mode",
    type=click.Choice([*InstallModes.__members__], case_sensitive=False),
    default=None,
    help="Override the installation mode. [default: auto-detect]",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Run the installer non-interactively from the given CLI options.",
)
@click.option(
    "--target-path",
    type=str,
    default=str(Path.home() / "backendai"),
    help="Explicitly set the target installation path. [default: ~/backendai]",
)
@click.option(
    "--show-guide",
    is_flag=True,
    default=False,
    help="Show the post-install guide using INSTALL-INFO if present.",
)
@click.option(
    "--accelerator",
    type=click.Choice([a.value for a in Accelerator], case_sensitive=False),
    default=None,
    show_default=True,
    help="Select accelerator plugin (cuda, cuda_mock, cuda_mig_mock, rocm_mock, none)",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run the installer as headless mode.",
)
@click.option(
    "--public-facing-address",
    type=str,
    default="127.0.0.1",
    help="Set public facing address for the Backend.AI server.",
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    cli_ctx: click.Context,
    mode: InstallModes | None,
    target_path: str,
    show_guide: bool,
    non_interactive: bool,
    headless: bool,
    public_facing_address: str,
    accelerator: str,
) -> None:
    """The installer"""
    from rich.console import Console

    from .app import InstallerApp

    # check sudo permission
    console = Console(stderr=True)
    if os.geteuid() == 0:
        console.print(
            "[bright_red] The script should not be run as root, while it requires"
            " the passwordless sudo privilege."
        )
        sys.exit(1)
    # start installer
    args = CliArgs(
        mode=mode,
        target_path=target_path,
        show_guide=show_guide,
        non_interactive=non_interactive,
        public_facing_address=public_facing_address,
        accelerator=accelerator,
    )
    app = InstallerApp(args)
    app.run(headless=headless)
