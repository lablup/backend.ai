from __future__ import annotations

import asyncio
import sys

import click

from ai.backend.common.dependencies.stacks.visualizing import VisualizingDependencyStack

from ..dependencies import CoordinatorDependencyComposer, DependencyInput
from .context import CLIContext


@click.group()
def cli() -> None:
    """Command set for dependency verification and validation."""
    pass


@cli.command(name="verify")
@click.option("--no-timestamps", is_flag=True, help="Hide timestamps in output")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="WARNING",
    help="Set the logging level (default: WARNING)",
)
@click.pass_obj
def verify(
    cli_ctx: CLIContext,
    no_timestamps: bool,
    log_level: str,
) -> None:
    """Verify all app proxy coordinator dependencies can be initialized successfully."""

    async def _verify_dependencies() -> bool:
        """Verify all app proxy coordinator dependencies can be initialized."""
        print("\n" + "=" * 60)
        print("App Proxy Coordinator Dependency Verification")
        print("=" * 60)
        print(f"Config: {cli_ctx.config_path or 'default locations'}")
        print(f"Log Level: {log_level.upper()}")
        print("=" * 60 + "\n")

        stack = VisualizingDependencyStack(
            output=sys.stdout,
            show_timestamps=not no_timestamps,
        )

        try:
            async with stack:
                dependency_input = DependencyInput(
                    config_path=cli_ctx.config_path,
                )
                composer = CoordinatorDependencyComposer()

                await stack.enter_composer(composer, dependency_input)

        except Exception as e:
            print(f"\n❌ Dependency initialization failed: {e}\n")

        print()
        stack.print_summary()

        return not stack.has_failures()

    success = asyncio.run(_verify_dependencies())

    if success:
        print("All dependencies verified successfully!\n")
        sys.exit(0)
    else:
        print("Some dependencies failed. Check the output above for details.\n")
        sys.exit(1)
