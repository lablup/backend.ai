from __future__ import annotations

import functools
import pathlib
from collections.abc import Callable, Sequence
from typing import Any

import click
import tomli
import tomlkit

from .migrator import ConfigMigrator
from .types import MappingRule


def sd_migration_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Common Click options for the ``service-discovery`` migration command."""

    @click.option(
        "-i",
        "--input",
        "input_path",
        required=True,
        type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
        help="Path to the existing TOML configuration file.",
    )
    @click.option(
        "-o",
        "--output",
        "output_path",
        type=click.Path(dir_okay=False, writable=True, path_type=pathlib.Path),
        default=None,
        help="Output file path. If omitted, prints to stdout.",
    )
    @click.option(
        "--append",
        is_flag=True,
        default=False,
        help="Append the generated section directly to the input file.",
    )
    @click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Preview the migration result without writing any files.",
    )
    @click.option(
        "--force",
        is_flag=True,
        default=False,
        help="Proceed even if service-discovery endpoints already exist.",
    )
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def run_sd_migration(
    *,
    input_path: pathlib.Path,
    output_path: pathlib.Path | None,
    append: bool,
    dry_run: bool,
    force: bool,
    component_name: str,
    mapping_rules: Sequence[MappingRule],
) -> None:
    """Execute the service-discovery config migration."""
    with input_path.open("rb") as f:
        config = tomli.load(f)

    migrator = ConfigMigrator(mapping_rules)

    if migrator.check_existing_endpoints(config) and not force:
        click.echo(
            f"Warning: [{component_name}] service-discovery.endpoints already exist "
            f"in {input_path}. Use --force to overwrite.",
            err=True,
        )
        raise SystemExit(1)

    result = migrator.migrate(config)

    if not result.generated_endpoints:
        click.echo(
            f"No address/port fields detected for {component_name}. Nothing to migrate.",
            err=True,
        )
        return

    if dry_run:
        click.echo(migrator.format_dry_run_output(result))
        return

    if append:
        with input_path.open() as f:
            doc = tomlkit.load(f)
        migrator.append_to_document(doc, result)
        with input_path.open("w") as f:
            tomlkit.dump(doc, f)
        click.echo(f"Appended service-discovery endpoints to {input_path}")
        return

    toml_output = migrator.generate_toml_section(result)
    if output_path is not None:
        output_path.write_text(toml_output)
        click.echo(f"Wrote service-discovery endpoints to {output_path}")
    else:
        click.echo(toml_output)
