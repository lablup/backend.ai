"""``backend.ai v2 config`` CLI commands for managing ``~/.backend.ai/`` settings."""

from __future__ import annotations

from typing import Any

import click

from .helpers import CONFIG_DIR, CONFIG_FILE

CONFIGURABLE_KEYS = {
    "endpoint": "endpoint",
    "endpoint-type": "endpoint_type",
    "api-version": "api_version",
    "skip-ssl-verification": "skip_ssl_verification",
}


def _load_toml(path: click.Path) -> dict[str, Any]:
    """Load a TOML file, returning empty dict if missing."""
    import tomllib
    from pathlib import Path as P

    p = P(str(path))
    if not p.exists():
        return {}
    with p.open("rb") as f:
        return tomllib.load(f)


def _save_toml(path: click.Path, data: dict[str, Any]) -> None:
    """Write a dict to a TOML file under the ``[backend-ai]`` section."""
    from pathlib import Path as P

    import tomli_w

    p = P(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("wb") as f:
        tomli_w.dump(data, f)


@click.group()
def config() -> None:
    """Manage v2 CLI configuration stored in ~/.backend.ai/."""


@config.command()
def show() -> None:
    """Display the current v2 configuration."""
    from .helpers import load_v2_config

    cfg = load_v2_config()
    click.echo(f"Endpoint:             {click.style(str(cfg.endpoint), bold=True)}")
    click.echo(f"Endpoint type:        {click.style(cfg.endpoint_type, bold=True)}")
    click.echo(f"API version:          {click.style(cfg.api_version, bold=True)}")
    click.echo(f"Skip SSL:             {click.style(str(cfg.skip_ssl_verification), bold=True)}")
    if cfg.access_key:
        click.echo(f"Access key:           {click.style(cfg.access_key, bold=True)}")
    else:
        click.echo("Access key:           (not set)")
    if cfg.secret_key:
        masked = cfg.secret_key[:6] + "****" + cfg.secret_key[-4:]
        click.echo(f"Secret key:           {click.style(masked, bold=True)}")
    else:
        click.echo("Secret key:           (not set)")
    click.echo(f"Config dir:           {CONFIG_DIR}")


@config.command("set")
@click.argument("key", type=click.Choice(list(CONFIGURABLE_KEYS.keys())))
@click.argument("value")
def set_value(key: str, value: str) -> None:
    """Set a configuration value.

    KEY is one of: endpoint, endpoint-type, api-version, skip-ssl-verification.
    """
    toml_key = CONFIGURABLE_KEYS[key]

    data = _load_toml(CONFIG_FILE)
    section = data.setdefault("backend-ai", {})

    if key == "skip-ssl-verification":
        section[toml_key] = value.lower() in ("true", "1", "yes")
    else:
        section[toml_key] = value

    _save_toml(CONFIG_FILE, data)
    click.echo(f"Set {key} = {value}")


@config.command("get")
@click.argument("key", type=click.Choice(list(CONFIGURABLE_KEYS.keys())))
def get_value(key: str) -> None:
    """Get a configuration value."""
    from .helpers import load_v2_config

    cfg = load_v2_config()
    field_map = {
        "endpoint": str(cfg.endpoint),
        "endpoint-type": cfg.endpoint_type,
        "api-version": cfg.api_version,
        "skip-ssl-verification": str(cfg.skip_ssl_verification),
    }
    click.echo(field_map[key])
