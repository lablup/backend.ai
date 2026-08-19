"""Unit tests for AppConfigAllowList GraphQL types and schema registration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigAllowListOrderField,
)
from ai.backend.manager.api.gql.app_config_allow_list.types import (
    AppConfigAllowListFilterGQL,
    AppConfigAllowListGQL,
    AppConfigAllowListOrderByGQL,
    AppConfigAllowListOrderFieldGQL,
    AppConfigScopeTypeFilterGQL,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter


class TestAppConfigAllowListGQL:
    def test_from_pydantic_maps_all_fields(self) -> None:
        created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)
        node = AppConfigAllowListNode(
            id=uuid.uuid4(),
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            rank=200,
            created_at=created,
            updated_at=updated,
        )

        gql = AppConfigAllowListGQL.from_pydantic(node)

        assert gql.config_name == "theme"
        assert gql.scope_type == AppConfigScopeType.DOMAIN
        assert gql.rank == 200
        assert gql.created_at == created
        assert gql.updated_at == updated


class TestAppConfigAllowListInputs:
    def test_filter_to_pydantic_string(self) -> None:
        filter_gql = AppConfigAllowListFilterGQL(
            config_name=StringFilter(contains="the"),
            scope_type=None,
            created_at=None,
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.config_name is not None
        assert dto.config_name.contains == "the"

    def test_filter_to_pydantic_scope_type(self) -> None:
        filter_gql = AppConfigAllowListFilterGQL(
            config_name=None,
            scope_type=AppConfigScopeTypeFilterGQL(equals=AppConfigScopeType.USER),
            created_at=None,
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.scope_type is not None
        assert dto.scope_type.equals == AppConfigScopeType.USER

    def test_filter_to_pydantic_datetime(self) -> None:
        after = datetime(2026, 1, 1, tzinfo=UTC)
        filter_gql = AppConfigAllowListFilterGQL(
            config_name=None,
            scope_type=None,
            created_at=DateTimeFilter(after=after),
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.created_at is not None
        assert dto.created_at.after == after

    def test_order_by_to_pydantic(self) -> None:
        order_gql = AppConfigAllowListOrderByGQL(
            field=AppConfigAllowListOrderFieldGQL.SCOPE_TYPE,
            direction=OrderDirection.DESC,
        )

        dto = order_gql.to_pydantic()

        assert dto.field == AppConfigAllowListOrderField.SCOPE_TYPE
        assert dto.direction.value == OrderDirection.DESC.value
