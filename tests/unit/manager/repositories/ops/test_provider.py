"""Tests for the DB ops wrapper (DBOpsProvider / ReadOps).

These verify observable contracts — the empty-scope constraint, single-row and scoped
batch reads — not internal call wiring.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.errors.repository import EmptyOperationScopeError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Querier
from ai.backend.manager.repositories.ops import DBOpsProvider, ReadOps
from ai.backend.testutils.db import with_tables


class OpsTestParentRow(Base):
    __tablename__ = "test_ops_parent"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    domain_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass(frozen=True)
class ParentDomainScope(OperationScope):
    domain_name: str

    @override
    def to_condition(self) -> QueryCondition:
        return lambda: OpsTestParentRow.domain_name == self.domain_name

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@pytest.fixture
async def ops_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, [OpsTestParentRow]):
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> DBOpsProvider:
    return DBOpsProvider(database_connection)


async def _seed_parents(db: ExtendedAsyncSAEngine, parents: Sequence[tuple[str, str]]) -> list[int]:
    async with db.begin_session() as session:
        rows = [OpsTestParentRow(name=name, domain_name=domain) for name, domain in parents]
        session.add_all(rows)
        await session.flush()
        return [row.id for row in rows]


class TestScopeConstraint:
    async def test_with_scopes_rejects_empty_scopes(self) -> None:
        ops = ReadOps(AsyncMock())  # session is never touched before the guard raises
        querier = BatchQuerier(pagination=NoPagination())
        with pytest.raises(EmptyOperationScopeError):
            await ops.batch_query_with_scopes(sa.select(OpsTestParentRow), querier, [])


class TestQuery:
    async def test_query_returns_the_named_row(
        self,
        provider: DBOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        ops_tables: None,
    ) -> None:
        (parent_id,) = await _seed_parents(database_connection, [("p1", "d1")])

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is not None
        assert fetched.row.name == "p1"
        assert fetched.row.domain_name == "d1"

    async def test_query_returns_none_for_a_missing_row(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=-1))

        assert fetched is None


class TestScopeFiltering:
    async def test_with_scopes_filters_and_global_returns_all(
        self,
        provider: DBOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        ops_tables: None,
    ) -> None:
        await _seed_parents(database_connection, [("a", "d1"), ("b", "d2")])

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
