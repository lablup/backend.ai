"""`mgr seed apply` writes each binding through the upserter of its scope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"
_PUBLIC_KEY = "BACKENDAI_SESSION_ID:public"
_DOMAIN_KEY = f"BACKENDAI_USER_EMAIL:domain:{_DOMAIN_ID}"


@dataclass(frozen=True)
class _Binding:
    value_source: SystemSessionEnvironValueSource
    enabled: bool


async def _bindings(db: ExtendedAsyncSAEngine) -> dict[str, _Binding]:
    """Each binding by the key its seed item answers, with the public scope named."""
    public_id = global_entity_id(GlobalEntityName.PUBLIC)
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(SystemSessionEnvironRow.__table__))
        return {
            (
                f"{row.key}:{row.scope_type}"
                if row.scope_id == public_id
                else f"{row.key}:{row.scope_type}:{row.scope_id}"
            ): _Binding(value_source=row.value_source, enabled=row.enabled)
            for row in rows
        }


async def _members(db: ExtendedAsyncSAEngine, entity_type: str, entity_id: str) -> set[str]:
    """The bindings the node of ``entity_type`` and ``entity_id`` holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "system_session_environ",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _id_of(db: ExtendedAsyncSAEngine, key: str) -> str:
    async with db.begin_readonly() as conn:
        return str(
            await conn.scalar(
                sa.select(SystemSessionEnvironRow.id).where(SystemSessionEnvironRow.key == key)
            )
        )


@pytest.fixture
def plan(system_session_environ_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([system_session_environ_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
async def switched_off_after_apply(applied: None, db: ExtendedAsyncSAEngine) -> None:
    """The public binding switched off after the seed wrote it."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(SystemSessionEnvironRow)
            .where(SystemSessionEnvironRow.key == "BACKENDAI_SESSION_ID")
            .values(enabled=False)
        )


@pytest.fixture
def changed_plan(applied: None, system_session_environ_seed_dir: Path) -> SeedPlan:
    """The seeds with the public binding stating another source, switched off."""
    (system_session_environ_seed_dir / "system_session_environ" / "bindings.yaml").write_text(
        yaml.safe_dump({
            "kind": "system_session_environ",
            "version": 1,
            "items": [
                {
                    "value_source": "session_name",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "public",
                    "enabled": False,
                }
            ],
        })
    )
    return SeedPlanner(create_seed_kind_registry()).plan([system_session_environ_seed_dir])


@pytest.fixture
async def migrated_public_binding(db: ExtendedAsyncSAEngine) -> SystemSessionEnvironID:
    """The public binding written as the migration writes it: the row alone, in no scope."""
    async with db.begin_session() as sess:
        row = SystemSessionEnvironRow(
            value_source=SystemSessionEnvironValueSource.SESSION_ID,
            key="BACKENDAI_SESSION_ID",
            scope_type=SystemSessionEnvironScopeType.PUBLIC,
            scope_id=SystemSessionEnvironScopeID(global_entity_id(GlobalEntityName.PUBLIC)),
            enabled=True,
        )
        sess.add(row)
        await sess.flush()
        return row.id


class TestApply:
    async def test_an_empty_database_gets_every_binding(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.SYSTEM_SESSION_ENVIRON].succeeded == [_PUBLIC_KEY, _DOMAIN_KEY]
        assert await _bindings(db) == {
            _PUBLIC_KEY: _Binding(
                value_source=SystemSessionEnvironValueSource.SESSION_ID, enabled=True
            ),
            _DOMAIN_KEY: _Binding(
                value_source=SystemSessionEnvironValueSource.USER_EMAIL, enabled=False
            ),
        }

    @pytest.mark.parametrize(
        "scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC], ids=lambda name: name.value
    )
    async def test_a_public_binding_is_created_in_global_and_public(
        self, db: ExtendedAsyncSAEngine, applied: None, scope: GlobalEntityName
    ) -> None:
        members = await _members(db, str(GlobalEntityType()), str(global_entity_id(scope)))

        assert members == {await _id_of(db, "BACKENDAI_SESSION_ID")}

    async def test_a_domain_binding_is_created_in_its_domain(
        self, db: ExtendedAsyncSAEngine, applied: None
    ) -> None:
        members = await _members(db, str(DomainEntityType()), _DOMAIN_ID)

        assert members == {await _id_of(db, "BACKENDAI_USER_EMAIL")}

    async def test_an_existing_binding_is_skipped_and_kept(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        switched_off_after_apply: None,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.SYSTEM_SESSION_ENVIRON].succeeded == []
        assert [skip.reason for skip in results[SeedKind.SYSTEM_SESSION_ENVIRON].skipped] == [
            "exists",
            "exists",
        ]
        assert (await _bindings(db))[_PUBLIC_KEY].enabled is False

    async def test_an_overwrite_replaces_the_source_and_the_switch(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, changed_plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(changed_plan, overwrite=True)

        assert (await _bindings(db))[_PUBLIC_KEY] == _Binding(
            value_source=SystemSessionEnvironValueSource.SESSION_NAME, enabled=False
        )

    async def test_a_binding_the_migration_wrote_is_kept_and_placed_in_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        migrated_public_binding: SystemSessionEnvironID,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert [skip.reason for skip in results[SeedKind.SYSTEM_SESSION_ENVIRON].skipped] == [
            "exists"
        ]
        members = await _members(
            db, str(GlobalEntityType()), str(global_entity_id(GlobalEntityName.PUBLIC))
        )
        assert members == {str(migrated_public_binding)}
