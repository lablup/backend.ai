from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.errors.user import UserResourcePolicyNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.searchable_fields import (
    UserResourcePolicySearchableFields,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.testutils.db import with_tables


class TestUserResourcePolicyRepository:
    """Test suite for UserResourcePolicyRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> UserResourcePolicyRepository:
        """Repository instance with real database"""
        return UserResourcePolicyRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[UserResourcePolicyData, None]:
        """Create a sample policy in the database for testing"""
        policy_name = "test-policy-sample"
        async with db_with_cleanup.begin_session() as db_sess:
            policy_row = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1000000,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy_row)
            await db_sess.flush()

        yield UserResourcePolicySearchableFields.own.to_data(policy_row)

    async def test_get_by_name_success(
        self, repository: UserResourcePolicyRepository, sample_policy: UserResourcePolicyData
    ) -> None:
        """Reads the policy the name addresses."""
        result = await repository.get_by_name(sample_policy.name)

        assert isinstance(result, UserResourcePolicyData)
        assert result.name == sample_policy.name
        assert result.max_vfolder_count == sample_policy.max_vfolder_count
        assert result.max_quota_scope_size == sample_policy.max_quota_scope_size

    async def test_get_by_name_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """An unknown name is an error, not an empty answer."""
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.get_by_name("non-existing")
