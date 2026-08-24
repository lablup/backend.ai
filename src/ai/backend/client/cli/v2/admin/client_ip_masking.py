"""Admin CLI commands for the client IP masking policies."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)

_TARGET_TYPES = ["default", "login_history"]
_MODES = ["none", "truncate", "drop"]


@click.group(name="client-ip-masking-policy")
def client_ip_masking_policy() -> None:
    """Client IP masking policy admin commands."""


@client_ip_masking_policy.command()
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option(
    "--target-type",
    type=click.Choice(_TARGET_TYPES, case_sensitive=False),
    default=None,
    help="Filter by the governed target.",
)
@click.option(
    "--mode",
    type=click.Choice(_MODES, case_sensitive=False),
    default=None,
    help="Filter by masking mode.",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., target_type:asc). "
        "Fields: target_type, mode, created_at, updated_at."
    ),
)
def search(
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    limit: int | None,
    offset: int | None,
    target_type: str | None,
    mode: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Read the masking set for every target (superadmin only)."""
    from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
        AdminSearchClientIPMaskingPoliciesInput,
        ClientIPMaskingPolicyFilter,
        ClientIPMaskingPolicyOrder,
    )
    from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
        ClientIPMaskingMode,
        ClientIPMaskingPolicyOrderField,
        ClientIPMaskingTarget,
    )

    filter_dto: ClientIPMaskingPolicyFilter | None = None
    if target_type is not None or mode is not None:
        filter_dto = ClientIPMaskingPolicyFilter(
            target_type=ClientIPMaskingTarget(target_type) if target_type else None,
            mode=ClientIPMaskingMode(mode) if mode else None,
        )
    orders = (
        parse_order_options(order_by, ClientIPMaskingPolicyOrderField, ClientIPMaskingPolicyOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            payload = await registry.client_ip_masking.admin_search(
                AdminSearchClientIPMaskingPoliciesInput(
                    filter=filter_dto,
                    order=orders,
                    first=first,
                    after=after,
                    last=last,
                    before=before,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(payload)
        finally:
            await registry.close()

    asyncio.run(_run())


@client_ip_masking_policy.command()
@click.argument("target_type", type=click.Choice(_TARGET_TYPES, case_sensitive=False))
@click.argument("mode", type=click.Choice(_MODES, case_sensitive=False))
def upsert(target_type: str, mode: str) -> None:
    """Set the masking one target gets (superadmin only)."""
    from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
        AdminUpsertClientIPMaskingPolicyInput,
    )
    from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
        ClientIPMaskingMode,
        ClientIPMaskingTarget,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            payload = await registry.client_ip_masking.admin_upsert(
                AdminUpsertClientIPMaskingPolicyInput(
                    target_type=ClientIPMaskingTarget(target_type),
                    mode=ClientIPMaskingMode(mode),
                ),
            )
            print_result(payload)
        finally:
            await registry.close()

    asyncio.run(_run())


@client_ip_masking_policy.command()
@click.argument("policy_id", type=click.UUID)
def purge(policy_id: str) -> None:
    """Drop one target's policy so it falls back to the default (superadmin only)."""
    from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
        AdminPurgeClientIPMaskingPolicyInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            payload = await registry.client_ip_masking.admin_purge(
                AdminPurgeClientIPMaskingPolicyInput(id=policy_id),
            )
            print_result(payload)
        finally:
            await registry.close()

    asyncio.run(_run())
