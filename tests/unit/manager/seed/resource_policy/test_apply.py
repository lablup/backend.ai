"""`mgr seed apply` writes the resource policy files through their upserters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_ROWS: dict[SeedKind, type[Base]] = {
    SeedKind.USER_RESOURCE_POLICY: UserResourcePolicyRow,
    SeedKind.PROJECT_RESOURCE_POLICY: ProjectResourcePolicyRow,
    SeedKind.KEYPAIR_RESOURCE_POLICY: KeyPairResourcePolicyRow,
}


@pytest.fixture
def plan(resource_policy_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([resource_policy_seed_dir])


async def _rows(db: ExtendedAsyncSAEngine, row_class: type[Base]) -> dict[str, dict[str, Any]]:
    """Each row by its uuid, without ``created_at``."""
    table = row_class.__table__
    columns = [column for column in table.columns if column.name != "created_at"]
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(*columns))
        return {str(row.uuid): dict(row._mapping) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine, entity_type: str) -> set[str]:
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
                VirtualEntityRow.entity_type == entity_type,
            )
        )
        return {str(row.entity_id) for row in rows}


async def _change_all(db: ExtendedAsyncSAEngine) -> None:
    """Change the columns a seed states on every row."""
    async with db.begin_session() as sess:
        await sess.execute(sa.update(UserResourcePolicyRow).values(max_vfolder_count=99))
        await sess.execute(sa.update(ProjectResourcePolicyRow).values(max_network_count=99))
        await sess.execute(
            sa.update(KeyPairResourcePolicyRow).values(
                max_concurrent_sessions=99, max_priority=1, allowed_vfolder_hosts={}
            )
        )


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        for kind, row_class in _ROWS.items():
            [item] = [batch for batch in plan.batches if batch.kind.name == kind][0].items()
            assert results[kind].succeeded == [item.key()]
            rows = await _rows(db, row_class)
            assert set(rows) == {item.key()}
        [keypair] = (await _rows(db, KeyPairResourcePolicyRow)).values()
        assert keypair["is_default"] is True
        assert keypair["max_pending_session_resource_slots"] == ResourceSlot({"cpu": 2})
        assert keypair["allowed_vfolder_hosts"] == {
            "local:volume1": {"create-vfolder", "mount-in-session"}
        }

    async def test_a_created_policy_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)

        for kind, row_class in _ROWS.items():
            assert await _global_members(db, kind) == set(await _rows(db, row_class))

    async def test_an_existing_policy_is_skipped(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        await _change_all(db)
        changed = {kind: await _rows(db, row_class) for kind, row_class in _ROWS.items()}

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        for kind, row_class in _ROWS.items():
            assert results[kind].succeeded == []
            assert all(failure.reason.startswith("exists") for failure in results[kind].skipped)
            assert await _rows(db, row_class) == changed[kind]

    async def test_overwrite_restores_the_seed_values(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        written = {kind: await _rows(db, row_class) for kind, row_class in _ROWS.items()}
        await _change_all(db)

        await SeedApplier(repository).apply(plan, overwrite=True)

        for kind, row_class in _ROWS.items():
            assert await _rows(db, row_class) == written[kind]

    async def test_overwrite_keeps_the_name(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """The name is the key users refer to, so it is written on insert only."""
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(sa.update(UserResourcePolicyRow).values(name="renamed"))

        await SeedApplier(repository).apply(plan, overwrite=True)

        [user_policy] = (await _rows(db, UserResourcePolicyRow)).values()
        assert user_policy["name"] == "renamed"

    async def test_a_name_held_under_another_uuid_skips_the_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(ProjectResourcePolicyRow).values(
                    name="default",
                    max_vfolder_count=1,
                    max_quota_scope_size=1,
                    max_network_count=1,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.PROJECT_RESOURCE_POLICY].succeeded == []
        [skipped] = results[SeedKind.PROJECT_RESOURCE_POLICY].skipped
        assert skipped.reason.startswith("collides with a row")
        assert len(results[SeedKind.USER_RESOURCE_POLICY].succeeded) == 1

    async def test_a_second_default_keypair_policy_is_skipped(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(KeyPairResourcePolicyRow).values(
                    name="other",
                    is_default=True,
                    total_resource_slots=ResourceSlot({"cpu": 1}),
                    max_concurrent_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=0,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.KEYPAIR_RESOURCE_POLICY].succeeded == []
        [skipped] = results[SeedKind.KEYPAIR_RESOURCE_POLICY].skipped
        assert skipped.reason.startswith("collides with a row")
