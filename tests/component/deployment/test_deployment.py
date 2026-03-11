"""
Component tests for deployment query and read operations.

These tests verify HTTP routing, request/response serialization,
and read-only query behavior for Deployment API endpoints via the Client SDK.
"""

from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy, ModelDeploymentStatus
from ai.backend.common.dto.manager.deployment import (
    CreateDeploymentRequest,
    DeactivateRevisionResponse,
    DeploymentFilter,
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
)
from ai.backend.common.dto.manager.deployment.request import ClusterConfigInput
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import ClusterMode
from ai.backend.manager.services.deployment.service import _map_lifecycle_to_status


class TestSearchDeployments:
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

    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_search_deployments_paginated(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Search deployments with pagination returns correct page."""
        image_id, vfolder_id = deployment_seed_data
        # Create multiple deployments
        deployment_ids = []
        for i in range(3):
            request = CreateDeploymentRequest(
                metadata=DeploymentMetadataInput(
                    project_id=group_fixture,
                    domain_name=domain_fixture,
                    name=f"test-deployment-{i}-{secrets.token_hex(4)}",
                ),
                network_access=NetworkAccessInput(open_to_public=False),
                default_deployment_strategy=DeploymentStrategyInput(
                    type=DeploymentStrategy.ROLLING,
                ),
                desired_replica_count=1,
                initial_revision=RevisionInput(
                    name="v1",
                    cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                    resource_config=ResourceConfigInput(
                        resource_group=scaling_group_fixture,
                        resource_slots={"cpu": "2", "mem": "2147483648"},
                    ),
                    image=ImageInput(id=image_id),
                    model_runtime_config=ModelRuntimeConfigInput(),
                    model_mount_config=ModelMountConfigInput(
                        vfolder_id=vfolder_id,
                        mount_destination="/models",
                        definition_path="model-definition.yaml",
                    ),
                ),
            )
            response = await admin_registry.deployment.create_deployment(request)
            deployment_ids.append(response.deployment.id)

        # Search with pagination
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(limit=2, offset=0),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert len(result.deployments) >= 2
        assert result.pagination.total >= 3


class TestGetDeployment:
    async def test_get_deployment_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """GET a non-existent deployment UUID returns a proper error response."""
        non_existent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_deployment(non_existent_id)

    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_get_deployment_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Get deployment by ID returns correct deployment details."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            desired_replica_count=1,
            initial_revision=RevisionInput(
                name="v1",
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_group=scaling_group_fixture,
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Get by ID
        fetched_response = await admin_registry.deployment.get_deployment(deployment.id)
        fetched = fetched_response.deployment
        assert fetched.id == deployment.id
        assert fetched.name == deployment.name
        assert fetched.project_id == group_fixture


class TestSearchRevisions:
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

    async def test_search_revisions_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search revisions with custom pagination returns correct pagination info."""
        random_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_revisions(
            random_deployment_id,
            SearchRevisionsRequest(limit=10, offset=0),
        )
        assert isinstance(result, ListRevisionsResponse)
        assert result.revisions == []
        assert result.pagination.total == 0
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0


class TestSearchRoutes:
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

    async def test_search_routes_for_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Searching routes for a non-existent deployment returns empty results."""
        random_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_routes(
            random_deployment_id,
            SearchRoutesRequest(),
        )
        assert isinstance(result, ListRoutesResponse)
        assert result.routes == []
        assert result.pagination.total_count == 0
        assert result.pagination.has_next_page is False
        assert result.pagination.has_previous_page is False

    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_search_routes_for_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Search routes for a deployment returns route list."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            desired_replica_count=1,
            initial_revision=RevisionInput(
                name="v1",
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_group=scaling_group_fixture,
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Search routes
        routes_result = await admin_registry.deployment.search_routes(
            deployment.id,
            SearchRoutesRequest(limit=10, offset=0),
        )
        assert routes_result is not None
        # Routes may be empty if not yet created, but API should succeed
        assert hasattr(routes_result, "routes")


class TestDeactivateRevision:
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


class TestStatusMapping:
    def test_lifecycle_to_status_mapping(self) -> None:
        """Verify EndpointLifecycle maps correctly to ModelDeploymentStatus."""
        mapping = {
            EndpointLifecycle.PENDING: ModelDeploymentStatus.PENDING,
            EndpointLifecycle.CREATED: ModelDeploymentStatus.READY,
            EndpointLifecycle.READY: ModelDeploymentStatus.READY,
            EndpointLifecycle.SCALING: ModelDeploymentStatus.SCALING,
            EndpointLifecycle.DEPLOYING: ModelDeploymentStatus.DEPLOYING,
            EndpointLifecycle.DESTROYING: ModelDeploymentStatus.STOPPING,
            EndpointLifecycle.DESTROYED: ModelDeploymentStatus.STOPPED,
        }

        for lifecycle, expected_status in mapping.items():
            actual_status = _map_lifecycle_to_status(lifecycle)
            assert actual_status == expected_status, (
                f"EndpointLifecycle.{lifecycle.name} should map to "
                f"ModelDeploymentStatus.{expected_status.name}, got {actual_status.name}"
            )
