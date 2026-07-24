"""Unit tests for AppConfigFragment GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
)
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.gql.app_config_fragment.types import (
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigFragmentScopeGQL,
    AppConfigScopeTypeFilterGQL,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL


class TestAppConfigFragmentGQL:
    def test_from_pydantic_maps_all_fields(self) -> None:
        created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)
        scope_id = uuid.uuid4()
        node = AppConfigFragmentNode(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id=AppConfigScopeID(scope_id),
            config={"k": "v"},
            created_at=created,
            updated_at=updated,
        )

        gql = AppConfigFragmentGQL.from_pydantic(node)

        assert gql.config_name == "theme"
        assert gql.scope_type == AppConfigScopeType.DOMAIN
        assert gql.scope_id == scope_id
        assert gql.config == {"k": "v"}
        assert gql.created_at == created
        assert gql.updated_at == updated

    def test_from_pydantic_maps_public_scope_id_as_none(self) -> None:
        node = AppConfigFragmentNode(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id=None,
            config={},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        gql = AppConfigFragmentGQL.from_pydantic(node)

        assert gql.scope_type == AppConfigScopeType.PUBLIC
        assert gql.scope_id is None


class TestAppConfigFragmentInputs:
    def test_scope_to_pydantic_domain(self) -> None:
        domain_id = uuid.uuid4()
        scope_gql = AppConfigFragmentScopeGQL(
            domain=[UUIDScopeGQL(value=domain_id)],
            user=None,
            public=None,
        )

        dto = scope_gql.to_pydantic()

        assert dto.domain is not None
        assert dto.domain[0].value == domain_id

    def test_scope_to_pydantic_public(self) -> None:
        scope_gql = AppConfigFragmentScopeGQL(domain=None, user=None, public=True)

        dto = scope_gql.to_pydantic()

        assert dto.public is True

    def test_filter_to_pydantic_string(self) -> None:
        filter_gql = AppConfigFragmentFilterGQL(
            config_name=StringFilter(contains="the"),
            scope_type=None,
            created_at=None,
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.config_name is not None
        assert dto.config_name.contains == "the"

    def test_filter_to_pydantic_scope_type(self) -> None:
        filter_gql = AppConfigFragmentFilterGQL(
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
        filter_gql = AppConfigFragmentFilterGQL(
            config_name=None,
            scope_type=None,
            created_at=DateTimeFilter(after=after),
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.created_at is not None
        assert dto.created_at.after == after

    def test_order_by_to_pydantic(self) -> None:
        order_gql = AppConfigFragmentOrderByGQL(
            field=AppConfigFragmentOrderFieldGQL.SCOPE_TYPE,
            direction=OrderDirection.DESC,
        )

        dto = order_gql.to_pydantic()

        assert dto.field == AppConfigFragmentOrderField.SCOPE_TYPE
        assert dto.direction.value == OrderDirection.DESC.value
