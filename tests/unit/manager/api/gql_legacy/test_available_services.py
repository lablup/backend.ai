from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.schema import Mutation, Query
from ai.backend.manager.models.user import UserRole

_AVAILABLE_SERVICES_QUERY = """
    query {
        available_services {
            count
            edges { node { id service_variants } }
        }
    }
"""

_AVAILABLE_SERVICE_QUERY = """
    query {
        available_service { service_variants }
    }
"""


@pytest.fixture(scope="module")
def legacy_schema() -> graphene.Schema:
    return graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)


@pytest.fixture
def graph_ctx(request: pytest.FixtureRequest) -> MagicMock:
    role: UserRole = request.param
    ctx = MagicMock()
    ctx.user = {
        "role": role,
        "domain_name": "default",
        "uuid": uuid.uuid4(),
        "email": "test@test.com",
    }
    return ctx


class TestAvailableServices:
    @pytest.mark.parametrize("graph_ctx", [UserRole.SUPERADMIN], indirect=True)
    async def test_superadmin_reads_connection(
        self, legacy_schema: graphene.Schema, graph_ctx: MagicMock
    ) -> None:
        result = await legacy_schema.execute_async(
            _AVAILABLE_SERVICES_QUERY, context_value=graph_ctx
        )

        assert result.errors is None
        data: dict[str, Any] = result.data["available_services"]
        assert data["count"] == 1
        assert [edge["node"]["service_variants"] for edge in data["edges"]] == [
            ["manager", "common"]
        ]

    @pytest.mark.parametrize("graph_ctx", [UserRole.SUPERADMIN], indirect=True)
    async def test_superadmin_reads_service_variants(
        self, legacy_schema: graphene.Schema, graph_ctx: MagicMock
    ) -> None:
        result = await legacy_schema.execute_async(
            _AVAILABLE_SERVICE_QUERY, context_value=graph_ctx
        )

        assert result.errors is None
        assert result.data["available_service"]["service_variants"] == ["manager", "common"]

    @pytest.mark.parametrize(
        "graph_ctx",
        [UserRole.ADMIN, UserRole.USER, UserRole.MONITOR],
        indirect=True,
        ids=lambda role: role.value,
    )
    async def test_non_superadmin_is_forbidden(
        self, legacy_schema: graphene.Schema, graph_ctx: MagicMock
    ) -> None:
        result = await legacy_schema.execute_async(
            _AVAILABLE_SERVICES_QUERY, context_value=graph_ctx
        )

        assert result.errors is not None
        assert "superadmin privilege required" in str(result.errors[0])
