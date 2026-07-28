"""Admin CLI commands for idle checker configurations."""

from __future__ import annotations

import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_model,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    IdleCheckerInputTypeDTO,
    IdleCheckerTypeDTO,
)
from ai.backend.common.types import SessionTypes


@click.group()
def idle_checker() -> None:
    """Idle checker admin commands (superadmin required)."""


@idle_checker.command()
@click.option("--name", required=True, type=str, help="Unique idle checker name.")
@click.option("--description", default=None, type=str, help="Idle checker description.")
@click.option(
    "--checker-type",
    required=True,
    type=click.Choice([checker_type.value for checker_type in IdleCheckerInputTypeDTO]),
    help="Idle checker implementation type.",
)
@click.option(
    "--target-session-type",
    "target_session_types",
    multiple=True,
    required=True,
    type=click.Choice([session_type.value for session_type in SessionTypes]),
    help="Target session type (repeatable).",
)
@click.option(
    "--initial-grace-period-seconds",
    default=0,
    type=click.IntRange(min=0),
    show_default=True,
    help="Grace period before the checker becomes active.",
)
@click.option(
    "--checker-spec",
    required=True,
    type=str,
    help="Checker spec as JSON or @file.",
)
def create(
    name: str,
    description: str | None,
    checker_type: str,
    target_session_types: tuple[str, ...],
    initial_grace_period_seconds: int,
    checker_spec: str,
) -> None:
    """Create an idle checker."""
    from ai.backend.common.dto.manager.v2.idle_checker.request import (
        CreateIdleCheckerInput,
        IdleCheckerSpecInputDTO,
    )

    input_ = CreateIdleCheckerInput(
        name=name,
        description=description,
        checker_type=IdleCheckerInputTypeDTO(checker_type),
        target_session_types=[SessionTypes(session_type) for session_type in target_session_types],
        initial_grace_period_seconds=initial_grace_period_seconds,
        checker_spec=load_model(checker_spec, IdleCheckerSpecInputDTO),
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.idle_checker.admin_create(input_))
        finally:
            await registry.close()

    run_async(_run)


@idle_checker.command()
@click.option("--limit", type=click.IntRange(min=1), default=20, show_default=True)
@click.option("--offset", type=click.IntRange(min=0), default=0, show_default=True)
@click.option("--name-contains", default=None, type=str, help="Filter by name substring.")
@click.option(
    "--checker-type",
    default=None,
    type=click.Choice([checker_type.value for checker_type in IdleCheckerTypeDTO]),
    help="Filter by checker type.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (for example, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    checker_type: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search idle checkers."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.idle_checker.request import (
        IdleCheckerFilter,
        IdleCheckerOrder,
        SearchIdleCheckersInput,
    )
    from ai.backend.common.dto.manager.v2.idle_checker.types import (
        CheckerTypeFilter,
        IdleCheckerOrderField,
    )

    filter_ = None
    if name_contains is not None or checker_type is not None:
        filter_ = IdleCheckerFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            checker_type=(
                CheckerTypeFilter(equals=IdleCheckerTypeDTO(checker_type))
                if checker_type is not None
                else None
            ),
        )
    orders = (
        parse_order_options(order_by, IdleCheckerOrderField, IdleCheckerOrder) if order_by else None
    )
    input_ = SearchIdleCheckersInput(
        filter=filter_,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.idle_checker.admin_search(input_))
        finally:
            await registry.close()

    run_async(_run)


@idle_checker.command()
@click.argument("idle_checker_id", type=click.UUID)
@click.option("--name", default=None, type=str, help="Updated name.")
@click.option("--description", default=None, type=str, help="Updated description.")
@click.option(
    "--clear-description",
    is_flag=True,
    help="Clear the current description.",
)
@click.option(
    "--target-session-type",
    "target_session_types",
    multiple=True,
    type=click.Choice([session_type.value for session_type in SessionTypes]),
    help="Replacement target session type (repeatable).",
)
@click.option(
    "--initial-grace-period-seconds",
    default=None,
    type=click.IntRange(min=0),
    help="Updated grace period.",
)
@click.option(
    "--checker-spec",
    default=None,
    type=str,
    help="Replacement checker spec as JSON or @file.",
)
def update(
    idle_checker_id: uuid.UUID,
    name: str | None,
    description: str | None,
    clear_description: bool,
    target_session_types: tuple[str, ...],
    initial_grace_period_seconds: int | None,
    checker_spec: str | None,
) -> None:
    """Update an idle checker."""
    from ai.backend.common.api_handlers import SENTINEL
    from ai.backend.common.dto.manager.v2.idle_checker.request import (
        IdleCheckerSpecInputDTO,
        UpdateIdleCheckerInput,
    )
    from ai.backend.common.identifier.idle_checker import IdleCheckerID

    if description is not None and clear_description:
        raise click.UsageError("--description and --clear-description cannot be used together")

    checker_id = IdleCheckerID(idle_checker_id)
    input_ = UpdateIdleCheckerInput(
        id=checker_id,
        name=name,
        description=(
            None if clear_description else description if description is not None else SENTINEL
        ),
        target_session_types=(
            [SessionTypes(session_type) for session_type in target_session_types]
            if target_session_types
            else None
        ),
        initial_grace_period_seconds=initial_grace_period_seconds,
        checker_spec=(
            load_model(checker_spec, IdleCheckerSpecInputDTO) if checker_spec is not None else None
        ),
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.idle_checker.admin_update(checker_id, input_))
        finally:
            await registry.close()

    run_async(_run)


@idle_checker.command()
@click.argument("idle_checker_id", type=click.UUID)
def purge(idle_checker_id: uuid.UUID) -> None:
    """Permanently remove an idle checker."""
    from ai.backend.common.identifier.idle_checker import IdleCheckerID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.idle_checker.admin_purge(IdleCheckerID(idle_checker_id)))
        finally:
            await registry.close()

    run_async(_run)
