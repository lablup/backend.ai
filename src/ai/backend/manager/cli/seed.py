from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from ai.backend.manager.cli.context import CLIContext
    from ai.backend.manager.seed.result import SeedWriteResult


@click.group()
def cli() -> None:
    """Command set for applying seed files."""


@cli.command(name="check")
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def check(paths: tuple[Path, ...]) -> None:
    """
    Validate seed files as `apply` does, writing nothing.

    Each path is a seed file or a directory read recursively. A file whose kind is not
    registered, whose version is not supported, whose items do not fit the kind, or
    whose kind is applied after a kind with a skipped file in the same run, is reported and fails the command.

    Examples:

    \b
      $ backend.ai mgr seed check seeds/manager/role_preset
    """
    from ai.backend.cli.types import ExitCode
    from ai.backend.manager.seed.registry import SeedKindRegistry
    from ai.backend.manager.seed.runner import SeedPlanner

    plan = SeedPlanner(SeedKindRegistry.default()).plan(paths)
    for batch in plan.batches:
        print(f"{batch.kind.name()}: {len(batch.files)} files, {len(batch.items())} items")
    if plan.rejections:
        print(f"{len(plan.rejections)} seed files skipped.", file=sys.stderr)
        sys.exit(ExitCode.FAILURE)


@cli.command(name="apply")
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--overwrite", is_flag=True, help="Rewrite existing rows with the seed values.")
@click.pass_obj
def apply(cli_ctx: CLIContext, paths: tuple[Path, ...], overwrite: bool) -> None:
    """
    Write seed files into the database, kind by kind in dependency order.

    A file failing the checks of `check` is skipped and fails the command. An item that
    exists is skipped, or upserted with `--overwrite`; an item referring to a missing
    row fails the command. Both are listed, and the rest are written.

    Examples:

    \b
      $ backend.ai mgr seed apply seeds/manager/role_preset
      $ backend.ai mgr seed apply --overwrite seeds/
    """
    from ai.backend.cli.types import ExitCode
    from ai.backend.manager.models.base import ensure_all_tables_registered
    from ai.backend.manager.repositories.db.engine import connect_database
    from ai.backend.manager.repositories.global_entity.loader import GlobalEntityIDLoader
    from ai.backend.manager.repositories.ops.repository import OpsRepository
    from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
    from ai.backend.manager.seed.registry import SeedKindRegistry
    from ai.backend.manager.seed.runner import SeedApplier, SeedPlanner

    plan = SeedPlanner(SeedKindRegistry.default()).plan(paths)

    async def _apply() -> dict[str, SeedWriteResult]:
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        # A standalone CLI process has not imported the full model tree.
        ensure_all_tables_registered()
        async with connect_database(bootstrap_config.db) as db:
            await GlobalEntityIDLoader(db).load()
            repository: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(db))
            return await SeedApplier(repository).apply(plan, overwrite)

    results = asyncio.run(_apply())
    failed = 0
    for name, result in results.items():
        print(
            f"{name}: {len(result.succeeded)} written, {len(result.skipped)} skipped,"
            f" {len(result.failed)} failed"
        )
        for failure in result.skipped:
            print(f"  skipped {failure.key}: {failure.reason}")
        for failure in result.failed:
            print(f"  failed {failure.key}: {failure.reason}")
        failed += len(result.failed)
    if plan.rejections:
        print(f"{len(plan.rejections)} seed files skipped.", file=sys.stderr)
    if failed:
        print(f"{failed} seed items failed.", file=sys.stderr)
    if plan.rejections or failed:
        sys.exit(ExitCode.FAILURE)
