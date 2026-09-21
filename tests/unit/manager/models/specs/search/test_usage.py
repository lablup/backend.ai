from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.usage import UsedByConditions, UsesConditions

type Render = Callable[[sa.sql.ClauseElement], str]

_OTHER_ID = DomainID(uuid.UUID("00000000-0000-0000-0000-000000000001"))

_EXPECTED_SQL = (
    "SELECT items.id FROM items WHERE EXISTS (SELECT 1 AS anon_1 FROM users "
    "WHERE users.item_id = items.id "
    "AND users.domain_id = '00000000-0000-0000-0000-000000000001')"
)


@pytest.fixture
def users_table() -> sa.Table:
    """Rows naming the ``items`` row they use and the domain using it."""
    return sa.Table(
        "users",
        sa.MetaData(),
        sa.Column("item_id", sa.Uuid),
        sa.Column("domain_id", sa.Uuid),
    )


@pytest.fixture
def correlation(items_table: sa.Table, users_table: sa.Table) -> ToManyCorrelation:
    return ToManyCorrelation(users_table, items_table, users_table.c.item_id == items_table.c.id)


class TestUsedByConditions:
    """The searched side is the used one, narrowed by the using entity's id."""

    @pytest.fixture
    def usage(
        self, correlation: ToManyCorrelation, users_table: sa.Table
    ) -> UsedByConditions[DomainID]:
        return UsedByConditions[DomainID](correlation, users_table.c.domain_id)

    def test_used_by_names_the_using_entity(self, usage: UsedByConditions[DomainID]) -> None:
        assert usage.used_by(_OTHER_ID).target == _OTHER_ID

    def test_used_by_matches_rows_the_entity_uses(
        self, items_table: sa.Table, usage: UsedByConditions[DomainID], render: Render
    ) -> None:
        condition = usage.used_by(_OTHER_ID).condition

        assert render(sa.select(items_table.c.id).where(condition())) == _EXPECTED_SQL

    def test_the_other_direction_is_not_reachable(self, usage: UsedByConditions[DomainID]) -> None:
        assert not hasattr(usage, "uses")


class TestUsesConditions:
    """The searched side is the using one, narrowed by the used entity's id."""

    @pytest.fixture
    def usage(
        self, correlation: ToManyCorrelation, users_table: sa.Table
    ) -> UsesConditions[DomainID]:
        return UsesConditions[DomainID](correlation, users_table.c.domain_id)

    def test_uses_names_the_used_entity(self, usage: UsesConditions[DomainID]) -> None:
        assert usage.uses(_OTHER_ID).target == _OTHER_ID

    def test_uses_matches_rows_using_the_entity(
        self, items_table: sa.Table, usage: UsesConditions[DomainID], render: Render
    ) -> None:
        condition = usage.uses(_OTHER_ID).condition

        assert render(sa.select(items_table.c.id).where(condition())) == _EXPECTED_SQL

    def test_the_other_direction_is_not_reachable(self, usage: UsesConditions[DomainID]) -> None:
        assert not hasattr(usage, "used_by")
