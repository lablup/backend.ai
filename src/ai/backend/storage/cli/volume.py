"""Volume management CLI commands for Backend.AI Storage Proxy."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from pathlib import Path

import click

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.loaders import load_local_config
from ai.backend.storage.config.unified import VolumeInfoConfig
from ai.backend.storage.volumes.health.types import MARKER_FILE_NAME

from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    """Volume management commands."""


def _mark_one(volume_name: str, mount_path: Path) -> tuple[bool, str]:
    """Writes the marker for one volume. Returns whether it succeeded, and why not."""
    marker_path = mount_path / MARKER_FILE_NAME
    try:
        declared = marker_path.read_text().strip()
    except FileNotFoundError:
        pass
    except OSError as e:
        return False, f"cannot read the existing marker: {e}"
    else:
        if declared == volume_name:
            return True, "already marked"
        return False, (
            f"the marker already declares {declared!r}; "
            "this path may be serving different storage than declared"
        )

    # Refuse to stamp the directory underneath a mount that has fallen off.
    try:
        mount_path.stat()
        os.statvfs(mount_path)
    except OSError as e:
        return False, f"the mount is not usable: {e}"

    try:
        marker_path.write_text(f"{volume_name}\n")
    except OSError as e:
        return False, f"cannot write the marker: {e}"
    return True, "marked"


@cli.command()
@click.argument("volume_name")
@click.pass_obj
def mark(cli_ctx: CLIContext, volume_name: str) -> None:
    """
    Write the volume marker that mount probes read to verify volume identity.

    An existing marker is never overwritten, and a volume whose mount is not usable is
    refused, so that the directory underneath a dropped mount is not stamped.
    """
    local_config = load_local_config(cli_ctx.config_path, log_level=cli_ctx.log_level)
    if volume_name not in local_config.volume:
        raise click.UsageError(f"No volume named {volume_name!r} in the configuration.")
    _report({volume_name: local_config.volume[volume_name]})


@cli.command(name="mark-all")
@click.pass_obj
def mark_all(cli_ctx: CLIContext) -> None:
    """Write the volume marker for every volume declared in the configuration file."""
    local_config = load_local_config(cli_ctx.config_path, log_level=cli_ctx.log_level)
    _report(dict(local_config.volume))


def _report(targets: Mapping[str, VolumeInfoConfig]) -> None:
    failed = False
    for name, volume_config in targets.items():
        succeeded, reason = _mark_one(name, Path(volume_config.path))
        if succeeded:
            click.echo(f"{name}: {reason}")
        else:
            failed = True
            click.echo(f"{name}: refused - {reason}", err=True)
    if failed:
        raise click.exceptions.Exit(1)
