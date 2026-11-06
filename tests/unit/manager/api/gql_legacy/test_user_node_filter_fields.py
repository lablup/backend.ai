"""UserNode filter and order do not read the main access key. (BA-8902)"""

from __future__ import annotations

import pytest

from ai.backend.manager.api.gql_legacy.user import UserNode
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.user.row import UserRow


class TestUserNodeFilterFields:
    def test_a_filter_on_the_main_access_key_is_rejected(self) -> None:
        parser = QueryFilterParser(UserNode._queryfilter_fieldspec)
        with pytest.raises(InvalidAPIParameters):
            parser.parse_filter(UserRow.__table__, 'main_access_key == "AKIAIOSFODNN7EXAMPLE"')

    def test_a_filter_on_the_email_is_accepted(self) -> None:
        parser = QueryFilterParser(UserNode._queryfilter_fieldspec)
        parser.parse_filter(UserRow.__table__, 'email == "user@example.com"')

    def test_an_order_on_the_main_access_key_is_rejected(self) -> None:
        parser = QueryOrderParser(UserNode._queryorder_colmap)
        with pytest.raises(InvalidAPIParameters):
            parser.parse_order(UserRow.__table__, "+main_access_key")
