"""Regression tests for `--output` being accepted at both the root and the subcommand level."""

from collections.abc import Callable

import click
import pytest
from click.testing import CliRunner

from ai.backend.cli.types import CliContextInfo, ExitCode
from ai.backend.client.cli.extensions import output_option, pass_ctx_obj
from ai.backend.client.cli.types import CLIContext


@pytest.fixture
def sample_cli() -> click.Group:
    """A miniature of the real CLI: a root group holding `--output` plus leaf commands."""

    @click.group()
    @click.option("--output", type=click.Choice(["json", "console"]), default="console")
    @click.pass_context
    def root(ctx: click.Context, **kwargs: str) -> None:
        ctx.obj = CliContextInfo(info=kwargs)

    @root.command()
    @pass_ctx_obj
    @output_option
    def show(ctx: CLIContext) -> None:
        click.echo(ctx.output_mode.value)

    @root.command()
    @pass_ctx_obj
    @click.option("-o", "--output", type=click.Path(), default=None)
    def export(ctx: CLIContext, output: str | None) -> None:
        click.echo(f"{ctx.output_mode.value} {output}")

    return root


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["show"], "console"),
        (["--output=json", "show"], "json"),
        (["show", "--output=json"], "json"),
        (["--output=json", "show", "--output=console"], "console"),
    ],
    ids=["default", "root-level", "subcommand-level", "subcommand-wins"],
)
def test_output_is_accepted_at_any_level(
    runner: CliRunner, sample_cli: click.Group, argv: list[str], expected: str
) -> None:
    result = runner.invoke(sample_cli, argv)
    assert result.exit_code == ExitCode.OK
    assert result.output.strip() == expected


def test_command_owning_the_name_keeps_its_own_output(
    runner: CliRunner, sample_cli: click.Group
) -> None:
    """A command declaring its own `--output` is not given `output_option`, so its meaning
    (a destination path, as in `admin export`) survives alongside the root-level flag."""
    result = runner.invoke(sample_cli, ["--output=json", "export", "-o", "out.csv"])
    assert result.exit_code == ExitCode.OK
    assert result.output.strip() == "json out.csv"

    help_result = runner.invoke(sample_cli, ["export", "--help"])
    assert "[json|console]" not in help_result.output


def test_real_command_advertises_the_output_option(
    runner: CliRunner, cli_entrypoint: Callable[[], click.Group]
) -> None:
    result = runner.invoke(cli_entrypoint, ["service", "list", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "--output" in result.output
    assert "[json|console]" in result.output


def test_export_command_keeps_its_path_typed_output_option(
    runner: CliRunner, cli_entrypoint: Callable[[], click.Group]
) -> None:
    result = runner.invoke(cli_entrypoint, ["admin", "export", "users", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "--output PATH" in result.output
    assert "[json|console]" not in result.output
