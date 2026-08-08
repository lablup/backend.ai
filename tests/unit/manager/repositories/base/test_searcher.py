"""Integration tests for searcher with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, override
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.data.role_preset.types import (
    RolePresetData,
    RolePresetSearchResult,
)
from ai.backend.manager.errors.repository import EmptySearchScopeError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.repositories.base import (
    OffsetPagination,
    Searcher,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Fixtures shared by the searcher behavior tests
# =============================================================================


@dataclass(frozen=True)
class ItemData:
    """`data/` type the searcher converts rows into."""

    id: int
    name: str
    category: str


class ItemRow(Base):
    """ORM model for searcher testing."""

    __tablename__ = "test_searcher_item"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(50), nullable=False)

    def to_data(self) -> ItemData:
        return ItemData(id=self.id, name=self.name, category=self.category)


@dataclass
class ItemSearcher(Searcher[ItemRow, ItemData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ItemRow)

    @override
    def to_data(self, row: Row[Any]) -> ItemData:
        item_row: ItemRow = row.ItemRow
        return item_row.to_data()


@dataclass(frozen=True)
class CategoryScope(SearchScope):
    """SearchScope restricting rows to a single category."""

    category: str
    checks: Sequence[ExistenceCheck[Any]] = field(default_factory=tuple)

    @override
    def to_condition(self) -> QueryCondition:
        category = self.category

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ItemRow.category == category

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return self.checks


class TestSearcher:
    """Tests for executing a searcher against a real database."""

    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [ItemRow]):
            yield database_connection

    @pytest.fixture
    async def sample_items(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[dict[str, int | str]], None]:
        data: list[dict[str, int | str]] = [
            {"id": 1, "name": "item-a", "category": "cat1"},
            {"id": 2, "name": "item-b", "category": "cat1"},
            {"id": 3, "name": "item-c", "category": "cat2"},
            {"id": 4, "name": "item-d", "category": "cat2"},
            {"id": 5, "name": "item-e", "category": "cat3"},
        ]

        async with database.begin_session() as db_sess:
            await db_sess.execute(sa.insert(ItemRow), data)

        yield data

    @pytest.fixture
    def ops(self, database: ExtendedAsyncSAEngine) -> DBOpsProvider:
        return DBOpsProvider(database)

    async def test_returns_data_instead_of_rows(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """The searcher converts every fetched row, so no ORM row is returned."""
        async with ops.read_ops() as r:
            result = await r.search_in_global(
                ItemSearcher(pagination=OffsetPagination(offset=0, limit=10)),
            )

            assert [item.name for item in result.items] == [
                "item-a",
                "item-b",
                "item-c",
                "item-d",
                "item-e",
            ]
            assert all(isinstance(item, ItemData) for item in result.items)

    async def test_applies_conditions(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """Conditions carried by the searcher filter the result."""
        async with ops.read_ops() as r:
            result = await r.search_in_global(
                ItemSearcher(
                    pagination=OffsetPagination(offset=0, limit=10),
                    conditions=[lambda: ItemRow.category == "cat1"],
                ),
            )

            assert {item.name for item in result.items} == {"item-a", "item-b"}
            assert result.total_count == 2

    async def test_applies_orders(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """Orders carried by the searcher sort the result."""
        async with ops.read_ops() as r:
            result = await r.search_in_global(
                ItemSearcher(
                    pagination=OffsetPagination(offset=0, limit=10),
                    orders=[ItemRow.name.desc()],
                ),
            )

            assert [item.name for item in result.items] == [
                "item-e",
                "item-d",
                "item-c",
                "item-b",
                "item-a",
            ]

    async def test_reports_pagination_info(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """Page flags and total_count describe the whole match set, not the page."""
        async with ops.read_ops() as r:
            result = await r.search_in_global(
                ItemSearcher(pagination=OffsetPagination(offset=2, limit=2)),
            )

            assert len(result.items) == 2
            assert result.total_count == 5
            assert result.has_next_page is True
            assert result.has_previous_page is True

    async def test_scopes_restrict_the_result(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """Scopes are applied exactly as they are for a batch query."""
        async with ops.read_ops() as r:
            result = await r.search_with_scopes(
                [CategoryScope(category="cat1"), CategoryScope(category="cat3")],
                ItemSearcher(pagination=OffsetPagination(offset=0, limit=10)),
            )

            assert {item.name for item in result.items} == {"item-a", "item-b", "item-e"}
            assert result.total_count == 3

    async def test_rejects_empty_scopes(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """An empty scope list would degrade into an unscoped scan, so it is refused."""
        async with ops.read_ops() as r:
            with pytest.raises(EmptySearchScopeError):
                await r.search_with_scopes(
                    [],
                    ItemSearcher(pagination=OffsetPagination(offset=0, limit=10)),
                )

    async def test_global_search_applies_no_scope_filter(
        self,
        ops: DBOpsProvider,
        sample_items: list[dict[str, int | str]],
    ) -> None:
        """The global path returns rows from every category."""
        async with ops.read_ops() as r:
            result = await r.search_in_global(
                ItemSearcher(pagination=OffsetPagination(offset=0, limit=10)),
            )

            assert {item.category for item in result.items} == {"cat1", "cat2", "cat3"}
            assert result.total_count == 5


# =============================================================================
# Wiring a pass-through domain on the searcher
# =============================================================================


@dataclass
class RolePresetSearcher(Searcher[RolePresetRow, RolePresetData]):
    """The searcher `role_preset` would own once it moves onto this foundation."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RolePresetRow)

    @override
    def to_data(self, row: Row[Any]) -> RolePresetData:
        preset_row: RolePresetRow = row.RolePresetRow
        return preset_row.to_data()


class TestPassThroughDomainWiring:
    """`role_preset.search` — a pass-through search — rebuilt on the searcher."""

    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [RolePresetRow]):
            yield database_connection

    @pytest.fixture
    async def sample_presets(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[RolePresetID], None]:
        preset_ids = [RolePresetID(uuid4()) for _ in range(3)]
        async with database.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RolePresetRow),
                [
                    {
                        "id": preset_ids[0],
                        "name": "domain-admin",
                        "scope_type": ScopeType.DOMAIN,
                        "auto_assign": False,
                        "deleted": False,
                    },
                    {
                        "id": preset_ids[1],
                        "name": "project-member",
                        "scope_type": ScopeType.PROJECT,
                        "auto_assign": True,
                        "deleted": False,
                    },
                    {
                        "id": preset_ids[2],
                        "name": "retired",
                        "scope_type": ScopeType.PROJECT,
                        "auto_assign": False,
                        "deleted": True,
                    },
                ],
            )

        yield preset_ids

    async def test_search_collapses_to_a_single_ops_call(
        self,
        database: ExtendedAsyncSAEngine,
        sample_presets: list[RolePresetID],
    ) -> None:
        """The whole db_source.search body is one ops call plus the result wrapper."""
        ops = DBOpsProvider(database)
        searcher = RolePresetSearcher(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[lambda: RolePresetRow.deleted.is_(False)],
            orders=[RolePresetRow.name.asc()],
        )

        async with ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        search_result = RolePresetSearchResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

        assert [preset.name for preset in search_result.items] == [
            "domain-admin",
            "project-member",
        ]
        assert search_result.items[0].id == sample_presets[0]
        assert search_result.items[0].scope_type == ScopeType.DOMAIN.to_element()
        assert search_result.items[1].auto_assign is True
        assert search_result.total_count == 2
        assert search_result.has_next_page is False
        assert search_result.has_previous_page is False
