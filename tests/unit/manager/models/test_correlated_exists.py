from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.condition_utils import make_correlated_exists
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow


class TestMakeCorrelatedExists:
    def test_correlates_child_query_with_parent(self) -> None:
        correlated_exists = make_correlated_exists(
            child_row=RoutingRow,
            correlate_row=EndpointRow,
            join_predicate=RoutingRow.endpoint == EndpointRow.id,
        )
        condition = correlated_exists([
            lambda: RoutingRow.traffic_ratio > 0,
        ])
        query = sa.select(EndpointRow.id).where(condition())

        sql = str(query.compile(compile_kwargs={"literal_binds": True}))

        assert sql.count("EXISTS") == 1
        assert "routings.endpoint = endpoints.id" in sql
        assert "routings.traffic_ratio > 0" in sql
        assert "FROM routings, endpoints" not in sql
        assert "NOT" not in sql
