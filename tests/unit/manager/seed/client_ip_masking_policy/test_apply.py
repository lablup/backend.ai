"""`mgr seed apply` writes the policies through the client IP masking policy upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(client_ip_masking_policy_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([client_ip_masking_policy_seed_dir])


async def _policies(
    db: ExtendedAsyncSAEngine,
) -> dict[str, tuple[str, str, int | None, int | None]]:
    """Each target with its row id, mode and prefixes."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(ClientIPMaskingPolicyRow.__table__))
        return {
            str(row.target_type): (str(row.id), str(row.mode), row.ipv4_prefix, row.ipv6_prefix)
            for row in rows
        }


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The policies the global node holds as members."""
    global_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == global_node,
                VirtualEntityRow.entity_type == "client_ip_masking_policy",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _insert_policy(
    db: ExtendedAsyncSAEngine, target_type: ClientIPMaskingTarget, mode: ClientIPMaskingMode
) -> str:
    """A row written outside the seed, as the API would."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(ClientIPMaskingPolicyRow).values(target_type=target_type, mode=mode)
        )
    return (await _policies(db))[target_type.value][0]


class TestApply:
    async def test_an_empty_database_gets_every_policy(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.CLIENT_IP_MASKING_POLICY].succeeded == ["default", "audit_logs"]
        policies = await _policies(db)
        assert {target: values[1:] for target, values in policies.items()} == {
            "default": ("truncate", 24, 48),
            "audit_logs": ("drop", None, None),
        }

    async def test_a_created_policy_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {values[0] for values in (await _policies(db)).values()}

    async def test_an_existing_policy_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = await _insert_policy(db, ClientIPMaskingTarget.DEFAULT, ClientIPMaskingMode.NONE)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.CLIENT_IP_MASKING_POLICY].succeeded == ["audit_logs"]
        assert [
            skipped.reason for skipped in results[SeedKind.CLIENT_IP_MASKING_POLICY].skipped
        ] == ["exists"]
        assert (await _policies(db))["default"] == (existing, "none", None, None)

    async def test_an_overwrite_updates_the_policy_and_keeps_its_id(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = await _insert_policy(db, ClientIPMaskingTarget.DEFAULT, ClientIPMaskingMode.NONE)

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.CLIENT_IP_MASKING_POLICY].succeeded == ["default", "audit_logs"]
        assert (await _policies(db))["default"] == (existing, "truncate", 24, 48)
        assert existing in await _global_members(db)
