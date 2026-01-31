"""
Tests for Group GraphQL mutation response serialization.
Tests allowed_vfolder_hosts JSON serialization in CreateGroup mutation.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import graphene
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient

from ai.backend.common.types import (
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.api.gql_legacy.group import CreateGroup, GroupNode
from ai.backend.manager.data.group.types import GroupData, ProjectType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.group.actions.create_group import CreateGroupActionResult


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
    def group_data_response(self) -> GroupData:
        """GroupData returned from CreateGroup action."""
        return GroupData(
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
            integration_id=None,
            container_registry={},
        )

    @pytest.fixture
    def mock_graph_ctx(self, group_data_response: GroupData) -> MagicMock:
        """GraphQueryContext mock with processors and user context."""

        ctx = MagicMock()
        ctx.processors.group.create_group.wait_for_complete = AsyncMock(
            return_value=CreateGroupActionResult(data=group_data_response)
        )
        # Required for privileged_mutation decorator
        ctx.user = {
            "role": UserRole.SUPERADMIN,
            "domain_name": "default",
        }
        return ctx

    @pytest.fixture
    def mutation_schema(self) -> graphene.Schema:
        """Create GraphQL schema with CreateGroup mutation."""

        class Query(graphene.ObjectType):
            """Dummy query required by graphene.Schema."""

            ok = graphene.Boolean(default_value=True)

        class Mutation(graphene.ObjectType):
            create_group = CreateGroup.Field()

        return graphene.Schema(query=Query, mutation=Mutation)

    @pytest.fixture
    async def graphql_client(
        self,
        aiohttp_client: Any,
        mutation_schema: graphene.Schema,
        mock_graph_ctx: MagicMock,
    ) -> AsyncGenerator[TestClient, None]:
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

            response_data: dict = {}
            if result.data:
                response_data["data"] = result.data
            if result.errors:
                response_data["errors"] = [{"message": str(e)} for e in result.errors]

            return web.json_response(response_data)

        app = web.Application()
        app.router.add_post("/graphql", graphql_handler)

        return await aiohttp_client(app)

    async def test_create_group_response_is_json_serializable(
        self,
        graphql_client: TestClient,
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
    def mock_group_row(self) -> MagicMock:
        """GroupRow mock with VFolderHostPermissionMap (contains sets).

        This simulates what VFolderHostPermissionColumn.process_result_value() returns
        when loading data from the database.
        """
        row = MagicMock()
        row.id = uuid4()
        row.name = "test-group"
        row.description = "Test group"
        row.is_active = True
        row.created_at = datetime.now(tz=UTC)
        row.modified_at = datetime.now(tz=UTC)
        row.domain_name = "default"
        row.total_resource_slots = ResourceSlot({})
        # VFolderHostPermissionColumn.process_result_value() returns VFolderHostPermissionMap
        # which contains sets, not lists
        row.allowed_vfolder_hosts = VFolderHostPermissionMap({
            "local:volume1": {VFolderHostPermission.CREATE, VFolderHostPermission.MODIFY},
        })
        row.integration_id = None
        row.resource_policy = "default"
        row.type = ProjectType.GENERAL
        row.container_registry = {}
        return row

    @pytest.fixture
    def query_schema(self, mock_group_row: MagicMock) -> graphene.Schema:
        """Create GraphQL schema with GroupNode query."""

        class Query(graphene.ObjectType):
            group_node = graphene.Field(GroupNode, id=graphene.String(required=True))

            async def resolve_group_node(self, info: graphene.ResolveInfo, id: str) -> GroupNode:
                # Simulate GroupNode.from_row() with mock row
                return GroupNode.from_row(info.context, mock_group_row)

        return graphene.Schema(query=Query)

    @pytest.fixture
    async def graphql_client(
        self,
        aiohttp_client: Any,
        query_schema: graphene.Schema,
    ) -> AsyncGenerator[TestClient, None]:
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

            response_data: dict = {}
            if result.data:
                response_data["data"] = result.data
            if result.errors:
                response_data["errors"] = [{"message": str(e)} for e in result.errors]

            return web.json_response(response_data)

        app = web.Application()
        app.router.add_post("/graphql", graphql_handler)

        return await aiohttp_client(app)

    async def test_group_node_response_is_json_serializable(
        self,
        graphql_client: TestClient,
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
