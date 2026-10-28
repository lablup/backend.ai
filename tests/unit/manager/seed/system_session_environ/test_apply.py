"""`mgr seed apply` writes each binding through the upserter of its scope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironEntityType,
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"
_PUBLIC_SESSION_ID_SEED_KEY = "BACKENDAI_SESSION_ID:public"
_DOMAIN_USER_EMAIL_SEED_KEY = f"BACKENDAI_USER_EMAIL:domain:{_DOMAIN_ID}"


@dataclass(frozen=True)
class _ValueSourceAndDeleted:
    value_source: SystemSessionEnvironValueSource
    deleted: bool


async def _rows_by_seed_key(
    db: ExtendedAsyncSAEngine,
) -> dict[str, set[_ValueSourceAndDeleted]]:
    """The bindings under the key their seed item answers, with the public scope named."""
    public_id = global_entity_id(GlobalEntityName.PUBLIC)
    rows_by_seed_key: dict[str, set[_ValueSourceAndDeleted]] = {}
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(SystemSessionEnvironRow.__table__))
        for row in rows:
            seed_key = (
                f"{row.key}:{row.scope_type}"
                if row.scope_id == public_id
                else f"{row.key}:{row.scope_type}:{row.scope_id}"
            )
            rows_by_seed_key.setdefault(seed_key, set()).add(
                _ValueSourceAndDeleted(
                    value_source=row.value_source, deleted=row.deleted_at is not None
                )
            )
    return rows_by_seed_key


async def _environ_ids_reached_from(
    db: ExtendedAsyncSAEngine, scope_type: EntityType, scope_id: UUID
) -> set[str]:
    """The bindings a role at the scope reaches, as a permission check walks the graph."""
    async with db.begin_readonly() as conn:
        environ_ids = await conn.scalars(
            sa.select(SystemSessionEnvironRow.id).where(
                scope_membership_exists(
                    scope_type,
                    scope_id,
                    SystemSessionEnvironEntityType(),
                    SystemSessionEnvironRow.id,
                )
            )
        )
        return {str(environ_id) for environ_id in environ_ids}


async def _environ_id_of_key(db: ExtendedAsyncSAEngine, key: str) -> str:
    async with db.begin_readonly() as conn:
        return str(
            await conn.scalar(
                sa.select(SystemSessionEnvironRow.id).where(SystemSessionEnvironRow.key == key)
            )
        )


@pytest.fixture
def system_session_environ_plan(system_session_environ_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([system_session_environ_seed_dir])


@pytest.fixture
async def seeds_applied_once(
    repository: SeedRepository, system_session_environ_plan: SeedPlan
) -> None:
    await SeedApplier(repository).apply(system_session_environ_plan, overwrite=False)


@pytest.fixture
async def public_session_id_deleted_after_apply(
    seeds_applied_once: None, db: ExtendedAsyncSAEngine
) -> None:
    """The public binding soft-deleted after the seed wrote it."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(SystemSessionEnvironRow)
            .where(SystemSessionEnvironRow.key == "BACKENDAI_SESSION_ID")
            .values(deleted_at=sa.func.now())
        )


@pytest.fixture
def plan_rebinding_public_session_id(
    seeds_applied_once: None, system_session_environ_seed_dir: Path
) -> SeedPlan:
    """The seeds with the public binding stating another source."""
    (system_session_environ_seed_dir / "system_session_environ" / "bindings.yaml").write_text(
        yaml.safe_dump({
            "kind": "system_session_environ",
            "version": 1,
            "items": [
                {
                    "value_source": "session_name",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "public",
                }
            ],
        })
    )
    return SeedPlanner(create_seed_kind_registry()).plan([system_session_environ_seed_dir])


@pytest.fixture
async def public_session_id_row_from_migration(db: ExtendedAsyncSAEngine) -> SystemSessionEnvironID:
    """The public binding written as the migration writes it: the row alone, in no scope."""
    async with db.begin_session() as sess:
        row = SystemSessionEnvironRow(
            value_source=SystemSessionEnvironValueSource.SESSION_ID,
            key="BACKENDAI_SESSION_ID",
            scope_type=SystemSessionEnvironScopeType.PUBLIC,
            scope_id=SystemSessionEnvironScopeID(global_entity_id(GlobalEntityName.PUBLIC)),
        )
        sess.add(row)
        await sess.flush()
        return row.id


