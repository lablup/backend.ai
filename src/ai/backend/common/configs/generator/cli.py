"""The ``config render`` command every component's config CLI group adds."""

from __future__ import annotations

import pathlib
import tomllib

import click
import jinja2

from .template import render_config_template

__all__ = ("render",)


def _parse_args(
    _ctx: click.Context, _param: click.Parameter, values: tuple[str, ...]
) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        name, sep, arg = value.partition("=")
        if not sep or not name:
            raise click.BadParameter(f"'{value}' is not NAME=VALUE")
        parsed[name] = arg
    return parsed


@click.command()
@click.option(
    "-t",
    "--template",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Sample template made by `config generate-sample` (e.g., sample.toml.j2).",
)
@click.option(
    "-a",
    "--arg",
    "args",
    multiple=True,
    metavar="NAME=VALUE",
    callback=_parse_args,
    help="Value of a template argument, such as volume_name=local. Repeat for each.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=pathlib.Path),
    required=True,
    help="Path of the configuration file to write.",
)
@click.option("--overwrite", is_flag=True, help="Overwrite the output file if it exists.")
def render(
    template: pathlib.Path,
    args: dict[str, str],
    output: pathlib.Path,
    overwrite: bool,
) -> None:
    """Fill a sample template's arguments and write the configuration file."""
    if output.exists() and not overwrite:
        raise click.ClickException(
            f"Output file '{output}' already exists. Use --overwrite to replace it."
        )
    try:
        rendered = render_config_template(template.read_text(encoding="utf-8"), args)
    except (jinja2.UndefinedError, tomllib.TOMLDecodeError) as e:
        raise click.ClickException(f"Cannot render '{template}': {e}") from e
    output.write_text(rendered, encoding="utf-8")
    click.echo(f"Configuration written to {output}")
