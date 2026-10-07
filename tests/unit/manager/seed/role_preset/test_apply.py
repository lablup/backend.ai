"""`mgr seed apply` writes the role files through the role preset creators and upserters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.cli.role_fixture import RoleFixture
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.role_preset.kind import RolePresetSeedKind
from ai.backend.manager.seed.role_preset.loader import RoleSeedLoader
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner


@pytest.fixture
def plan(role_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(SeedKindRegistry.default()).plan([role_seed_dir])


async def _presets(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str, bool, bool]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                RolePresetRow.id,
                RolePresetRow.name,
                RolePresetRow.scope_type,
                RolePresetRow.auto_assign,
                RolePresetRow.deleted,
            )
        )
        return {
            str(row.id): (row.name, str(row.scope_type), row.auto_assign, row.deleted)
            for row in rows
        }


async def _permissions(db: ExtendedAsyncSAEngine) -> set[tuple[str, str, int]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                RolePermissionPresetRow.role_preset_id,
                RolePermissionPresetRow.entity_type,
                RolePermissionPresetRow.permission,
            )
        )
        return {
            (str(row.role_preset_id), str(row.entity_type), int(row.permission)) for row in rows
        }


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The role presets the global node holds as members."""
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
                VirtualEntityRow.entity_type == "role_preset",
            )
        )
        return {str(row.entity_id) for row in rows}


def _fixture(role_seed_dir: Path) -> dict[str, Any]:
    return RoleFixture(RoleSeedLoader(role_seed_dir).load()).render_presets()


class TestApply:
    async def test_an_empty_database_gets_the_fixture_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        role_seed_dir: Path,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results["role_preset"].succeeded) == len(plan.batches[0].items())
        assert results["role_preset"].skipped == []
        fixture = _fixture(role_seed_dir)
        assert await _presets(db) == {
            row["id"]: (row["name"], row["scope_type"], row["auto_assign"], False)
            for row in fixture["role_presets"]
        }
        assert await _permissions(db) == {
            (row["role_preset_id"], row["entity_type"], row["permission"])
            for row in fixture["role_permission_presets"]
        }

    async def test_a_created_preset_is_created_in_global(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        role_seed_dir: Path,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {
            row["id"] for row in _fixture(role_seed_dir)["role_presets"]
        }

    async def test_an_existing_preset_is_skipped_and_listed(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        domain_admin_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RolePresetRow)
                .where(RolePresetRow.id == domain_admin_id)
                .values(name="renamed")
            )
        permissions = await _permissions(db)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results["role_preset"].succeeded == []
        assert len(results["role_preset"].skipped) == len(plan.batches[0].items())
        assert all(
            failure.reason.startswith("exists") for failure in results["role_preset"].skipped
        )
        assert (await _presets(db))[domain_admin_id][0] == "renamed"
        assert await _permissions(db) == permissions

    async def test_overwrite_restores_the_seed_values(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        domain_admin_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        presets = await _presets(db)
        permissions = await _permissions(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RolePresetRow)
                .where(RolePresetRow.id == domain_admin_id)
                .values(name="renamed", auto_assign=True, deleted=True)
            )
            await sess.execute(
                sa.delete(RolePermissionPresetRow).where(
                    RolePermissionPresetRow.role_preset_id == domain_admin_id
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results["role_preset"].succeeded) == len(plan.batches[0].items())
        assert await _presets(db) == presets
        assert await _permissions(db) == permissions

    async def test_overwrite_rewrites_a_stated_entity_type_to_its_grant(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        domain_admin_id: str,
    ) -> None:
        """domain_admin states `agent: [read]` and `app_config: []`."""
        await SeedApplier(repository).apply(plan, overwrite=False)
        permissions = await _permissions(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(RolePermissionPresetRow).values([
                    {"role_preset_id": domain_admin_id, "entity_type": "agent", "permission": 16},
                    {
                        "role_preset_id": domain_admin_id,
                        "entity_type": "app_config",
                        "permission": 1,
                    },
                ])
            )

        await SeedApplier(repository).apply(plan, overwrite=True)

        assert await _permissions(db) == permissions

    async def test_overwrite_keeps_an_entity_type_the_seed_leaves_out(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        domain_admin_id: str,
        role_seed_dir: Path,
    ) -> None:
        [seed] = [
            seed for seed in RoleSeedLoader(role_seed_dir).load() if str(seed.id) == domain_admin_id
        ]
        kind = RolePresetSeedKind()
        creation = kind.creation(seed)
        await repository.create_entity_with_fields(creation.creator, creation.field_creators)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(RolePermissionPresetRow).values(
                    role_preset_id=domain_admin_id, entity_type="app_config", permission=1
                )
            )
        stated_agent_only = seed.model_copy(
            update={"permissions": {"agent": seed.permissions["agent"]}}
        )

        upsert = kind.upsert(stated_agent_only)
        await repository.upsert_entity_with_fields(
            upsert.upserter, upsert.field_upserters, upsert.field_purgers
        )

        assert (domain_admin_id, "app_config", 1) in await _permissions(db)

    async def test_a_permission_row_is_unique_per_preset_type_and_bit(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        plan: SeedPlan,
        domain_admin_id: str,
    ) -> None:
        """The upserter keys a permission row on this constraint."""
        await SeedApplier(repository).apply(plan, overwrite=False)
        with pytest.raises(IntegrityError):
            async with db.begin_session() as sess:
                await sess.execute(
                    sa.insert(RolePermissionPresetRow).values(
                        role_preset_id=domain_admin_id, entity_type="agent", permission=1
                    )
                )