class TestApply:
    async def test_an_empty_database_gets_every_binding(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        system_session_environ_plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(system_session_environ_plan, overwrite=False)

        assert results[SeedKind.SYSTEM_SESSION_ENVIRON].succeeded == [
            _PUBLIC_SESSION_ID_SEED_KEY,
            _DOMAIN_USER_EMAIL_SEED_KEY,
        ]
        assert await _rows_by_seed_key(db) == {
            _PUBLIC_SESSION_ID_SEED_KEY: {
                _ValueSourceAndDeleted(
                    value_source=SystemSessionEnvironValueSource.SESSION_ID, deleted=False
                )
            },
            _DOMAIN_USER_EMAIL_SEED_KEY: {
                _ValueSourceAndDeleted(
                    value_source=SystemSessionEnvironValueSource.USER_EMAIL, deleted=False
                )
            },
        }

    async def test_global_reaches_every_binding(
        self, db: ExtendedAsyncSAEngine, seeds_applied_once: None
    ) -> None:
        reached = await _environ_ids_reached_from(
            db, GlobalEntityType(), global_entity_id(GlobalEntityName.GLOBAL)
        )

        assert reached == {
            await _environ_id_of_key(db, "BACKENDAI_SESSION_ID"),
            await _environ_id_of_key(db, "BACKENDAI_USER_EMAIL"),
        }

    async def test_public_reaches_only_the_public_binding(
        self, db: ExtendedAsyncSAEngine, seeds_applied_once: None
    ) -> None:
        reached = await _environ_ids_reached_from(
            db, GlobalEntityType(), global_entity_id(GlobalEntityName.PUBLIC)
        )

        assert reached == {await _environ_id_of_key(db, "BACKENDAI_SESSION_ID")}

    async def test_a_domain_reaches_only_its_binding(
        self, db: ExtendedAsyncSAEngine, seeds_applied_once: None
    ) -> None:
        reached = await _environ_ids_reached_from(db, DomainEntityType(), UUID(_DOMAIN_ID))

        assert reached == {await _environ_id_of_key(db, "BACKENDAI_USER_EMAIL")}

    async def test_a_deleted_binding_stays_deleted(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        system_session_environ_plan: SeedPlan,
        public_session_id_deleted_after_apply: None,
    ) -> None:
        results = await SeedApplier(repository).apply(system_session_environ_plan, overwrite=False)

        assert results[SeedKind.SYSTEM_SESSION_ENVIRON].succeeded == []
        assert [skip.reason for skip in results[SeedKind.SYSTEM_SESSION_ENVIRON].skipped] == [
            "exists",
            "exists",
        ]
        assert (await _rows_by_seed_key(db))[_PUBLIC_SESSION_ID_SEED_KEY] == {
            _ValueSourceAndDeleted(
                value_source=SystemSessionEnvironValueSource.SESSION_ID, deleted=True
            )
        }

    async def test_an_overwrite_replaces_the_source(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan_rebinding_public_session_id: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan_rebinding_public_session_id, overwrite=True)

        assert (await _rows_by_seed_key(db))[_PUBLIC_SESSION_ID_SEED_KEY] == {
            _ValueSourceAndDeleted(
                value_source=SystemSessionEnvironValueSource.SESSION_NAME, deleted=False
            )
        }

    async def test_an_overwrite_rewrites_a_deleted_binding_and_leaves_it_deleted(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        public_session_id_deleted_after_apply: None,
        plan_rebinding_public_session_id: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan_rebinding_public_session_id, overwrite=True)

        assert (await _rows_by_seed_key(db))[_PUBLIC_SESSION_ID_SEED_KEY] == {
            _ValueSourceAndDeleted(
                value_source=SystemSessionEnvironValueSource.SESSION_NAME, deleted=True
            )
        }

    async def test_a_binding_the_migration_wrote_is_kept_and_placed_in_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        system_session_environ_plan: SeedPlan,
        public_session_id_row_from_migration: SystemSessionEnvironID,
    ) -> None:
        results = await SeedApplier(repository).apply(system_session_environ_plan, overwrite=False)

        assert [skip.reason for skip in results[SeedKind.SYSTEM_SESSION_ENVIRON].skipped] == [
            "exists"
        ]
        reached = await _environ_ids_reached_from(
            db, GlobalEntityType(), global_entity_id(GlobalEntityName.PUBLIC)
        )
        assert reached == {str(public_session_id_row_from_migration)}
