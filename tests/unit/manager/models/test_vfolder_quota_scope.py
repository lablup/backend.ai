from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import BinarySize, QuotaScopeID
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import ensure_quota_scope_accessible_by_user


class TestEnsureQuotaScopeAccessibleByUser:
    """Test cases for ensure_quota_scope_accessible_by_user function"""

    @pytest.fixture
    async def test_domain_name(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for quota scope",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def other_domain_name(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create other test domain and return domain name"""
        domain_name = f"test-domain-{uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Other test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def domain_admin_user(
        self,
        database_engine: ExtendedAsyncSAEngine,
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

        async with database_engine.begin_session() as db_sess:
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
        database_engine: ExtendedAsyncSAEngine,
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

        async with database_engine.begin_session() as db_sess:
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
        database_engine: ExtendedAsyncSAEngine,
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

        async with database_engine.begin_session() as db_sess:
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
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test project resource policy and return policy name"""
        policy_name = f"test-group-policy-{uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_group(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[UUID, None]:
        """Create test group and return group UUID"""
        group_uuid = uuid4()

        async with database_engine.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test_group_{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                resource_policy=test_project_resource_policy_name,
                description="",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_uuid

    @pytest.mark.asyncio
    async def test_ensure_quota_scope_accessible_by_domain_admin_with_user_dict(
        self,
        database_engine: ExtendedAsyncSAEngine,
        regular_user: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin accessing user quota scope within same domain with user dict"""
        quota_scope = QuotaScopeID.parse(f"user:{regular_user}")

        async with database_engine.begin_session() as session:
            # Should not raise any exception
            await ensure_quota_scope_accessible_by_user(
                session,
                quota_scope,
                domain_user_data_dict,
            )

    @pytest.mark.asyncio
    async def test_ensure_quota_scope_not_accessible_by_admin_from_other_domain(
        self,
        database_engine: ExtendedAsyncSAEngine,
        other_domain_user: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin cannot access user quota scope from different domain"""
        quota_scope = QuotaScopeID.parse(f"user:{other_domain_user}")

        async with database_engine.begin_session() as session:
            with pytest.raises(InvalidAPIParameters):
                await ensure_quota_scope_accessible_by_user(
                    session,
                    quota_scope,
                    domain_user_data_dict,
                )

    @pytest.mark.asyncio
    async def test_ensure_group_quota_scope_accessible_by_admin(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_group: UUID,
        domain_user_data_dict: dict[str, Any],
    ) -> None:
        """Test admin accessing project quota scope within same domain"""
        quota_scope = QuotaScopeID.parse(f"project:{test_group}")

        async with database_engine.begin_session() as session:
            # Should not raise any exception
            await ensure_quota_scope_accessible_by_user(
                session,
                quota_scope,
                domain_user_data_dict,
            )
