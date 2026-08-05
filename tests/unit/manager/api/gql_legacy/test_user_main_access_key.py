"""The legacy user GraphQL types filter and order by the main keypair marker.

``main_access_key`` is no longer a column of ``users``, so a spec that merely
names it resolves against the statement's table and raises. These tests pin
that both spec sets stay usable and reach ``keypairs``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.manager.api.gql_legacy.user import (
    _MAIN_KEYPAIR_ACCESS_KEY,
    User,
    UserNode,
)
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.minilang import FieldSpecItem, OrderSpecItem
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.user import UserRow, users


@dataclass(frozen=True)
class _SpecCase:
    """A spec set together with the statement the loader applies it to."""

    name: str
    statement: sa.Select
    filter_spec: dict[str, FieldSpecItem]
    order_spec: dict[str, OrderSpecItem]


class TestMainAccessKeySpecs:
    @pytest.fixture(autouse=True)
    def registered_tables(self) -> None:
        """Both statements reference mapped entities, which needs every Row imported."""
        ensure_all_tables_registered()

    @pytest.mark.parametrize(
        "case",
        [
            _SpecCase(
                name="user",
                statement=sa.select(users, _MAIN_KEYPAIR_ACCESS_KEY).select_from(users),
                filter_spec=dict(User._queryfilter_fieldspec),
                order_spec=dict(User._queryorder_colmap),
            ),
            _SpecCase(
                name="user-group-scoped",
                statement=sa.select(users, _MAIN_KEYPAIR_ACCESS_KEY).select_from(users),
                filter_spec={
                    key: ("users_" + spec[0], spec[1]) if isinstance(spec[0], str) else spec
                    for key, spec in User._queryfilter_fieldspec.items()
                },
                order_spec={
                    key: ("users_" + spec[0], spec[1]) if isinstance(spec[0], str) else spec
                    for key, spec in User._queryorder_colmap.items()
                },
            ),
            _SpecCase(
                name="user-node",
                statement=sa.select(UserRow),
                filter_spec=dict(UserNode._queryfilter_fieldspec),
                order_spec=dict(UserNode._queryorder_colmap),
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_filtering_reaches_the_marked_keypair(self, case: _SpecCase) -> None:
        query = QueryFilterParser(case.filter_spec).append_filter(
            case.statement, 'main_access_key == "AKTESTMAIN"'
        )

        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "keypairs.is_main" in compiled
        assert "AKTESTMAIN" in compiled

    @pytest.mark.parametrize(
        "case",
        [
            _SpecCase(
                name="user",
                statement=sa.select(users, _MAIN_KEYPAIR_ACCESS_KEY).select_from(users),
                filter_spec=dict(User._queryfilter_fieldspec),
                order_spec=dict(User._queryorder_colmap),
            ),
            _SpecCase(
                name="user-group-scoped",
                statement=sa.select(users, _MAIN_KEYPAIR_ACCESS_KEY).select_from(users),
                filter_spec={
                    key: ("users_" + spec[0], spec[1]) if isinstance(spec[0], str) else spec
                    for key, spec in User._queryfilter_fieldspec.items()
                },
                order_spec={
                    key: ("users_" + spec[0], spec[1]) if isinstance(spec[0], str) else spec
                    for key, spec in User._queryorder_colmap.items()
                },
            ),
            _SpecCase(
                name="user-node",
                statement=sa.select(UserRow),
                filter_spec=dict(UserNode._queryfilter_fieldspec),
                order_spec=dict(UserNode._queryorder_colmap),
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_ordering_reaches_the_marked_keypair(self, case: _SpecCase) -> None:
        query = QueryOrderParser(case.order_spec).append_ordering(
            case.statement, "-main_access_key"
        )

        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY" in compiled
        assert "keypairs.is_main" in compiled
