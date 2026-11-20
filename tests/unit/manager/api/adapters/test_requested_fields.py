"""An adapter turns requested data field names into the columns a partial searcher reads."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, cast, override

import pytest
import sqlalchemy as sa
from pydantic import ConfigDict
from strawberry import Info, Schema
from strawberry.relay import Connection, NodeID
from strawberry.tools import create_type

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.partial import PartialRecord, selectable
from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapter_options.requested_fields.requested_fields import (
    RequestedFields,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.api.gql.decorators import (
    gql_added_field,
    gql_added_resolver,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.requested_fields import RequestedFieldReader
from ai.backend.manager.api.gql.schema_config import GQLSchemaConfig
from ai.backend.manager.errors.api import RequestedFieldNotDeclared
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.pagination import CursorForwardPagination
from ai.backend.manager.models.specs.search.field import QueryColumn
from ai.backend.manager.models.specs.search.query_spec import QueryOwnSection, QuerySpec
from ai.backend.manager.models.specs.searcher import PartialSearcher

META = BackendAIGQLMeta(added_version="26.9.0", description="Probe.")


class _PresetOwnColumns(QueryOwnSection):
    id = QueryColumn(
        ResourcePresetRow.id,
        UUIDConditions(ResourcePresetRow.id),
        ColumnOrder(ResourcePresetRow.id),
    )
    name = QueryColumn(
        ResourcePresetRow.name,
        StringConditions(ResourcePresetRow.name),
        ColumnOrder(ResourcePresetRow.name),
    )
    shared_memory = QueryColumn(ResourcePresetRow.shared_memory, None, None)
    resource_group_name = QueryColumn(
        ResourcePresetRow.scaling_group_name,
        StringConditions(ResourcePresetRow.scaling_group_name),
        ColumnOrder(ResourcePresetRow.scaling_group_name),
    )


class _PresetQuerySpec(QuerySpec):
    own = _PresetOwnColumns()


class _PresetPartialData(PartialRecord):
    id: uuid.UUID
    name: str = selectable()
    shared_memory: int | None = selectable()
    resource_group_name: str | None = selectable()


@dataclass
class _PresetPartialSearcher(PartialSearcher[ResourcePresetRow, _PresetPartialData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourcePresetRow)

    @override
    def to_data(self, row: ResourcePresetRow) -> _PresetPartialData:
        return _PresetPartialData(
            id=row.id,
            name=row.name,
            shared_memory=row.shared_memory,
            resource_group_name=row.scaling_group_name,
        )

    @override
    def id_column(self) -> QueryColumn[Any, Any, Any]:
        return _PresetQuerySpec.own.id

    @override
    def partial_class(self) -> type[_PresetPartialData]:
        return _PresetPartialData


class _PresetNodeDTO(BaseResponseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    name: str | Unset = UNSET
    shared_memory: int | None | Unset = UNSET
    resource_group_name: str | None | Unset = UNSET


class _PresetProbeAdapter(BaseAdapter):
    def searcher(self, requested: RequestedFields | None) -> _PresetPartialSearcher:
        return self._build_partial_searcher(
            _PresetPartialSearcher,
            _PresetQuerySpec.own,
            requested,
            conditions=[],
            orders=[],
            pagination_spec=PaginationSpec(
                forward_order=ResourcePresetRow.name.asc(),
                cursor_column=ResourcePresetRow.id,
            ),
            first=10,
        )

    def to_node(self, data: _PresetPartialData) -> _PresetNodeDTO:
        return _PresetNodeDTO(
            id=data.id,
            entity_id=data.id,
            name=data.or_missing(lambda: data.name),
            shared_memory=data.or_missing(lambda: data.shared_memory),
            resource_group_name=data.or_missing(lambda: data.resource_group_name),
        )


@gql_node_type(META, name="PresetProbe")
class _PresetGQL(PydanticNodeMixin[_PresetNodeDTO]):
    id: NodeID[str]
    entity_id: uuid.UUID = gql_added_field(META)
    name: str = gql_field(description="Name.")
    shared_memory: int | None = gql_field(description="Shared memory.")
    resource_group_name: str | None = gql_field(description="Resource group name.")

    @gql_added_resolver(META, reads=[resource_group_name])
    async def resource_group(self) -> str | None:
        return self.resource_group_name


@gql_connection_type(META, name="PresetProbeConnection")
class _PresetConnection(Connection[_PresetGQL]):
    pass


@gql_root_field(META)
async def preset_probes(info: Info) -> _PresetConnection | None:
    requested = RequestedFieldReader(info).connection_node_fields(_PresetGQL)
    info.context["searcher"] = _PresetProbeAdapter().searcher(requested)
    return None


def _names(searcher: _PresetPartialSearcher) -> list[str] | None:
    return None if searcher.fields is None else [column.name for column in searcher.fields]


class TestRequestedFieldsColumns:
    def test_names_map_to_own_columns_in_declaration_order(self) -> None:
        requested = RequestedFields(names=frozenset({"resource_group_name", "id", "name"}))
        own = _PresetQuerySpec.own
        assert requested.columns(own) == [own.id, own.name, own.resource_group_name]

    def test_no_names_map_to_no_columns(self) -> None:
        assert RequestedFields(names=frozenset()).columns(_PresetQuerySpec.own) == []

    def test_a_name_without_a_column_is_rejected(self) -> None:
        requested = RequestedFields(names=frozenset({"name", "resource_slots"}))
        with pytest.raises(RequestedFieldNotDeclared):
            requested.columns(_PresetQuerySpec.own)


class TestBuildPartialSearcher:
    def test_fields_hold_the_requested_columns(self) -> None:
        searcher = _PresetProbeAdapter().searcher(RequestedFields(names=frozenset({"name"})))
        assert _names(searcher) == ["name"]
        assert isinstance(searcher.pagination, CursorForwardPagination)

    def test_no_request_reads_every_field(self) -> None:
        assert _PresetProbeAdapter().searcher(None).fields is None


class TestGQLSelectionToSearcher:
    @pytest.fixture(scope="class")
    def probe_schema(self) -> Schema:
        return Schema(
            query=create_type("Query", [cast(Any, preset_probes)]),
            config=GQLSchemaConfig(auto_camel_case=True),
        )

    async def test_searcher_fields_hold_only_the_selected_fields(
        self, probe_schema: Schema
    ) -> None:
        context: dict[str, Any] = {}
        result = await probe_schema.execute(
            "{ presetProbes { edges { node { id name resourceGroup } } } }",
            context_value=context,
        )
        assert result.errors is None
        assert _names(context["searcher"]) == ["id", "name", "resource_group_name"]

    def test_node_json_holds_the_selected_fields_and_the_id(self) -> None:
        preset_id = uuid.uuid4()
        partial = _PresetPartialData(id=preset_id, name="small", resource_group_name=None)
        node = _PresetProbeAdapter().to_node(partial)
        assert node.model_dump(mode="json") == {
            "id": str(preset_id),
            "entity_id": str(preset_id),
            "name": "small",
            "resource_group_name": None,
        }
