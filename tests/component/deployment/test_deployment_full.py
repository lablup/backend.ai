"""
Component tests for deployment lifecycle, query operations, and replica management.

These tests verify the full deployment lifecycle including:
- Deployment create/update/destroy operations
- Revision activation/deactivation
- Replica synchronization and desired_replicas changes
- Route traffic management
- Query operations (search, get by ID, pagination)
- Status mapping (EndpointLifecycle -> ModelDeploymentStatus)
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy, ModelDeploymentStatus
from ai.backend.common.dto.manager.deployment import (
    AddRevisionRequest,
    CreateDeploymentRequest,
    DeploymentMetadataInput,
    DeploymentStrategyInput,
    ImageInput,
    ListDeploymentsResponse,
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
from ai.backend.common.types import ClusterMode, QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.services.deployment.service import _map_lifecycle_to_status

# Type aliases for fixture factories
ImageFactoryFunc = Callable[[], Coroutine[Any, Any, uuid.UUID]]
VFolderFactoryFunc = Callable[[], Coroutine[Any, Any, uuid.UUID]]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID."""
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.deployment.test.local",
                registry_name=f"deployment-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
async def image_factory(
    db_engine: SAEngine,
    container_registry_fixture: uuid.UUID,
) -> AsyncIterator[ImageFactoryFunc]:
    """Factory that creates ImageRow entries for deployment tests."""
    created_ids: list[uuid.UUID] = []

    async def _create() -> uuid.UUID:
        image_id = uuid.uuid4()
        unique = secrets.token_hex(4)
        image_name = f"deployment-image-{unique}"
        canonical = f"registry.deployment.test.local/testproject/{image_name}:latest"
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(ImageRow.__table__).values(
                    id=image_id,
                    name=canonical,
                    project="testproject",
                    image=image_name,
                    tag="latest",
                    registry="registry.deployment.test.local",
                    registry_id=container_registry_fixture,
                    architecture="x86_64",
                    config_digest=f"sha256:{image_id.hex * 2}",
                    size_bytes=2048000,
                    is_local=False,
                    type=ImageType.COMPUTE,
                    accelerators=None,
                    labels={},
                    resources={
                        "cpu": {"min": "1", "max": "8"},
                        "mem": {"min": "536870912", "max": "8589934592"},
                    },
                    status=ImageStatus.ALIVE,
                )
            )
        created_ids.append(image_id)
        return image_id

    yield _create

    # Cleanup
    if created_ids:
        async with db_engine.begin() as conn:
            await conn.execute(
                ImageRow.__table__.delete().where(ImageRow.__table__.c.id.in_(created_ids))
            )


@pytest.fixture()
async def vfolder_factory(
    db_engine: SAEngine,
    domain_fixture: str,
    admin_user_fixture: Any,
) -> AsyncIterator[VFolderFactoryFunc]:
    """Factory that creates VFolder entries for deployment model mounts."""
    created_ids: list[uuid.UUID] = []

    async def _create() -> uuid.UUID:
        vfolder_id = uuid.uuid4()
        unique = secrets.token_hex(4)
        user_uuid = admin_user_fixture.user_uuid
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=user_uuid,
        )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(vfolders).values(
                    id=vfolder_id,
                    name=f"deployment-model-{unique}",
                    host="local",
                    domain_name=domain_fixture,
                    quota_scope_id=str(quota_scope_id),
                    usage_mode=VFolderUsageMode.MODEL,
                    permission=VFolderMountPermission.READ_ONLY,
                    ownership_type=VFolderOwnershipType.USER,
                    user=str(user_uuid),
                    creator="admin-test@test.local",
                    status=VFolderOperationStatus.READY,
                    cloneable=False,
                )
            )
        created_ids.append(vfolder_id)
        return vfolder_id

    yield _create

    # Cleanup
    if created_ids:
        async with db_engine.begin() as conn:
            await conn.execute(vfolders.delete().where(vfolders.c.id.in_(created_ids)))


