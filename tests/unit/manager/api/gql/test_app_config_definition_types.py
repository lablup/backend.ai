"""Unit tests for AppConfigDefinition GraphQL types and schema registration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.common.dto.manager.v2.app_config_definition.types import (
    AppConfigDefinitionOrderField,
)
from ai.backend.manager.api.gql.app_config_definition.types import (
    AppConfigDefinitionFilterGQL,
    AppConfigDefinitionGQL,
    AppConfigDefinitionOrderByGQL,
    AppConfigDefinitionOrderFieldGQL,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.schema import schema


class TestAppConfigDefinitionGQL:
    def test_from_pydantic_maps_all_fields(self) -> None:
        created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)
        node = AppConfigDefinitionNode(
            id=uuid.uuid4(),
            config_name="theme",
            created_at=created,
            updated_at=updated,
        )

        gql = AppConfigDefinitionGQL.from_pydantic(node)

        assert gql.config_name == "theme"
        assert gql.created_at == created
        assert gql.updated_at == updated


class TestAppConfigDefinitionInputs:
    def test_filter_to_pydantic_string(self) -> None:
        filter_gql = AppConfigDefinitionFilterGQL(
            config_name=StringFilter(contains="the"),
            created_at=None,
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.config_name is not None
        assert dto.config_name.contains == "the"

    def test_filter_to_pydantic_datetime(self) -> None:
        after = datetime(2026, 1, 1, tzinfo=UTC)
        filter_gql = AppConfigDefinitionFilterGQL(
            config_name=None,
            created_at=DateTimeFilter(after=after),
            updated_at=None,
        )

        dto = filter_gql.to_pydantic()

        assert dto.created_at is not None
        assert dto.created_at.after == after

    def test_order_by_to_pydantic(self) -> None:
        order_gql = AppConfigDefinitionOrderByGQL(
            field=AppConfigDefinitionOrderFieldGQL.CONFIG_NAME,
            direction=OrderDirection.DESC,
        )

        dto = order_gql.to_pydantic()

        assert dto.field == AppConfigDefinitionOrderField.CONFIG_NAME
        assert dto.direction.value == OrderDirection.DESC.value


class TestSchemaRegistration:
    def test_types_and_root_fields_present_in_schema(self) -> None:
        sdl = schema.as_str()
        assert "type AppConfigDefinition " in sdl
        assert "appConfigDefinition(" in sdl
        assert "appConfigDefinitions(" in sdl
        assert "adminCreateAppConfigDefinition(" in sdl
        assert "adminPurgeAppConfigDefinition(" in sdl
