"""Admin CLI commands for retention policy management (superadmin only)."""

from __future__ import annotations

import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)
from ai.backend.common.data.retention.types import RetentionCategory

_CATEGORY_CHOICE = click.Choice([c.value for c in RetentionCategory])


@click.group(name="retention-policy")
def retention_policy() -> None:
    """Admin retention policy commands (superadmin required)."""


@retention_policy.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--category",
    type=_CATEGORY_CHOICE,
    default=None,
    help="Filter by retention category.",
)
@click.option(
    "--enabled/--disabled",
    "enabled",
    default=None,
    help="Filter by enabled flag.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., category:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    category: str | None,
    enabled: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search retention policies (superadmin only)."""
    from ai.backend.common.dto.manager.v2.retention_policy.request import (
        RetentionPolicyFilter,
        RetentionPolicyOrder,
        SearchRetentionPoliciesInput,
    )
    from ai.backend.common.dto.manager.v2.retention_policy.types import (
        RetentionPolicyOrderField,
    )

    filter_dto: RetentionPolicyFilter | None = None
    if category is not None or enabled is not None:
        filter_dto = RetentionPolicyFilter(
            category=RetentionCategory(category) if category is not None else None,
            enabled=enabled,
        )

    orders = (
        parse_order_options(order_by, RetentionPolicyOrderField, RetentionPolicyOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.search(
                SearchRetentionPoliciesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@retention_policy.command()
@click.argument("policy_id", type=click.UUID)
def get(policy_id: uuid.UUID) -> None:
    """Get a retention policy by ID (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.get(policy_id)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@retention_policy.command()
@click.option("--category", type=_CATEGORY_CHOICE, required=True, help="Retention category.")
@click.option(
    "--retention-period-days",
    type=click.IntRange(min=1),
    required=True,
    help="Retention period in days; records older than now - period are purged.",
)
@click.option(
    "--enabled/--disabled",
    "enabled",
    default=True,
    help="Whether this policy is active (default: enabled).",
)
def create(category: str, retention_period_days: int, enabled: bool) -> None:
    """Create a retention policy (superadmin only)."""
    from ai.backend.common.dto.manager.v2.retention_policy.request import (
        CreateRetentionPolicyInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.create(
                CreateRetentionPolicyInput(
                    category=RetentionCategory(category),
                    retention_period_days=retention_period_days,
                    enabled=enabled,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@retention_policy.command()
@click.argument("policy_id", type=click.UUID)
@click.option(
    "--category",
    type=_CATEGORY_CHOICE,
    default=None,
    help="New category; omit to leave unchanged.",
)
@click.option(
    "--retention-period-days",
    type=click.IntRange(min=1),
    default=None,
    help="New retention period in days; omit to leave unchanged.",
)
@click.option(
    "--enabled/--disabled",
    "enabled",
    default=None,
    help="Toggle enabled; omit to leave unchanged.",
)
def update(
    policy_id: uuid.UUID,
    category: str | None,
    retention_period_days: int | None,
    enabled: bool | None,
) -> None:
    """Update a retention policy by ID (superadmin only)."""
    from ai.backend.common.dto.manager.v2.retention_policy.request import (
        UpdateRetentionPolicyInput,
    )
    from ai.backend.common.identifier.retention_policy import RetentionPolicyID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.update(
                policy_id,
                UpdateRetentionPolicyInput(
                    id=RetentionPolicyID(policy_id),
                    category=RetentionCategory(category) if category is not None else None,
                    retention_period_days=retention_period_days,
                    enabled=enabled,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@retention_policy.command()
@click.argument("policy_id", type=click.UUID)
def delete(policy_id: uuid.UUID) -> None:
    """Delete a retention policy by ID (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.delete(policy_id)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@retention_policy.command()
@click.argument("policy_id", type=click.UUID)
def purge(policy_id: uuid.UUID) -> None:
    """Purge (permanently remove) a retention policy by ID (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.retention_policy.purge(policy_id)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
