from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest

from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
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

        yield policy_row.to_dataclass()

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

    async def test_get_by_user_id_resolves_through_the_user(
        self,
        repository: UserResourcePolicyRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_policy: UserResourcePolicyData,
    ) -> None:
        """The join through ``users`` is why this repository still exists."""
        user_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name="default",
                    description="test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="policy-owner",
                    email="policy-owner@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name="default",
                    role=UserRole.USER,
                    resource_policy=sample_policy.name,
                )
            )
            await db_sess.flush()

        result = await repository.get_by_user_id(user_id)

        assert result.name == sample_policy.name

    async def test_get_by_user_id_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """A user with no policy row is an error, not an empty answer."""
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.get_by_user_id(uuid4())
