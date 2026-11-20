"""A GQL resolver reads the data field names its selection requests on a node type."""

from __future__ import annotations

import uuid
from typing import Any, cast

import pytest
from pydantic import BaseModel
from strawberry import Info, Schema
from strawberry.relay import Connection, Edge, NodeID
from strawberry.tools import create_type
from strawberry.types.base import get_object_definition

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.manager.api.adapter_options.requested_fields.requested_fields import (
    RequestedFields,
)
from ai.backend.manager.api.gql.decorators import (
    gql_added_field,
    gql_added_resolver,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_type,
    gql_resolver,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.requested_fields import RequestedFieldReader
from ai.backend.manager.api.gql.schema_config import GQLSchemaConfig
from ai.backend.manager.errors.api import InvalidResolverReads

META = BackendAIGQLMeta(added_version="26.9.0", description="Probe.")


class _SizeDTO(BaseModel):
    bytes: int
    display: str


class _ProbeNodeDTO(BaseResponseModel):
    id: uuid.UUID
    entity_id: uuid.UUID
    name: str
    group_name: str | None
    shared_memory: _SizeDTO | None


@gql_pydantic_type(META, model=_SizeDTO, name="ProbeSize")
class _SizeGQL(PydanticOutputMixin[_SizeDTO]):
    bytes: int = gql_field(description="Bytes.")
    display: str = gql_field(description="Display.")


@gql_node_type(META, name="ProbeNode")
class _ProbeNodeGQL(PydanticNodeMixin[_ProbeNodeDTO]):
    id: NodeID[str]
    entity_id: uuid.UUID = gql_added_field(META)
    name: str = gql_field(description="Name.")
    group_name: str | None = gql_field(description="Group name.")
    shared_memory: _SizeGQL | None = gql_field(description="Shared memory.")

    @gql_added_resolver(META, reads=[group_name])
    async def group(self) -> str | None:
        return self.group_name

    @gql_resolver(description="Name and group.", reads=[name, group_name])
    async def label(self) -> str:
        return f"{self.name}/{self.group_name}"

    @gql_resolver(description="Reads only the id.")
    async def link(self) -> str:
        return self.id


@gql_connection_type(META, name="ProbeNodeEdge")
class _ProbeNodeEdge(Edge[_ProbeNodeGQL]):
    pass


@gql_connection_type(META, name="ProbeNodeConnection")
class _ProbeNodeConnection(Connection[_ProbeNodeGQL]):
    count: int = gql_field(description="Count.")


@gql_node_type(META, name="OtherProbeNode")
class _OtherProbeNodeGQL(PydanticNodeMixin[_ProbeNodeDTO]):
    id: NodeID[str]
    entity_id: uuid.UUID = gql_added_field(META)

    @gql_resolver(
        description="Reads a field of ProbeNode.",
        reads=[
            next(
                field
                for field in get_object_definition(_ProbeNodeGQL, strict=True).fields
                if field.python_name == "name"
            )
        ],
    )
    async def borrowed(self) -> str:
        return ""


@gql_root_field(META)
async def other_probe_node(info: Info) -> _OtherProbeNodeGQL | None:
    RequestedFieldReader(info).node_fields(_OtherProbeNodeGQL)
    return None


@gql_root_field(META)
async def probe_node(info: Info) -> _ProbeNodeGQL | None:
    info.context["requested"] = RequestedFieldReader(info).node_fields(_ProbeNodeGQL)
    return None


@gql_root_field(META)
async def probe_nodes(info: Info) -> _ProbeNodeConnection | None:
    reader = RequestedFieldReader(info)
    info.context["requested"] = reader.connection_node_fields(_ProbeNodeGQL)
    return None


@pytest.fixture(scope="module")
def probe_schema() -> Schema:
    return Schema(
        query=create_type(
            "Query", [cast(Any, probe_node), cast(Any, probe_nodes), cast(Any, other_probe_node)]
        ),
        config=GQLSchemaConfig(auto_camel_case=True),
    )


async def _requested(probe_schema: Schema, query: str) -> RequestedFields:
    context: dict[str, Any] = {}
    result = await probe_schema.execute(query, context_value=context)
    assert result.errors is None
    return cast(RequestedFields, context["requested"])


class TestNodeFields:
    async def test_plain_fields_map_to_their_snake_case_names(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNode { name groupName } }")
        assert requested.names == {"name", "group_name"}

    async def test_id_and_entity_id_map_to_id(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNode { id entityId } }")
        assert requested.names == {"id"}

    async def test_a_resolver_field_maps_to_the_fields_it_reads(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNode { group label } }")
        assert requested.names == {"name", "group_name"}

    async def test_a_resolver_field_without_reads_adds_nothing(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNode { link } }")
        assert requested.names == frozenset()

    async def test_an_object_field_maps_to_itself_not_to_its_subfields(
        self, probe_schema: Schema
    ) -> None:
        requested = await _requested(probe_schema, "{ probeNode { sharedMemory { bytes } } }")
        assert requested.names == {"shared_memory"}

    async def test_fragments_and_aliases_are_expanded(self, probe_schema: Schema) -> None:
        query = """
            { probeNode { renamed: name ...Group ... on ProbeNode { sharedMemory { display } }
                          ... on Node { id } } }
            fragment Group on ProbeNode { groupName ... on ProbeNode { name } }
        """
        requested = await _requested(probe_schema, query)
        assert requested.names == {"name", "group_name", "shared_memory", "id"}

    async def test_typename_adds_nothing(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNode { __typename } }")
        assert requested.names == frozenset()


class TestConnectionNodeFields:
    async def test_only_the_node_selection_under_edges_is_read(self, probe_schema: Schema) -> None:
        query = "{ probeNodes { count pageInfo { hasNextPage } edges { cursor node { name } } } }"
        requested = await _requested(probe_schema, query)
        assert requested.names == {"name"}

    async def test_edges_in_fragments_and_aliases_are_merged(self, probe_schema: Schema) -> None:
        query = """
            { probeNodes { first: edges { node { name } } ...Edges } }
            fragment Edges on ProbeNodeConnection { edges { node { ... on ProbeNode { group } } } }
        """
        requested = await _requested(probe_schema, query)
        assert requested.names == {"name", "group_name"}

    async def test_a_connection_without_edges_requests_nothing(self, probe_schema: Schema) -> None:
        requested = await _requested(probe_schema, "{ probeNodes { count } }")
        assert requested.names == frozenset()


class TestResolverReadsDeclaration:
    def test_reads_rejects_a_resolver_field(self) -> None:
        resolver_field = gql_resolver(description="A resolver.")(lambda: "x")
        with pytest.raises(InvalidResolverReads):
            gql_resolver(description="Reads a resolver.", reads=[resolver_field])

    def test_reads_rejects_a_value_that_is_not_a_field(self) -> None:
        with pytest.raises(InvalidResolverReads):
            gql_added_resolver(META, reads=["group_name"])

    async def test_reads_of_another_type_is_rejected_when_read(self, probe_schema: Schema) -> None:
        result = await probe_schema.execute("{ otherProbeNode { borrowed } }", context_value={})
        assert result.errors is not None
        assert isinstance(result.errors[0].original_error, InvalidResolverReads)
