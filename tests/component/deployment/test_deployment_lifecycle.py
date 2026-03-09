"""
Component tests for the Deployment SDK client lifecycle methods.

These tests verify HTTP routing, request/response serialization,
and error handling for Deployment API endpoints via the Client SDK.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.deployment import (
    CreateDeploymentRequest,
    DeploymentMetadataInput,
    DeploymentStrategyInput,
    ImageInput,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    NetworkAccessInput,
    ResourceConfigInput,
    RevisionInput,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
    UpdateDeploymentRequest,
)
from ai.backend.common.dto.manager.deployment.request import ClusterConfigInput
from ai.backend.common.types import ClusterMode

_RANDOM_DEPLOYMENT_ID = uuid.uuid4()
_RANDOM_REVISION_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Tier 1: SDK create — deployment creation via the HTTP API
# ---------------------------------------------------------------------------


class TestCreateDeployment:
    async def test_create_deployment_missing_image_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
    ) -> None:
        """Creating a deployment with a non-existent image raises an error."""
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture,
                name="test-deployment",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            desired_replica_count=1,
            initial_revision=RevisionInput(
                name="rev-1",
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_group="nonexistent-sgroup",
                    resource_slots={"cpu": "1", "mem": "1073741824"},
                ),
                image=ImageInput(id=uuid.uuid4()),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=uuid.uuid4(),
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
            ),
        )
        with pytest.raises(Exception):
            await admin_registry.deployment.create_deployment(request)


# ---------------------------------------------------------------------------
# Tier 2: SDK scale — update deployment replica count
# ---------------------------------------------------------------------------


class TestUpdateDeployment:
    async def test_update_nonexistent_deployment_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Updating a non-existent deployment raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.update_deployment(
                _RANDOM_DEPLOYMENT_ID,
                UpdateDeploymentRequest(desired_replicas=5),
            )

    async def test_update_deployment_name_nonexistent(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Updating the name of a non-existent deployment raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.update_deployment(
                _RANDOM_DEPLOYMENT_ID,
                UpdateDeploymentRequest(name="new-name"),
            )


# ---------------------------------------------------------------------------
# Tier 3: SDK sync — search routes (route synchronization readiness)
# ---------------------------------------------------------------------------


class TestSearchRoutesLifecycle:
    async def test_search_routes_for_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Searching routes for a non-existent deployment returns empty results."""
        result = await admin_registry.deployment.search_routes(
            _RANDOM_DEPLOYMENT_ID,
            SearchRoutesRequest(),
        )
        assert isinstance(result, ListRoutesResponse)
        assert result.routes == []
        assert result.pagination.total_count == 0
        assert result.pagination.has_next_page is False
        assert result.pagination.has_previous_page is False


# ---------------------------------------------------------------------------
# Tier 4: SDK delete — destroy deployment
# ---------------------------------------------------------------------------


class TestDestroyDeployment:
    async def test_destroy_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Destroying a non-existent deployment raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.destroy_deployment(_RANDOM_DEPLOYMENT_ID)


# ---------------------------------------------------------------------------
# Tier 5: SDK revision operations
# ---------------------------------------------------------------------------


class TestGetRevision:
    async def test_get_revision_nonexistent(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Getting a non-existent revision raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_revision(
                _RANDOM_DEPLOYMENT_ID,
                _RANDOM_REVISION_ID,
            )


class TestSearchRevisionsLifecycle:
    async def test_search_revisions_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search revisions with custom pagination returns correct pagination info."""
        result = await admin_registry.deployment.search_revisions(
            _RANDOM_DEPLOYMENT_ID,
            SearchRevisionsRequest(limit=10, offset=0),
        )
        assert isinstance(result, ListRevisionsResponse)
        assert result.revisions == []
        assert result.pagination.total == 0
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0


# ---------------------------------------------------------------------------
# Tier 6: Role-based access — user vs admin
# ---------------------------------------------------------------------------


class TestUserAccessDeployment:
    async def test_user_searches_empty_deployments(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user can search deployments and gets empty results."""
        result = await user_registry.deployment.search_deployments(
            SearchDeploymentsRequest(),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert result.deployments == []
        assert result.pagination.total == 0

    async def test_user_get_nonexistent_deployment(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user gets NotFoundError for non-existent deployment."""
        with pytest.raises(NotFoundError):
            await user_registry.deployment.get_deployment(_RANDOM_DEPLOYMENT_ID)
