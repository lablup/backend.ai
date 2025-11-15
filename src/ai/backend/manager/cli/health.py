from __future__ import annotations

import asyncio
import logging
import sys
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import click

from ai.backend.common.health_checker import (
    HealthProbe,
    HealthProbeOptions,
)
from ai.backend.common.health_checker.types import (
    DATABASE,
    REDIS,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.types import LogLevel

from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@click.group()
def cli() -> None:
    """Health check commands for manager components."""
    pass


@cli.command(name="check")
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
def check(
    cli_ctx: CLIContext,
    no_timestamps: bool,
    log_level: str,
) -> None:
    """
    Perform health checks on all manager dependencies.

    This command initializes all manager dependencies and then performs
    health checks on each component to verify they are responsive.

    The output shows health check results with status indicators:
    - ▶ Category (for groupings)
    - ✓ Passed (for successful checks)
    - ✗ Failed (for failed checks)

    Examples:

        # Check all health endpoints with default WARNING log level
        $ backend.ai mgr health check

        # Hide timestamps in output
        $ backend.ai mgr health check --no-timestamps

        # Set log level to DEBUG to see detailed check logs
        $ backend.ai mgr health check --log-level DEBUG
    """
    import logging as std_logging

    # Set logging level BEFORE any dependency initialization
    std_logging.basicConfig(
        level=getattr(std_logging, log_level.upper()),
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )

    config_path = cli_ctx.config_path

    async def _check_health() -> bool:
        """Perform health checks on all manager components."""
        print("\n" + "=" * 60)
        print("Manager Health Check")
        print("=" * 60)
        print(f"Config: {config_path or 'default locations'}")
        print(f"Log Level: {log_level.upper()}")
        print("=" * 60 + "\n")

        probe = HealthProbe(options=HealthProbeOptions(check_interval=60))

        # Track which checks we attempted
        results: dict[tuple[str, str], tuple[bool, str | None]] = {}

        # Initialize dependencies and register health checkers
        # Each component is tried independently so failures don't block other checks
        print("Initializing and checking components...\n")

        try:
            async with _initialize_and_check_all_components(
                config_path or Path("manager.toml"),
                LogLevel(log_level.upper()),
                probe,
                results,
            ):
                pass
        except Exception as e:
            log.error(f"Unexpected error during health check: {e}", exc_info=True)

        # Display results
        await _display_health_results_from_dict(results, no_timestamps)

        # Check if any health checks failed
        failed = sum(1 for success, _ in results.values() if not success)
        return failed == 0

    # Run the health check
    success = asyncio.run(_check_health())

    if success:
        print("\nAll health checks passed!\n")
        sys.exit(0)
    else:
        print("\nSome health checks failed. Check the output above for details.\n")
        sys.exit(1)


@asynccontextmanager
async def _initialize_and_check_all_components(
    config_path: Path,
    log_level: LogLevel,
    probe: HealthProbe,
    results: dict[tuple[str, str], tuple[bool, str | None]],
) -> AsyncIterator[None]:
    """
    Initialize dependencies and check each component independently.

    Each component is initialized and checked independently, so failures
    in one component don't prevent checking other components.
    """
    from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
    from ai.backend.manager.dependencies.bootstrap.composer import (
        BootstrapComposer,
        BootstrapInput,
    )
    from ai.backend.manager.dependencies.infrastructure.database import DatabaseDependency
    from ai.backend.manager.dependencies.infrastructure.redis import ValkeyDependency

    dependency_stack = DependencyBuilderStack()

    async with dependency_stack:
        # Bootstrap is required for other components
        bootstrap = None
        try:
            bootstrap_composer = BootstrapComposer()
            bootstrap_input = BootstrapInput(config_path=config_path, log_level=log_level)
            bootstrap = await dependency_stack.enter_composer(bootstrap_composer, bootstrap_input)
        except Exception as e:
            log.error(f"Bootstrap initialization failed: {e}", exc_info=True)
            results[("bootstrap", "etcd")] = (False, f"Failed to initialize: {str(e)}")

        # If bootstrap failed, we can't initialize other components
        if bootstrap is None:
            yield
            return

        # Try to initialize and check database independently
        try:
            db_dependency = DatabaseDependency()
            await dependency_stack.enter_dependency(db_dependency, bootstrap.config_provider.config)
        except Exception as e:
            log.error(f"Database initialization failed: {e}", exc_info=True)
            results[(DATABASE, "postgres")] = (False, f"Failed to initialize: {str(e)}")

        # Try to initialize and check Valkey clients independently
        try:
            valkey_dependency = ValkeyDependency()
            await dependency_stack.enter_dependency(
                valkey_dependency, bootstrap.config_provider.config
            )
        except Exception as e:
            log.error(f"Valkey initialization failed: {e}", exc_info=True)
            # Mark all 8 valkey clients as failed
            for component in [
                "artifact",
                "container_log",
                "live",
                "stat",
                "image",
                "stream",
                "schedule",
                "bgtask",
            ]:
                results[(REDIS, component)] = (False, f"Failed to initialize: {str(e)}")

        # Get collected health checkers and register them
        health_checkers = dependency_stack.get_health_checkers()
        for key, checker in health_checkers.items():
            await probe.register(key, checker)

        # Perform health checks on successfully initialized components
        if health_checkers:
            await probe.check_all()
            health_response = await probe.get_health_response()

            # Convert health response to results dict
            for check in health_response.connectivity_checks:
                results[(check.service_group, check.component_id)] = (
                    check.is_healthy,
                    check.error_message,
                )

        yield


async def _display_health_results_from_dict(
    results: dict[tuple[str, str], tuple[bool, str | None]],
    no_timestamps: bool,
) -> None:
    """Display health check results from results dictionary."""
    # Group by service group
    grouped: dict[str, list[tuple[str, bool, str | None]]] = defaultdict(list)
    for (service_group, component_id), (is_healthy, error_msg) in results.items():
        grouped[service_group].append((component_id, is_healthy, error_msg))

    # Display each group
    for service_group in sorted(grouped.keys()):
        checks = grouped[service_group]

        # Group header
        print(f"▶ {service_group}")

        # Display each check in the group
        for component_id, is_healthy, error_msg in sorted(checks, key=lambda x: x[0]):
            status_symbol = "✓" if is_healthy else "✗"

            error_info = ""
            if not is_healthy and error_msg:
                error_info = f" - {error_msg}"

            print(f"  {status_symbol} {component_id}{error_info}")

        print()  # Blank line between groups

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    total_checks = len(results)
    passed = sum(1 for is_healthy, _ in results.values() if is_healthy)
    failed = total_checks - passed

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Overall Status: {'HEALTHY' if failed == 0 else 'UNHEALTHY'}")
    print("=" * 60)
