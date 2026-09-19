from __future__ import annotations

import uuid
from collections.abc import Callable

import sqlalchemy as sa

from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.usage import UsageConditions

type Render = Callable[[sa.sql.ClauseElement], str]


class TestUsageConditions:
    def test_used_by_matches_rows_the_entity_uses(
        self, items_table: sa.Table, tags_table: sa.Table, render: Render
    ) -> None:
        usage = UsageConditions(
            ToManyCorrelation(tags_table, items_table, tags_table.c.item_id == items_table.c.id),
            tags_table.c.key,
        )
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        condition = usage.used_by(user_id)

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id "
            "AND tags.key = '00000000-0000-0000-0000-000000000001')"
        )
