"""Integration tests for execute_pruner with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base import (
    CascadeChild,
    PrunerResult,
    PrunerSpec,
    execute_pruner,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# Module-level test ORM models so SQLAlchemy can resolve them.


class PrunerTestParentRow(Base):  # type: ignore[misc]
    """Parent table for pruner tests with a status + terminated_at."""

    __tablename__ = "test_pruner_parent"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)
    terminated_at = sa.Column(sa.DateTime(timezone=True), nullable=True)


class PrunerTestChildRow(Base):  # type: ignore[misc]
    """Child table FK-bound to PrunerTestParentRow.id (for cascade tests)."""

    __tablename__ = "test_pruner_child"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = sa.Column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("test_pruner_parent.id"),
        nullable=False,
    )
    name = sa.Column(sa.String(50), nullable=False)


class TestChildCascade(CascadeChild[PrunerTestChildRow]):
    @classmethod
    def row_class(cls) -> type[PrunerTestChildRow]:
        return PrunerTestChildRow

    @classmethod
    def parent_id_column(cls) -> Any:
        return PrunerTestChildRow.parent_id


@dataclass
class TerminatedTestParentPrunerSpec(PrunerSpec[PrunerTestParentRow]):
    """Default spec — no entity_type, so RBAC cleanup is skipped."""

    @classmethod
    def row_class(cls) -> type[PrunerTestParentRow]:
        return PrunerTestParentRow

    @classmethod
    def prune_condition(cls) -> sa.ColumnElement[bool]:
        return PrunerTestParentRow.status == "terminated"


@dataclass
class TerminatedTestParentPrunerSpecWithRBAC(TerminatedTestParentPrunerSpec):
    """Variant that opts into RBAC cleanup using EntityType.SESSION as a stand-in."""

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


async def _seed_parents(
    db: ExtendedAsyncSAEngine,
) -> dict[str, list[UUID]]:
    """Insert 5 terminated + 3 active parent rows; return PKs grouped by status."""
    now = datetime.now(UTC)
    terminated: list[UUID] = []
    active: list[UUID] = []
    async with db.begin_session() as db_sess:
        for i in range(5):
            row_id = uuid.uuid4()
            db_sess.add(
                PrunerTestParentRow(
                    id=row_id,
                    name=f"term-{i}",
                    status="terminated",
                    terminated_at=now - timedelta(hours=2 if i < 3 else 0),
                )
            )
            terminated.append(row_id)
        for i in range(3):
            row_id = uuid.uuid4()
            db_sess.add(
                PrunerTestParentRow(
                    id=row_id,
                    name=f"active-{i}",
                    status="active",
                    terminated_at=None,
                )
            )
            active.append(row_id)
    return {"terminated": terminated, "active": active}


@pytest.fixture
async def parent_only_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Create parent table only (no children, no RBAC table)."""
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.create(c, checkfirst=True))
    yield database_connection
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.drop(c, checkfirst=True))


@pytest.fixture
async def parent_child_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Create parent + FK-bound child tables."""
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.create(c, checkfirst=True))
        await conn.run_sync(lambda c: PrunerTestChildRow.__table__.create(c, checkfirst=True))
    yield database_connection
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: PrunerTestChildRow.__table__.drop(c, checkfirst=True))
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.drop(c, checkfirst=True))


@pytest.fixture
async def parent_with_rbac_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Create parent + association_scopes_entities tables for RBAC tests."""
    async with database_connection.begin() as conn:
        # association_scopes_entities.id has server_default=uuid_generate_v4().
        await conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.create(c, checkfirst=True))
        await conn.run_sync(
            lambda c: AssociationScopesEntitiesRow.__table__.create(c, checkfirst=True)
        )
    yield database_connection
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: AssociationScopesEntitiesRow.__table__.drop(c, checkfirst=True)
        )
        await conn.run_sync(lambda c: PrunerTestParentRow.__table__.drop(c, checkfirst=True))


