from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import BinarySize, QuotaScopeID, ResourceSlot
from ai.backend.manager.data.permission.types import (
    EntityType as PermissionEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as PermissionScopeType,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
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
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow, ensure_quota_scope_accessible_by_user
from ai.backend.testutils.db import with_tables


class TestEnsureQuotaScopeAccessibleByUser:
    """Test cases for ensure_quota_scope_accessible_by_user function"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables. TRUNCATE CASCADE handles cleanup."""
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
                AgentRow,
                VFolderRow,
                ContainerRegistryRow,
                ImageRow,
                ResourcePresetRow,
                EndpointRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                SessionRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for quota scope",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def other_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create other test domain and return domain name"""
        domain_name = f"test-domain-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Other test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def domain_admin_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Create admin user and return user UUID"""
        user_uuid = uuid4()
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"test_admin_{user_uuid.hex[:8]}",
                email=f"test-admin-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.ADMIN,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def regular_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Create regular user and return user UUID"""
        user_uuid = uuid4()
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"test_user_{user_uuid.hex[:8]}",
                email=f"test-user-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def other_domain_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Create user in other domain and return user UUID"""
        user_uuid = uuid4()
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"test_other_{user_uuid.hex[:8]}",
                email=f"test-other-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=other_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def domain_user_data_dict(
        self,
        domain_admin_user: UUID,
        test_domain_name: str,
    ) -> dict[str, Any]:
        """Return user dict for domain admin user"""
        return {
            "uuid": domain_admin_user,
            "role": UserRole.ADMIN,
            "domain_name": test_domain_name,
        }

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test project resource policy and return policy name"""
        policy_name = f"test-group-policy-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Create test group and return group UUID"""
        group_uuid = uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test_group_{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                resource_policy=test_project_resource_policy_name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_uuid

    async def test_ensure_quota_scope_accessible_by_domain_admin_with_user_dict(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        regular_user: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin accessing user quota scope within same domain with user dict"""
        quota_scope = QuotaScopeID.parse(f"user:{regular_user}")

        async with db_with_cleanup.begin_session() as session:
            # Should not raise any exception
            await ensure_quota_scope_accessible_by_user(
                session,
                quota_scope,
                domain_user_data_dict,
            )

    async def test_ensure_quota_scope_not_accessible_by_admin_from_other_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_domain_user: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin cannot access user quota scope from different domain"""
        quota_scope = QuotaScopeID.parse(f"user:{other_domain_user}")

        async with db_with_cleanup.begin_session() as session:
            with pytest.raises(InvalidAPIParameters):
                await ensure_quota_scope_accessible_by_user(
                    session,
                    quota_scope,
                    domain_user_data_dict,
                )

    async def test_ensure_group_quota_scope_accessible_by_admin(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin accessing project quota scope within same domain"""
        quota_scope = QuotaScopeID.parse(f"project:{test_group}")

        async with db_with_cleanup.begin_session() as session:
            # Should not raise any exception
            await ensure_quota_scope_accessible_by_user(
                session,
                quota_scope,
                domain_user_data_dict,
            )

    @pytest.fixture
    def regular_user_data_dict(
        self,
        regular_user: UUID,
        test_domain_name: str,
    ) -> dict[str, Any]:
        """User dict for a regular user (USER role)."""
        return {
            "uuid": regular_user,
            "role": UserRole.USER,
            "domain_name": test_domain_name,
        }

    @pytest.fixture
    async def regular_user_membership_in_test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        regular_user: UUID,
        test_group: UUID,
    ) -> AsyncGenerator[None, None]:
        """Insert ASE row binding regular_user to test_group."""
        async with db_with_cleanup.begin_session() as session:
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(test_group),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(regular_user),
                )
            )
            await session.flush()
        yield

    @pytest.fixture
    async def other_group_with_regular_user_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        regular_user: UUID,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Insert a separate group in the same domain plus an ASE row for regular_user."""
        other_group_id = uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(
                GroupRow(
                    id=other_group_id,
                    name=f"other_group_{other_group_id.hex[:8]}",
                    domain_name=test_domain_name,
                    resource_policy=test_project_resource_policy_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    type=ProjectType.GENERAL,
                )
            )
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(other_group_id),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(regular_user),
                )
            )
            await session.flush()
        yield other_group_id

    async def test_user_can_access_group_quota_when_ase_membership_present(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: UUID,
        regular_user_data_dict: dict[str, Any],
        regular_user_membership_in_test_group: None,
    ) -> None:
        """Regular user with ASE (PROJECT, group, USER) row passes the project quota check."""
        quota_scope = QuotaScopeID.parse(f"project:{test_group}")

        async with db_with_cleanup.begin_session() as session:
            # Should not raise any exception
            await ensure_quota_scope_accessible_by_user(
                session,
                quota_scope,
                regular_user_data_dict,
            )

    async def test_user_cannot_access_group_quota_without_ase_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: UUID,
        regular_user_data_dict: dict[str, Any],
    ) -> None:
        """Regular user without ASE membership row is rejected at the project quota check."""
        quota_scope = QuotaScopeID.parse(f"project:{test_group}")

        async with db_with_cleanup.begin_session() as session:
            with pytest.raises(InvalidAPIParameters):
                await ensure_quota_scope_accessible_by_user(
                    session,
                    quota_scope,
                    regular_user_data_dict,
                )

    async def test_user_membership_in_other_project_does_not_grant_access(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: UUID,
        regular_user_data_dict: dict[str, Any],
        other_group_with_regular_user_membership: UUID,
    ) -> None:
        """Membership in project A does not grant quota access to project B."""
        quota_scope = QuotaScopeID.parse(f"project:{test_group}")

        async with db_with_cleanup.begin_session() as session:
            with pytest.raises(InvalidAPIParameters):
                await ensure_quota_scope_accessible_by_user(
                    session,
                    quota_scope,
                    regular_user_data_dict,
                )