@pytest.fixture()
async def deployment_seed_data(
    image_factory: ImageFactoryFunc,
    vfolder_factory: VFolderFactoryFunc,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create and return (image_id, vfolder_id) for deployment tests."""
    image_id = await image_factory()
    vfolder_id = await vfolder_factory()
    return image_id, vfolder_id


# ---------------------------------------------------------------------------
# Tier 1: Deployment Lifecycle — create, update, destroy
# ---------------------------------------------------------------------------


class TestDeploymentLifecycle:
    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_create_deployment_success(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Creating a deployment with valid config returns deployment with initial status."""
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
        assert deployment.id is not None
        assert deployment.name == request.metadata.name
        assert deployment.status is not None  # Should have initial status

    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_update_deployment_config(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Updating deployment config (name, desired_replicas) succeeds."""
        image_id, vfolder_id = deployment_seed_data
        # Create deployment
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

        # Update name and replicas
        new_name = f"updated-deployment-{secrets.token_hex(4)}"
        await admin_registry.deployment.update_deployment(
            deployment.id,
            UpdateDeploymentRequest(name=new_name, desired_replicas=3),
        )

        # Verify update
        updated_response = await admin_registry.deployment.get_deployment(deployment.id)
        updated = updated_response.deployment
        assert updated.name == new_name
        assert updated.replica_state.desired_replica_count == 3

    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_destroy_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Destroying a deployment terminates it successfully."""
        image_id, vfolder_id = deployment_seed_data
        # Create deployment
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

        # Destroy deployment
        await admin_registry.deployment.destroy_deployment(deployment.id)

        # Verify deployment is destroyed (should raise NotFoundError or have DESTROYED status)
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_deployment(deployment.id)


# ---------------------------------------------------------------------------
# Tier 2: Query Operations — search, get by ID, pagination, 404 handling
# ---------------------------------------------------------------------------


class TestQueryOperations:
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

    async def test_get_nonexistent_deployment_returns_404(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Get non-existent deployment returns 404 NotFoundError."""
        random_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_deployment(random_id)


# ---------------------------------------------------------------------------
# Tier 3: Revision Management — activate, deactivate
# ---------------------------------------------------------------------------


class TestRevisionManagement:
    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_activate_deactivate_revision(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Activating and deactivating revisions updates their status."""
        image_id, vfolder_id = deployment_seed_data
        # Create deployment with initial revision
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

        # Add a second revision
        revision2_response = await admin_registry.deployment.add_revision(
            deployment.id,
            AddRevisionRequest(
                revision=RevisionInput(
                    name="v2",
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
            ),
        )
        revision2 = revision2_response.revision

        # Activate revision2
        await admin_registry.deployment.activate_revision(deployment.id, revision2.id)

        # Get revisions and verify activation
        revisions_result = await admin_registry.deployment.search_revisions(
            deployment.id,
            SearchRevisionsRequest(limit=10, offset=0),
        )
        # Check that we have at least one revision returned
        assert len(revisions_result.revisions) > 0
        # Verify that the activated revision is in the list
        revision_ids = [r.id for r in revisions_result.revisions]
        assert revision2.id in revision_ids

        # Deactivate revision
        await admin_registry.deployment.deactivate_revision(deployment.id, revision2.id)


# ---------------------------------------------------------------------------
# Tier 4: Replica Management — sync replicas, change desired_replicas
# ---------------------------------------------------------------------------


class TestReplicaManagement:
    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_change_desired_replicas(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        scaling_group_fixture: str,
        deployment_seed_data: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Changing desired_replicas updates the replica count."""
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

        # Scale to 5 replicas
        await admin_registry.deployment.update_deployment(
            deployment.id,
            UpdateDeploymentRequest(desired_replicas=5),
        )

        # Verify replica count updated
        updated_response = await admin_registry.deployment.get_deployment(deployment.id)
        updated = updated_response.deployment
        assert updated.replica_state.desired_replica_count == 5


# ---------------------------------------------------------------------------
# Tier 5: Route & Traffic Management
# ---------------------------------------------------------------------------


class TestRouteTrafficManagement:
    @pytest.mark.xfail(strict=True, reason="Requires deployment controller mocking")
    async def test_search_routes(
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


# ---------------------------------------------------------------------------
# Tier 6: Status Mapping — EndpointLifecycle -> ModelDeploymentStatus
# ---------------------------------------------------------------------------


class TestStatusMapping:
    def test_lifecycle_to_status_mapping(self) -> None:
        """Verify EndpointLifecycle maps correctly to ModelDeploymentStatus."""
        # Test all lifecycle states map to correct status
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
                f"EndpointLifecycle.{lifecycle.name} should map to ModelDeploymentStatus.{expected_status.name}, got {actual_status.name}"
            )
