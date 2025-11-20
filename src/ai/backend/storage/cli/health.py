from __future__ import annotations

import click

from .context import CLIContext


@click.group()
def cli() -> None:
    """Health check commands for storage proxy components."""
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
    Perform health checks on all storage proxy dependencies.

    This command initializes all storage proxy dependencies and then performs
    health checks on each component to verify they are responsive.

    The output shows health check results with status indicators:
    - ▶ Category (for groupings)
    - ✓ Passed (for successful checks)
    - ✗ Failed (for failed checks)

    Examples:

        # Check all health endpoints with default WARNING log level
        $ backend.ai storage health check

        # Hide timestamps in output
        $ backend.ai storage health check --no-timestamps

        # Set log level to DEBUG to see detailed check logs
        $ backend.ai storage health check --log-level DEBUG
    """
    import asyncio
    import logging as std_logging
    import sys
    from collections import defaultdict
    from collections.abc import AsyncIterator
    from contextlib import asynccontextmanager
    from pathlib import Path

    from ai.backend.common.dto.internal.health import ConnectivityCheckResponse
    from ai.backend.common.health_checker import (
        HealthProbe,
        HealthProbeOptions,
    )

    # Set logging level BEFORE any dependency initialization
    std_logging.basicConfig(
        level=getattr(std_logging, log_level.upper()),
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )

    config_path = cli_ctx.config_path

    @asynccontextmanager
    async def _initialize_and_check_all_components(
        config_path: Path,
        probe: HealthProbe,
    ) -> AsyncIterator[None]:
        """
        Initialize dependencies using StorageDependencyComposer.

        Uses the StorageDependencyComposer to initialize all dependencies in the correct order,
        then collects health checkers from the DependencyBuilderStack.
        """
        from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
        from ai.backend.storage.dependencies.composer import (
            DependencyInput,
            StorageDependencyComposer,
        )

        dependency_stack = DependencyBuilderStack()

        async with dependency_stack:
            # Use StorageDependencyComposer to initialize all dependencies
            storage_composer = StorageDependencyComposer()
            storage_input = DependencyInput(config_path=config_path)
            await dependency_stack.enter_composer(storage_composer, storage_input)

            # Get collected health checkers and register them
            health_checkers = dependency_stack.get_health_checkers()
            for key, checker in health_checkers.items():
                await probe.register(checker)

            # Perform health checks on successfully initialized components
            if health_checkers:
                await probe.check_all()

            yield

    async def _display_health_results(
        health_response: ConnectivityCheckResponse,
        no_timestamps: bool,
    ) -> None:
        """Display health check results."""
        # Group by service group
        grouped: dict[str, list[tuple[str, bool, str | None]]] = defaultdict(list)
        for check in health_response.connectivity_checks:
            grouped[check.service_group].append((
                check.component_id,
                check.is_healthy,
                check.error_message,
            ))

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
                    error_info = f" - {error_msg.strip()}"

                print(f"  {status_symbol} {component_id}{error_info}")

            print()  # Blank line between groups

        # Summary
        print("=" * 60)
        print("Summary")
        print("=" * 60)

        total_checks = len(health_response.connectivity_checks)
        passed = sum(1 for check in health_response.connectivity_checks if check.is_healthy)
        failed = total_checks - passed

        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Overall Status: {'HEALTHY' if health_response.overall_healthy else 'UNHEALTHY'}")
        print("=" * 60)

    async def _check_health() -> bool:
        """Perform health checks on all storage proxy components."""
        print("\n" + "=" * 60)
        print("Storage Proxy Health Check")
        print("=" * 60)
        print(f"Config: {config_path or 'default locations'}")
        print(f"Log Level: {log_level.upper()}")
        print("=" * 60 + "\n")

        probe = HealthProbe(options=HealthProbeOptions(check_interval=60))

        # Initialize dependencies and register health checkers
        print("Initializing and checking components...\n")

        try:
            async with _initialize_and_check_all_components(
                config_path or Path("storage-proxy.toml"),
                probe,
            ):
                pass
        except Exception as e:
            print(f"✗ Failed to initialize dependencies: {str(e).strip()}\n")
            return False

        # Get health check results
        health_response = await probe.get_connectivity_status()

        # Display results
        await _display_health_results(health_response, no_timestamps)

        # Check if any health checks failed
        return health_response.overall_healthy

    # Run the health check
    success = asyncio.run(_check_health())

    if success:
        print("\nAll health checks passed!\n")
        sys.exit(0)
    else:
        print("\nSome health checks failed. Check the output above for details.\n")
        sys.exit(1)
