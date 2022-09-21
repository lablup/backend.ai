from __future__ import annotations

import subprocess
import sys

import click

from .context import CLIContext
from .utils import CommaSeparatedChoice, CustomUsageArgsCommand


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    The integration test suite
    """
    ctx.obj = CLIContext()


@main.command(
    cls=CustomUsageArgsCommand,
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": True,
    },
    usage_args="[PKGS] [PYTEST_ARGS]",
)
@click.argument(
    "pkgs",
    type=CommaSeparatedChoice(
        [
            "admin",
            "user",
        ]
    ),
    metavar="PKGS",
)
@click.pass_context
def run_cli(
    ctx: click.Context,
    pkgs: list[str],
) -> None:
    """A shortcut command to run pytest against a specific set of CLI-based
    integration tests

    It takes one or more test package names in a comma-separated list (PKGS)
    and forwards all other extra arguments and options (PYTEST_ARGS) to
    the underlying pytest command.

    \b
    Available CLI-based integration test package names:
      admin
      user
    """
    pytest_args = ctx.args
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--pyargs",
            *(f"ai.backend.test.cli_integration.{pkg}" for pkg in pkgs),
            *pytest_args,
        ]
    )
    ctx.exit(result.returncode)


if __name__ == "__main__":
    main()