class TestPrunerBasic:
    """Core behavior — no cascade, no RBAC."""

    async def test_prune_terminal_rows(self, parent_only_tables: ExtendedAsyncSAEngine) -> None:
        seeded = await _seed_parents(parent_only_tables)
        async with parent_only_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec()
            result = await execute_pruner(db_sess, spec)

        assert isinstance(result, PrunerResult)
        assert result.count == 5
        assert set(result.ids) == set(seeded["terminated"])

        async with parent_only_tables.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalars(sa.select(PrunerTestParentRow.id))
            assert set(remaining.all()) == set(seeded["active"])

    async def test_prune_no_matching_rows(self, parent_only_tables: ExtendedAsyncSAEngine) -> None:
        # Only active rows seeded — terminal-state condition matches none.
        async with parent_only_tables.begin_session() as db_sess:
            for i in range(3):
                db_sess.add(
                    PrunerTestParentRow(
                        id=uuid.uuid4(),
                        name=f"active-{i}",
                        status="active",
                    )
                )

        async with parent_only_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec()
            result = await execute_pruner(db_sess, spec)

        assert result.count == 0
        assert result.ids == []

    async def test_prune_empty_table(self, parent_only_tables: ExtendedAsyncSAEngine) -> None:
        async with parent_only_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec()
            result = await execute_pruner(db_sess, spec)

        assert result.count == 0
        assert result.ids == []

    async def test_prune_with_runtime_condition(
        self, parent_only_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded = await _seed_parents(parent_only_tables)
        # Seed sets terminated_at = now-2h for first 3 terminated rows; rest at now.
        cutoff = datetime.now(UTC) - timedelta(hours=1)

        async with parent_only_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec(
                conditions=[lambda: PrunerTestParentRow.terminated_at < cutoff],
            )
            result = await execute_pruner(db_sess, spec)

        assert result.count == 3
        # The first 3 terminated rows have terminated_at = now-2h.
        assert set(result.ids) == set(seeded["terminated"][:3])

    async def test_prune_with_limit_caps_count(
        self, parent_only_tables: ExtendedAsyncSAEngine
    ) -> None:
        await _seed_parents(parent_only_tables)
        async with parent_only_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec(limit=2)
            result = await execute_pruner(db_sess, spec)

        assert result.count == 2
        assert len(result.ids) == 2

        async with parent_only_tables.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalars(
                sa.select(sa.func.count()).select_from(PrunerTestParentRow)
            )
            assert remaining.one() == 6  # 8 - 2


class TestPrunerCascade:
    """FK cascade behavior."""

    async def _seed_with_children(
        self, db: ExtendedAsyncSAEngine
    ) -> tuple[dict[str, list[UUID]], dict[UUID, list[UUID]]]:
        """Seed parents + 2 children per parent. Return (parents_by_status, children_by_parent)."""
        seeded = await _seed_parents(db)
        children_by_parent: dict[UUID, list[UUID]] = {}
        async with db.begin_session() as db_sess:
            for parent_id in seeded["terminated"] + seeded["active"]:
                child_ids = []
                for i in range(2):
                    cid = uuid.uuid4()
                    db_sess.add(
                        PrunerTestChildRow(
                            id=cid,
                            parent_id=parent_id,
                            name=f"child-{i}",
                        )
                    )
                    child_ids.append(cid)
                children_by_parent[parent_id] = child_ids
        return seeded, children_by_parent

    async def test_cascade_deletes_children_of_pruned_parents(
        self, parent_child_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded, children = await self._seed_with_children(parent_child_tables)

        async with parent_child_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec(cascade=[TestChildCascade()])
            result = await execute_pruner(db_sess, spec)

        assert result.count == 5
        assert set(result.ids) == set(seeded["terminated"])

        # Children of pruned parents are gone; children of active parents remain.
        async with parent_child_tables.begin_readonly_session() as db_sess:
            remaining_children = (
                await db_sess.scalars(sa.select(PrunerTestChildRow.parent_id))
            ).all()
            expected_remaining_parents = set(seeded["active"])
            assert (
                set(remaining_children)
                == {pid for pid in expected_remaining_parents for _ in children[pid]}
                or set(remaining_children) <= expected_remaining_parents
            )

            # Each surviving parent still has its 2 children.
            count = await db_sess.scalars(
                sa.select(sa.func.count()).select_from(PrunerTestChildRow)
            )
            assert count.one() == len(seeded["active"]) * 2

    async def test_cascade_skipped_for_non_terminal_parents(
        self, parent_child_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded, _children = await self._seed_with_children(parent_child_tables)

        async with parent_child_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec(cascade=[TestChildCascade()])
            await execute_pruner(db_sess, spec)

        # Active parents preserved.
        async with parent_child_tables.begin_readonly_session() as db_sess:
            remaining = (await db_sess.scalars(sa.select(PrunerTestParentRow.id))).all()
            assert set(remaining) == set(seeded["active"])

    async def test_no_cascade_with_fk_violation_raises(
        self, parent_child_tables: ExtendedAsyncSAEngine
    ) -> None:
        """Without the cascade, FK constraint blocks the parent DELETE.

        Also verifies that ``execute_pruner`` translates the SQLAlchemy
        ``IntegrityError`` into ``ForeignKeyViolationError`` via
        ``parse_integrity_error``.
        """
        await self._seed_with_children(parent_child_tables)

        with pytest.raises(ForeignKeyViolationError):
            async with parent_child_tables.begin_session() as db_sess:
                spec = TerminatedTestParentPrunerSpec()  # no cascade
                await execute_pruner(db_sess, spec)


class TestPrunerRBAC:
    """RBAC association cleanup driven by entity_type()."""

    async def _seed_with_rbac(
        self, db: ExtendedAsyncSAEngine
    ) -> tuple[dict[str, list[UUID]], dict[UUID, UUID]]:
        """Seed parents + one SESSION RBAC association per parent.

        Returns (parents_by_status, association_id_by_parent_id).
        """
        seeded = await _seed_parents(db)
        assoc_by_parent: dict[UUID, UUID] = {}
        async with db.begin_session() as db_sess:
            for parent_id in seeded["terminated"] + seeded["active"]:
                aid = uuid.uuid4()
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        id=aid,
                        scope_type=ScopeType.GLOBAL,
                        scope_id="global",
                        entity_type=EntityType.SESSION,
                        entity_id=str(parent_id),
                    )
                )
                assoc_by_parent[parent_id] = aid
            # One unrelated row using a different entity_type with the same UUID
            # as a terminated parent — should never be deleted (entity_type filter).
            # Distinct scope_id avoids the (scope_type, scope_id, entity_id) unique constraint.
            unrelated_id = uuid.uuid4()
            db_sess.add(
                AssociationScopesEntitiesRow(
                    id=unrelated_id,
                    scope_type=ScopeType.GLOBAL,
                    scope_id="other-scope",
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(seeded["terminated"][0]),
                )
            )
            assoc_by_parent[uuid.uuid4()] = unrelated_id  # sentinel key for return
        return seeded, assoc_by_parent

    async def test_rbac_cleanup_when_enabled(
        self, parent_with_rbac_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded, _ = await self._seed_with_rbac(parent_with_rbac_tables)

        async with parent_with_rbac_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpecWithRBAC(cascade_rbac=True)
            result = await execute_pruner(db_sess, spec)

        assert result.count == 5

        async with parent_with_rbac_tables.begin_readonly_session() as db_sess:
            # SESSION associations for terminated parents are gone.
            remaining_session_assoc_ids = (
                await db_sess.scalars(
                    sa.select(AssociationScopesEntitiesRow.entity_id).where(
                        AssociationScopesEntitiesRow.entity_type == EntityType.SESSION,
                    )
                )
            ).all()
            assert set(remaining_session_assoc_ids) == {str(pid) for pid in seeded["active"]}

            # The unrelated VFOLDER association — same UUID but different entity_type — is preserved.
            unrelated_count = await db_sess.scalars(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_type == EntityType.VFOLDER)
            )
            assert unrelated_count.one() == 1

    async def test_rbac_skipped_when_disabled(
        self, parent_with_rbac_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded, _ = await self._seed_with_rbac(parent_with_rbac_tables)

        async with parent_with_rbac_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpecWithRBAC(cascade_rbac=False)
            await execute_pruner(db_sess, spec)

        # All SESSION associations preserved (8 — one per parent).
        async with parent_with_rbac_tables.begin_readonly_session() as db_sess:
            count = await db_sess.scalars(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_type == EntityType.SESSION)
            )
            assert count.one() == len(seeded["terminated"]) + len(seeded["active"])

    async def test_rbac_skipped_when_entity_type_none(
        self, parent_with_rbac_tables: ExtendedAsyncSAEngine
    ) -> None:
        seeded, _ = await self._seed_with_rbac(parent_with_rbac_tables)

        # Default spec returns entity_type=None — RBAC cleanup must be skipped
        # even with cascade_rbac=True (default).
        async with parent_with_rbac_tables.begin_session() as db_sess:
            spec = TerminatedTestParentPrunerSpec()
            result = await execute_pruner(db_sess, spec)

        assert result.count == 5

        async with parent_with_rbac_tables.begin_readonly_session() as db_sess:
            count = await db_sess.scalars(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_type == EntityType.SESSION)
            )
            assert count.one() == len(seeded["terminated"]) + len(seeded["active"])
