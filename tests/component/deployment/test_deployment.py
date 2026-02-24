from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.deployment import (
    DeactivateRevisionResponse,
    DeploymentFilter,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
)
from ai.backend.common.dto.manager.query import StringFilter


class TestSearchDeployments:
    @pytest.mark.asyncio
    async def test_search_deployments_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with no data returns an empty list and pagination total=0."""
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert result.deployments == []
        assert result.pagination.total == 0

    @pytest.mark.asyncio
    async def test_search_deployments_with_filter(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with a name filter on empty data returns an empty list."""
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(
                filter=DeploymentFilter(
                    name=StringFilter(contains="nonexistent"),
                ),
            ),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert result.deployments == []
        assert result.pagination.total == 0


class TestGetDeployment:
    @pytest.mark.asyncio
    async def test_get_deployment_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """GET a non-existent deployment UUID returns a proper error response."""
        non_existent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_deployment(non_existent_id)


class TestSearchRevisions:
    @pytest.mark.asyncio
    async def test_search_revisions_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search revisions for a non-existent deployment returns empty results."""
        non_existent_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_revisions(
            non_existent_deployment_id,
            SearchRevisionsRequest(),
        )
        assert isinstance(result, ListRevisionsResponse)
        assert result.revisions == []
        assert result.pagination.total == 0


class TestDeactivateRevision:
    @pytest.mark.asyncio
    async def test_deactivate_revision_stub(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deactivate always returns success=True (stub handler)."""
        fake_deployment_id = uuid.uuid4()
        fake_revision_id = uuid.uuid4()
        result = await admin_registry.deployment.deactivate_revision(
            fake_deployment_id,
            fake_revision_id,
        )
        assert isinstance(result, DeactivateRevisionResponse)
        assert result.success is True


class TestSearchRoutes:
    @pytest.mark.asyncio
    async def test_search_routes_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search routes for a non-existent deployment returns empty results."""
        non_existent_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_routes(
            non_existent_deployment_id,
            SearchRoutesRequest(),
        )
        assert isinstance(result, ListRoutesResponse)
        assert result.routes == []
        assert result.pagination.total_count == 0
