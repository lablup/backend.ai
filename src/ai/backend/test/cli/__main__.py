from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import click

from ai.backend.test.testcases.spec_manager import TestSpecManager
from ai.backend.test.testcases.testspecs import ROOT_TEST_SPECS
from ai.backend.test.tester.exporter import DefaultExporter
from ai.backend.test.tester.tester import Tester

from .context import CLIContext
from .utils import CommaSeparatedChoice, CustomUsageArgsCommand

_DEFAULT_CONFIG_PATH = "configs/tester/tester.toml"


def _spec_manager() -> TestSpecManager:
    """
    Returns the test specification manager for the CLI.
    """
    return TestSpecManager(specs=ROOT_TEST_SPECS)


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
    usage_args="[PKGS] [PYTEST_ARGS] --user-file [PATH] --user2-file [PATH] --admin-file [PATH]",
)
@click.argument(
    "pkgs",
    type=CommaSeparatedChoice([
        "admin",
        "user",
    ]),
    metavar="PKGS",
)
@click.option(
    "--user-file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default="env-local-user-api.sh",
    help="The path to the environment file for the first user",
)
@click.option(
    "--user2-file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default="env-local-user2-api.sh",
    help="The path to the environment file for the second user",
)
@click.option(
    "--admin-file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default="env-local-admin-api.sh",
    help="The path to the environment file for the admin user",
)
@click.pass_context
def run_cli(
    ctx: click.Context,
    pkgs: list[str],
    user_file: str,
    user2_file: str,
    admin_file: str,
) -> None:
    """A shortcut command to run pytest against a specific set of CLI-based
    integration tests

    It takes one or more test package names in a comma-separated list (PKGS)
    and forwards all other extra arguments and options (PYTEST_ARGS) to
    the underlying pytest command.


    \b
    Parameters:
        pkgs: A comma-separated list of package names to test. Available options are 'admin' and 'user'.
        user_file: Path to the environment file for the 'user' profile. Defaults to 'env-local-user-api.sh'.
        user2_file: Path to the environment file for the 'user2' profile. Defaults to 'env-local-user2-api.sh'.
        admin_file: Path to the environment file for the 'admin' profile. Defaults to 'env-local-admin-api.sh'.

    \b
    Usage:
        run_cli [PKGS] [PYTEST_ARGS] --user-file [PATH] --user2-file [PATH] --admin-file [PATH]

    \b
    Examples:
        run_cli admin,user --some-pytest-option
        run_cli user --user-file custom-user-env.sh --pytest-arg1 --pytest-arg2

    The command simplifies the process of running CLI-based integration tests for specific packages, allowing customization of the environment and passing additional arguments to pytest.
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
        ],
        env={
            **os.environ,
            "user_file": user_file,
            "user2_file": user2_file,
            "admin_file": admin_file,
        },
    )
    ctx.exit(result.returncode)


@main.command()
@click.pass_obj
def get_all_specs(cli_ctx: CLIContext) -> None:
    spec_manager = _spec_manager()
    print("Available test specifications:")
    print("====================================")
    for spec in spec_manager.all_specs():
        print(f"{spec.name}:\n {spec.description}")


@click.argument("name", type=str)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=_DEFAULT_CONFIG_PATH,
    help="The path to the configuration file for the tester",
)
@main.command(help="Run a specific test by its name")
@click.pass_obj
def run_test(cli_ctx: CLIContext, name: str, config_path: str) -> None:
    config_file_path = Path(config_path)
    spec_manager = _spec_manager()
    tester = Tester(
        spec_manager=spec_manager, exporter_type=DefaultExporter, config_file_path=config_file_path
    )
    asyncio.run(tester.run_by_name(name))


@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=_DEFAULT_CONFIG_PATH,
    help="The path to the configuration file for the tester",
)
@main.command(help="Run configured tests in the config file")
@click.pass_obj
def run(cli_ctx: CLIContext, config_path: str) -> None:
    config_file_path = Path(config_path)
    spec_manager = _spec_manager()
    tester = Tester(
        spec_manager=spec_manager, exporter_type=DefaultExporter, config_file_path=config_file_path
    )
    asyncio.run(tester.run())


@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=_DEFAULT_CONFIG_PATH,
    help="The path to the configuration file for the tester",
)
@main.command(help="Run all tests defined in the test specifications")
@click.pass_obj
def run_all(cli_ctx: CLIContext, config_path: str) -> None:
    spec_manager = _spec_manager()
    config_file_path = Path(config_path)
    tester = Tester(
        spec_manager=spec_manager, exporter_type=DefaultExporter, config_file_path=config_file_path
    )
    asyncio.run(tester.run_all())


if __name__ == "__main__":
    main()
