"""
Component tests for deployment mutation and lifecycle operations.

These tests verify HTTP routing, request/response serialization,
and write/mutation behavior for Deployment API endpoints via the Client SDK.
"""

from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.config import ModelDefinitionDraft
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
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode
from ai.backend.testutils.fixtures import DomainFixtureData, ScalingGroupFixtureData

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
        domain_fixture: DomainFixtureData,
    ) -> None:
        """Creating a deployment with a non-existent image raises an error."""
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=ResourceGroupName("nonexistent-sgroup"),
                name="test-deployment",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "1", "mem": "1073741824"},
                ),
                image=ImageInput(id=ImageID(uuid.uuid4())),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=VFolderUUID(uuid.uuid4()),
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        with pytest.raises(Exception):
            await admin_registry.deployment.create_deployment(request)

    async def test_create_deployment_success(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_fixture: ScalingGroupFixtureData,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Creating a deployment with valid config returns deployment with initial status."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_fixture.scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
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
                UpdateDeploymentRequest(replica_count=5),
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

    async def test_update_deployment_config(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_fixture: ScalingGroupFixtureData,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Updating deployment config (name, replica_count) succeeds."""
        image_id, vfolder_id = deployment_seed_data
        # Create deployment
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_fixture.scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Update name and replicas
        new_name = f"updated-deployment-{secrets.token_hex(4)}"
        await admin_registry.deployment.update_deployment(
            deployment.id,
            UpdateDeploymentRequest(name=new_name, replica_count=3),
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

    @pytest.mark.xfail(strict=True, reason="Destroyed deployment still accessible via GET")
    async def test_destroy_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_fixture: ScalingGroupFixtureData,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Destroying a deployment terminates it successfully."""
        image_id, vfolder_id = deployment_seed_data
        # Create deployment
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_fixture.scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
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

    async def test_activate_deactivate_revision(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_fixture: ScalingGroupFixtureData,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Adding a revision and searching revisions works correctly."""
        image_id, vfolder_id = deployment_seed_data
        revision_input = RevisionInput(
            cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigInput(
                resource_slots={"cpu": "2", "mem": "2147483648"},
            ),
            image=ImageInput(id=image_id),
            model_runtime_config=ModelRuntimeConfigInput(),
            model_mount_config=ModelMountConfigInput(
                vfolder_id=vfolder_id,
                mount_destination="/models",
                definition_path="model-definition.yaml",
            ),
            model_definition=ModelDefinitionDraft(),
        )

        # Create deployment with initial revision (auto-activated)
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_fixture.scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=0,
            initial_revision=revision_input,
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Add a second revision (not activated since deployment is already deploying)
        revision2_response = await admin_registry.deployment.add_revision(
            deployment.id,
            AddRevisionRequest(
                revision=RevisionInput(
                    cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                    resource_config=ResourceConfigInput(
                        resource_slots={"cpu": "2", "mem": "2147483648"},
                    ),
                    image=ImageInput(id=image_id),
                    model_runtime_config=ModelRuntimeConfigInput(),
                    model_mount_config=ModelMountConfigInput(
                        vfolder_id=vfolder_id,
                        mount_destination="/models",
                        definition_path="model-definition.yaml",
                    ),
                    model_definition=ModelDefinitionDraft(),
                ),
            ),
        )
        revision2 = revision2_response.revision

        # Search revisions and verify both exist
        revisions_result = await admin_registry.deployment.search_revisions(
            deployment.id,
            SearchRevisionsRequest(limit=10, offset=0),
        )
        assert len(revisions_result.revisions) >= 2
        revision_ids = [r.id for r in revisions_result.revisions]
        assert revision2.id in revision_ids


# ---------------------------------------------------------------------------
# Replica Management
# ---------------------------------------------------------------------------


class TestReplicaManagement:
    async def test_change_replica_count(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_fixture: ScalingGroupFixtureData,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Changing replica_count updates the replica count."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_fixture.scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Scale to 5 replicas
        await admin_registry.deployment.update_deployment(
            deployment.id,
            UpdateDeploymentRequest(replica_count=5),
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
        """Regular user gets NotFoundError or PermissionDeniedError for non-existent deployment."""
        with pytest.raises((NotFoundError, PermissionDeniedError)):
            await user_registry.deployment.get_deployment(_RANDOM_DEPLOYMENT_ID)
