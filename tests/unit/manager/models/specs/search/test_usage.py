from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.usage import UsageConditions

type Render = Callable[[sa.sql.ClauseElement], str]

_USING_ID = DomainID(uuid.UUID("00000000-0000-0000-0000-000000000001"))


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
def usage(items_table: sa.Table, users_table: sa.Table) -> UsageConditions[DomainID]:
    return UsageConditions[DomainID](
        ToManyCorrelation(users_table, items_table, users_table.c.item_id == items_table.c.id),
        users_table.c.domain_id,
    )


class TestUsageConditions:
    def test_used_by_names_the_using_entity(self, usage: UsageConditions[DomainID]) -> None:
        assert usage.used_by(_USING_ID).target == _USING_ID

    def test_used_by_matches_rows_the_entity_uses(
        self, items_table: sa.Table, usage: UsageConditions[DomainID], render: Render
    ) -> None:
        condition = usage.used_by(_USING_ID).condition

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE EXISTS (SELECT 1 AS anon_1 FROM users "
            "WHERE users.item_id = items.id "
            "AND users.domain_id = '00000000-0000-0000-0000-000000000001')"
        )
