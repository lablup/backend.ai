"""
Component tests for deployment mutation and lifecycle operations.

These tests verify HTTP routing, request/response serialization,
and write/mutation behavior for Deployment API endpoints via the Client SDK.
"""

from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
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
    UpdateDeploymentRequest,
)
from ai.backend.common.dto.manager.deployment.request import ClusterConfigInput
from ai.backend.common.types import ClusterMode

_RANDOM_DEPLOYMENT_ID = uuid.uuid4()
_RANDOM_REVISION_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Deployment CRUD
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


# ---------------------------------------------------------------------------
# Destroy
# ---------------------------------------------------------------------------


class TestDestroyDeployment:
    async def test_destroy_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Destroying a non-existent deployment raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.destroy_deployment(_RANDOM_DEPLOYMENT_ID)

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
# Revision Management
# ---------------------------------------------------------------------------


class TestRevisionManagement:
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
# Replica Management
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
# Role-based access — user vs admin
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
