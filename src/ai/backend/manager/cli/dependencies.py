from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click

from ai.backend.common.dependencies.stacks.visualizing import VisualizingDependencyStack
from ai.backend.logging import BraceStyleAdapter

from ..dependencies.composer import DependencyInput, ManagerDependencyComposer
from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@click.group()
def cli() -> None:
    """Dependency verification commands for manager setup."""
    pass


@cli.command(name="verify")
@click.option(
    "--no-timestamps",
    is_flag=True,
    help="Hide timestamps in output",
)
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
    """
    Verify all manager dependencies can be initialized successfully.

    This command attempts to initialize all manager dependencies (bootstrap,
    infrastructure, components) and reports any failures during the setup process.

    The output shows dependency initialization with status indicators:
    - ▶ Starting (for composers)
    - ✓ Completed (for dependencies)
    - ✗ Failed (for dependencies)

    Examples:

        # Verify all dependencies with default WARNING log level
        $ backend.ai mgr dependencies verify

        # Hide timestamps in output
        $ backend.ai mgr dependencies verify --no-timestamps

        # Set log level to DEBUG to see detailed initialization logs
        $ backend.ai mgr dependencies verify --log-level DEBUG
    """
    import logging as std_logging

    # Set logging level BEFORE any dependency initialization
    std_logging.basicConfig(
        level=getattr(std_logging, log_level.upper()),
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )

    config_path = cli_ctx.config_path

    async def _verify_dependencies() -> bool:
        """Verify all manager dependencies can be initialized."""
        print("\n" + "=" * 60)
        print("Manager Dependency Verification")
        print("=" * 60)
        print(f"Config: {config_path or 'default locations'}")
        print(f"Log Level: {log_level.upper()}")
        print("=" * 60 + "\n")

        # Create visualizing stack
        stack = VisualizingDependencyStack(
            output=sys.stdout,
            show_timestamps=not no_timestamps,
        )

        try:
            async with stack:
                from ai.backend.logging import LogLevel

                dependency_input = DependencyInput(
                    config_path=config_path or Path("manager.toml"),
                    log_level=LogLevel(log_level.upper()),
                )
                composer = ManagerDependencyComposer()

                # Initialize all dependencies through the composer
                await stack.enter_composer(composer, dependency_input)

        except Exception as e:
            print(f"\n❌ Dependency initialization failed: {e}\n")

        # Print summary
        print()
        stack.print_summary()

        return not stack.has_failures()

    # Run the verification
    success = asyncio.run(_verify_dependencies())

    if success:
        print("All dependencies verified successfully!\n")
        sys.exit(0)
    else:
        print("Some dependencies failed. Check the output above for details.\n")
        sys.exit(1)
