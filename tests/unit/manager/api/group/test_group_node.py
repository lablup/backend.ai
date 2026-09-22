"""
Tests for Group GraphQL mutation response serialization.
Tests allowed_vfolder_hosts JSON serialization in CreateGroup mutation.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import graphene
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from graphene.types import inputobjecttype
from graphql import GraphQLInputObjectType, Undefined, coerce_input_value

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import (
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult
from ai.backend.manager.api.gql_legacy.base import DataLoaderManager
from ai.backend.manager.api.gql_legacy.group import (
    CreateGroup,
    Group,
    GroupNode,
    ModifyGroupInput,
)
from ai.backend.manager.data.container_registry.types import ImageCommitRegistry
from ai.backend.manager.data.project.types import ProjectData, ProjectType
from ai.backend.manager.models.user import UserRole


class TestCreateGroupMutation:
    """Tests for CreateGroup GraphQL mutation response serialization."""

    CREATE_GROUP_MUTATION = """
        mutation CreateGroup($name: String!, $props: GroupInput!) {
            createGroup(name: $name, props: $props) {
                ok
                msg
                group {
                    id
                    name
                    allowedVfolderHosts
                }
            }
        }
    """

    @pytest.fixture
    def group_data_response(self) -> ProjectData:
        """ProjectData returned from CreateGroup action."""
        return ProjectData(
            id=uuid4(),
            name="test-group",
            description="Test group",
            is_active=True,
            created_at=datetime.now(tz=UTC),
            modified_at=datetime.now(tz=UTC),
            domain_name="default",
            total_resource_slots=ResourceSlot({}),
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                "local:volume1": {VFolderHostPermission.CREATE, VFolderHostPermission.MODIFY},
            }),
            dotfiles=b"",
            resource_policy="default",
            type=ProjectType.GENERAL,
            integration_name=None,
            container_registry=None,
        )

    @pytest.fixture
    def mock_graph_ctx(self, group_data_response: ProjectData) -> MagicMock:
        """GraphQueryContext mock with processors and user context."""

        ctx = MagicMock()
        ctx.processors.project.create_project.run = AsyncMock(
            return_value=CreatedEntityOpsResult(data=group_data_response)
        )
        domain_data = MagicMock()
        domain_data.id = uuid4()
        ctx.processors.domain.lookup.run = AsyncMock(return_value=MagicMock(data=domain_data))
        # Required for privileged_mutation decorator
        ctx.user = {
            "role": UserRole.SUPERADMIN,
            "domain_name": "default",
        }
        return ctx

    @pytest.fixture
    def mutation_schema(self) -> graphene.Schema:
        """Create GraphQL schema with CreateGroup mutation."""

        class Query(graphene.ObjectType):  # type: ignore[misc]
            """Dummy query required by graphene.Schema."""

            ok = graphene.Boolean(default_value=True)

        class Mutation(graphene.ObjectType):  # type: ignore[misc]
            create_group = CreateGroup.Field()

        return graphene.Schema(query=Query, mutation=Mutation)

    @pytest.fixture
    async def graphql_client(
        self,
        aiohttp_client: Any,
        mutation_schema: graphene.Schema,
        mock_graph_ctx: MagicMock,
    ) -> TestClient[Any]:  # type: ignore[type-arg]
        """Create test client with GraphQL endpoint."""

        async def graphql_handler(request: web.Request) -> web.Response:
            """Handle GraphQL POST requests."""
            body = await request.json()
            query = body.get("query", "")
            variables = body.get("variables")
            operation_name = body.get("operationName")

            result = await mutation_schema.execute_async(
                query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=mock_graph_ctx,
            )

            response_data: dict[str, Any] = {}
            if result.data:
                response_data["data"] = result.data
            if result.errors:
                response_data["errors"] = [{"message": str(e)} for e in result.errors]

            return web.json_response(response_data)

        app = web.Application()
        app.router.add_post("/graphql", graphql_handler)

        client: TestClient[Any] = await aiohttp_client(app)  # type: ignore[type-arg]
        return client

    async def test_create_group_response_is_json_serializable(
        self,
        graphql_client: TestClient[Any],  # type: ignore[type-arg]
    ) -> None:
        """CreateGroup mutation response should have JSON-serializable allowed_vfolder_hosts."""
        # Act: Make HTTP POST request to GraphQL endpoint
        resp = await graphql_client.post(
            "/graphql",
            json={
                "query": self.CREATE_GROUP_MUTATION,
                "variables": {
                    "name": "test-group",
                    "props": {
                        "domainName": "default",
                    },
                },
            },
        )

        # Assert: HTTP response should succeed
        assert resp.status == HTTPStatus.OK

        # Assert: Response should be valid JSON (no serialization errors)
        data = await resp.json()

        # Assert: No GraphQL errors
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"

        # Assert: CreateGroup mutation succeeded
        create_group_result = data.get("data", {}).get("createGroup", {})
        allowed_vfolder_hosts = create_group_result.get("group", {}).get("allowedVfolderHosts")
        assert create_group_result.get("ok") is True, f"Unexpected result: {create_group_result}"
        assert allowed_vfolder_hosts is not None and allowed_vfolder_hosts != {}


class TestGroupNodeQuery:
    """Tests for GroupNode GraphQL query response serialization."""

    GROUP_NODE_QUERY = """
        query GetGroup($id: String!) {
            groupNode(id: $id) {
                id
                name
                allowedVfolderHosts
            }
        }
    """

    @pytest.fixture
    def group_data(self) -> ProjectData:
        return ProjectData(
            id=uuid4(),
            name="test-group",
            description="Test group",
            is_active=True,
            created_at=datetime.now(tz=UTC),
            modified_at=datetime.now(tz=UTC),
            domain_name="default",
            total_resource_slots=ResourceSlot({}),
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                "local:volume1": {VFolderHostPermission.CREATE, VFolderHostPermission.MODIFY},
            }),
            integration_name=None,
            container_registry=None,
            resource_policy="default",
            type=ProjectType.GENERAL,
            dotfiles=b"",
        )

    @pytest.fixture
    def query_schema(self, group_data: ProjectData) -> graphene.Schema:
        """Create GraphQL schema with GroupNode query."""

        class Query(graphene.ObjectType):  # type: ignore[misc]
            group_node = graphene.Field(GroupNode, id=graphene.String(required=True))

            async def resolve_group_node(self, info: graphene.ResolveInfo, id: str) -> GroupNode:
                return GroupNode.from_data(group_data)

        return graphene.Schema(query=Query)

    @pytest.fixture
    async def graphql_client(
        self,
        aiohttp_client: Any,
        query_schema: graphene.Schema,
    ) -> TestClient[Any]:  # type: ignore[type-arg]
        """Create test client with GraphQL endpoint."""
        mock_ctx = MagicMock()

        async def graphql_handler(request: web.Request) -> web.Response:
            body = await request.json()
            query = body.get("query", "")
            variables = body.get("variables")

            result = await query_schema.execute_async(
                query,
                variable_values=variables,
                context_value=mock_ctx,
            )

            response_data: dict[str, Any] = {}
            if result.data:
                response_data["data"] = result.data
            if result.errors:
                response_data["errors"] = [{"message": str(e)} for e in result.errors]

            return web.json_response(response_data)

        app = web.Application()
        app.router.add_post("/graphql", graphql_handler)

        client: TestClient[Any] = await aiohttp_client(app)  # type: ignore[type-arg]
        return client

    async def test_group_node_response_is_json_serializable(
        self,
        graphql_client: TestClient[Any],  # type: ignore[type-arg]
    ) -> None:
        """GroupNode query response should have JSON-serializable allowed_vfolder_hosts."""
        # Act: Make HTTP POST request to GraphQL endpoint
        resp = await graphql_client.post(
            "/graphql",
            json={
                "query": self.GROUP_NODE_QUERY,
                "variables": {"id": "test-group-id"},
            },
        )

        # Assert: HTTP response should succeed
        assert resp.status == HTTPStatus.OK

        # Assert: Response should be valid JSON (no serialization errors)
        data = await resp.json()

        # Assert: No GraphQL errors (set serialization would cause error here)
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"

        # Assert: GroupNode query returned valid data
        group_node = data.get("data", {}).get("groupNode", {})
        assert group_node.get("allowedVfolderHosts") is not None


class TestRegistryTargetInput:
    @pytest.mark.parametrize(
        "configuration", [{}, {"containerRegistry": None}, {"containerRegistry": "{}"}]
    )
    def test_omitted_null_and_empty_clear_the_target(
        self, configuration: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(inputobjecttype, "_INPUT_OBJECT_TYPE_DEFAULT_VALUE", Undefined)

        schema = graphene.Schema(types=[ModifyGroupInput])
        input_type = schema.graphql_schema.get_type("ModifyGroupInput")
        assert isinstance(input_type, GraphQLInputObjectType)
        props = coerce_input_value(configuration, input_type)
        target = props.to_action(uuid4()).updater.container_registry
        assert not target.is_nop()
        assert target.optional_value() is None


async def test_registry_field_is_lazy_and_batches_group_types() -> None:
    first, second = ProjectID(uuid4()), ProjectID(uuid4())

    async def resolve_groups(root: Any, info: graphene.ResolveInfo) -> list[Group]:
        return [Group(id=first), Group(id=second)]

    async def resolve_nodes(root: Any, info: graphene.ResolveInfo) -> list[GroupNode]:
        return [GroupNode(id=first, row_id=first)]

    query = type(
        "Query",
        (graphene.ObjectType,),
        {
            "groups": graphene.List(Group),
            "nodes": graphene.List(GroupNode),
            "resolve_groups": resolve_groups,
            "resolve_nodes": resolve_nodes,
        },
    )

    ctx = MagicMock()
    ctx.dataloader_manager = DataLoaderManager()
    project = ProjectData(
        id=first,
        name="project",
        description=None,
        is_active=True,
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
        integration_name=None,
        domain_name="default",
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        dotfiles=b"",
        resource_policy="default",
        type=ProjectType.GENERAL,
        container_registry=ImageCommitRegistry("harbor", "images"),
    )
    loader = ctx.processors.project.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[ProjectData].succeeded(
                    first, project, description="resolved"
                ),
                PartialBulkEntityResult[ProjectData].succeeded(
                    second,
                    replace(project, id=second, container_registry=None),
                    description="resolved",
                ),
            ]
        )
    )
    schema = graphene.Schema(query=query)
    plain = await schema.execute_async("{ groups { id } }", context_value=ctx)
    assert plain.errors is None
    loader.assert_not_awaited()
    loaded = await schema.execute_async(
        "{ groups { containerRegistry } nodes { containerRegistry } }", context_value=ctx
    )
    assert loaded.errors is None
    assert loaded.data == {
        "groups": [
            {"containerRegistry": '{"registry": "harbor", "project": "images"}'},
            {"containerRegistry": None},
        ],
        "nodes": [{"containerRegistry": '{"registry": "harbor", "project": "images"}'}],
    }
    loader.assert_awaited_once()
    assert list(loader.call_args.args[0].ids) == [first, second]
