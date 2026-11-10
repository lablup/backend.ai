"""``backend.ai v2 profile`` CLI commands for managing ``~/.backend.ai/profiles/``."""

from __future__ import annotations

import shutil

import click

from .config_cmd import _save_toml
from .helpers import ProfilePaths, ProfileStore


def _echo_profile(paths: ProfilePaths) -> None:
    cfg = paths.read_config()
    click.echo(f"Profile:              {click.style(paths.name or '(default)', bold=True)}")
    click.echo(f"Endpoint:             {click.style(str(cfg['endpoint']), bold=True)}")
    click.echo(f"Endpoint type:        {click.style(str(cfg['endpoint_type']), bold=True)}")
    click.echo(f"API version:          {click.style(str(cfg['api_version']), bold=True)}")
    click.echo(f"Logged in:            {'yes' if paths.cookie_file.exists() else 'no'}")
    click.echo(f"Config dir:           {paths.base_dir}")


@click.group()
def profile() -> None:
    """Manage v2 CLI profiles (one endpoint, one account and its session each)."""


@profile.command()
@click.argument("name")
@click.option("--endpoint", default=None, help="Endpoint URL of the profile.")
@click.option(
    "--endpoint-type",
    type=click.Choice(["api", "session"]),
    default=None,
    help="Endpoint type of the profile.",
)
def create(name: str, endpoint: str | None, endpoint_type: str | None) -> None:
    """Create a profile."""
    paths = ProfileStore().paths(name)
    if paths.base_dir.exists():
        raise click.ClickException(f"Profile {name!r} already exists.")
    section: dict[str, str] = {}
    if endpoint is not None:
        section["endpoint"] = endpoint
    if endpoint_type is not None:
        section["endpoint_type"] = endpoint_type
    _save_toml(paths.config_file, {"backend-ai": section})
    click.echo(f"Created profile {name}")


@profile.command()
@click.argument("name")
def use(name: str) -> None:
    """Make NAME the current profile."""
    store = ProfileStore()
    store.existing(name)
    store.set_current(name)
    click.echo(f"Current profile: {name}")


@profile.command("list")
def list_profiles() -> None:
    """List profiles. The selected one is marked with ``*``."""
    store = ProfileStore()
    selected = store.selected_name()
    for name in store.names():
        marker = "*" if name == selected else " "
        endpoint = store.paths(name).read_config()["endpoint"]
        click.echo(f"{marker} {name}\t{endpoint}")


@profile.command()
@click.argument("name", required=False)
def show(name: str | None) -> None:
    """Show the settings of NAME, or of the selected profile."""
    store = ProfileStore()
    _echo_profile(store.existing(name) if name is not None else store.selected())


@profile.command()
@click.argument("name")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip the confirmation.")
def delete(name: str, yes: bool) -> None:
    """Delete a profile with its credentials and session."""
    store = ProfileStore()
    paths = store.existing(name)
    if not yes:
        click.confirm(f"Delete profile {name!r}?", abort=True)
    shutil.rmtree(paths.base_dir)
    if store.current() == name:
        store.set_current(None)
    click.echo(f"Deleted profile {name}")


@profile.command()
@click.argument("old")
@click.argument("new")
def rename(old: str, new: str) -> None:
    """Rename a profile."""
    store = ProfileStore()
    old_paths = store.existing(old)
    new_paths = store.paths(new)
    if new_paths.base_dir.exists():
        raise click.ClickException(f"Profile {new!r} already exists.")
    old_paths.base_dir.rename(new_paths.base_dir)
    if store.current() == old:
        store.set_current(new)
    click.echo(f"Renamed profile {old} to {new}")
