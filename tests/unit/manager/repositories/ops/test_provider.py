"""Tests for the DB ops wrapper (DBOpsProvider / ReadOps / WriteOps).

These verify observable contracts — the empty-scope constraint, real create/query/
update/purge outcomes, and that dependent inserts carry the resolved dependency — not
internal call wiring.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.errors.repository import EmptySearchScopeError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    CreatorSpec,
    DependentCreatorSpec,
    ExistenceCheck,
    NoPagination,
    Purger,
    Querier,
    QueryCondition,
    SearchScope,
    Updater,
    UpdaterSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, ReadOps
from ai.backend.testutils.db import with_tables


class OpsTestParentRow(Base):  # type: ignore[misc]
    __tablename__ = "test_ops_parent"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    domain_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class OpsTestChildRow(Base):  # type: ignore[misc]
    __tablename__ = "test_ops_child"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("test_ops_parent.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass
class ParentCreatorSpec(CreatorSpec[OpsTestParentRow]):
    name: str
    domain_name: str

    def build_row(self) -> OpsTestParentRow:
        return OpsTestParentRow(name=self.name, domain_name=self.domain_name)


@dataclass
class ParentUpdaterSpec(UpdaterSpec[OpsTestParentRow]):
    new_name: str

    @property
    def row_class(self) -> type[OpsTestParentRow]:
        return OpsTestParentRow

    def build_values(self) -> dict[str, Any]:
        return {"name": self.new_name}

    @override
    def guard_condition(self) -> QueryCondition | None:
        return None

    @override
    def not_found_error(self) -> BackendAIError | None:
        return None

    @override
    def on_guard_failure(self) -> BackendAIError | None:
        return None


@dataclass(frozen=True)
class ChildDependency:
    parent_id: int


@dataclass
class ChildDependentCreatorSpec(DependentCreatorSpec[ChildDependency, OpsTestChildRow]):
    label: str

    def build_row(self, dependency: ChildDependency) -> OpsTestChildRow:
        return OpsTestChildRow(parent_id=dependency.parent_id, label=self.label)


@dataclass(frozen=True)
class ParentDomainScope(SearchScope):
    domain_name: str

    def to_condition(self) -> QueryCondition:
        return lambda: OpsTestParentRow.domain_name == self.domain_name

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@pytest.fixture
async def ops_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, [OpsTestParentRow, OpsTestChildRow]):
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> DBOpsProvider:
    return DBOpsProvider(database_connection)


class TestScopeConstraint:
    async def test_with_scopes_rejects_empty_scopes(self) -> None:
        ops = ReadOps(AsyncMock())  # session is never touched before the guard raises
        querier = BatchQuerier(pagination=NoPagination())
        with pytest.raises(EmptySearchScopeError):
            await ops.batch_query_with_scopes(sa.select(OpsTestParentRow), querier, [])


class TestWriteRoundTrip:
    async def test_create_then_query(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
        parent_id = created.row.id

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is not None
        assert fetched.row.name == "p1"
        assert fetched.row.domain_name == "d1"

    async def test_update_reflected(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
            parent_id = created.row.id
            await w.update(Updater(spec=ParentUpdaterSpec(new_name="p2"), pk_value=parent_id))

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is not None
        assert fetched.row.name == "p2"

    async def test_purge_removes(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
            parent_id = created.row.id
            await w.purge(Purger(row_class=OpsTestParentRow, pk_value=parent_id))

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is None


class TestDependentCreate:
    async def test_bulk_create_dependent_carries_parent_id(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.write_ops() as w:
            parent = (
                await w.create(Creator(spec=ParentCreatorSpec(name="p", domain_name="d")))
            ).row
            dependency = ChildDependency(parent_id=parent.id)
            specs = [
                ChildDependentCreatorSpec(label="a"),
                ChildDependentCreatorSpec(label="b"),
            ]
            result = await w.bulk_create_dependent(specs, dependency)

        assert {child.label for child in result.rows} == {"a", "b"}
        assert all(child.parent_id == parent.id for child in result.rows)

    async def test_create_dependent_single(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            parent = (
                await w.create(Creator(spec=ParentCreatorSpec(name="p", domain_name="d")))
            ).row
            dependency = ChildDependency(parent_id=parent.id)
            child = (
                await w.create_dependent(ChildDependentCreatorSpec(label="solo"), dependency)
            ).row

        assert child.parent_id == parent.id
        assert child.label == "solo"


class TestScopeFiltering:
    async def test_with_scopes_filters_and_global_returns_all(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.write_ops() as w:
            await w.create(Creator(spec=ParentCreatorSpec(name="a", domain_name="d1")))
            await w.create(Creator(spec=ParentCreatorSpec(name="b", domain_name="d2")))

        async with provider.read_ops() as r:
            scoped = await r.batch_query_with_scopes(
                sa.select(OpsTestParentRow),
                BatchQuerier(pagination=NoPagination()),
                [ParentDomainScope(domain_name="d1")],
            )
            full = await r.batch_query_in_global(
                sa.select(OpsTestParentRow),
                BatchQuerier(pagination=NoPagination()),
            )

        assert {row[0].domain_name for row in scoped.rows} == {"d1"}
        assert len(full.rows) == 2
