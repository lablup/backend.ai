"""Tests for GroupDBSource.resolve_users_by_name()"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow, association_groups_users
from ai.backend.manager.models.group.row import AssocGroupUserRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.group.db_source import GroupDBSource
from ai.backend.testutils.db import with_tables


class TestResolveUsersByName:
    """Tests for GroupDBSource.resolve_users_by_name"""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                AssocGroupUserRow,
                AssociationScopesEntitiesRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return domain_name

    @pytest.fixture
    async def other_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"other-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    name=domain_name,
                    description="Other domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return domain_name

    @pytest.fixture
    async def user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    description="Test project",
                    is_active=True,
                    domain_name=test_domain,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
                )
            )
            await session.commit()
        return project_id

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        policy_name: str,
        password_info: PasswordInfo,
        *,
        username: str | None = None,
        email: str | None = None,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> tuple[uuid.UUID, str, str | None]:
        """Create a user and return (uuid, email, username)."""
        user_uuid = uuid.uuid4()
        if username is None:
            username = f"user-{user_uuid.hex[:8]}"
        if email is None:
            email = f"user-{user_uuid.hex[:8]}@example.com"
        async with db.begin_session() as session:
            session.add(
                UserRow(
                    uuid=user_uuid,
                    username=username,
                    email=email,
                    password=password_info,
                    need_password_change=False,
                    full_name="Test User",
                    description="",
                    status=status,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                )
            )
            await session.commit()
        return (user_uuid, email, username)

    async def _pre_assign_user(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        """Manually insert an AssocGroupUserRow to simulate pre-assignment."""
        async with db.begin_session() as session:
            await session.execute(
                sa.insert(association_groups_users).values(user_id=user_id, group_id=project_id)
            )
            await session.commit()

    @pytest.fixture
    async def same_domain_user_1(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> tuple[uuid.UUID, str, str]:
        uid, email, username = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="alice",
            email="alice@example.com",
        )
        assert username is not None
        return (uid, email, username)

    @pytest.fixture
    async def same_domain_user_2(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> tuple[uuid.UUID, str, str]:
        uid, email, username = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="bob",
            email="bob@example.com",
        )
        assert username is not None
        return (uid, email, username)

    @pytest.fixture
    async def cross_domain_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> tuple[uuid.UUID, str, str]:
        uid, email, username = await self._create_user(
            db_with_cleanup,
            other_domain,
            user_resource_policy,
            test_password_info,
            username="charlie",
            email="charlie@other.com",
        )
        assert username is not None
        return (uid, email, username)

    @pytest.fixture
    async def inactive_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> tuple[uuid.UUID, str, str]:
        uid, email, username = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="dave_inactive",
            email="dave@example.com",
            status=UserStatus.INACTIVE,
        )
        assert username is not None
        return (uid, email, username)

    @pytest.fixture
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

    # --- Test cases ---

    async def test_resolve_by_email(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve a user by email address."""
        uid, email, _ = same_domain_user_1
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [email])

        assert user_ids == [uid]
        assert failed == []

    async def test_resolve_by_username(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve a user by username."""
        uid, _, username = same_domain_user_1
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [username])

        assert user_ids == [uid]
        assert failed == []

    async def test_resolve_mixed_email_and_username(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
        same_domain_user_2: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve users using a mix of emails and usernames."""
        uid1, email1, _ = same_domain_user_1
        uid2, _, username2 = same_domain_user_2
        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, [email1, username2]
        )

        assert set(user_ids) == {uid1, uid2}
        assert failed == []

    async def test_nonexistent_name_in_failed(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
    ) -> None:
        """Non-existent email/username appears in failed_names."""
        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, ["nobody@example.com"]
        )

        assert user_ids == []
        assert failed == ["nobody@example.com"]

    async def test_cross_domain_user_in_failed(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        cross_domain_user: tuple[uuid.UUID, str, str],
    ) -> None:
        """User from a different domain appears in failed_names."""
        _, email, _ = cross_domain_user
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [email])

        assert user_ids == []
        assert failed == [email]

    async def test_already_assigned_user_in_failed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
    ) -> None:
        """Already-assigned user appears in failed_names."""
        uid, email, _ = same_domain_user_1
        await self._pre_assign_user(db_with_cleanup, uid, test_project)

        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [email])

        assert user_ids == []
        assert failed == [email]

    async def test_inactive_user_resolves_successfully(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        inactive_user: tuple[uuid.UUID, str, str],
    ) -> None:
        """Inactive users are resolved (no status restriction)."""
        uid, email, _ = inactive_user
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [email])

        assert user_ids == [uid]
        assert failed == []

    async def test_mixed_valid_and_invalid_names(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
        cross_domain_user: tuple[uuid.UUID, str, str],
    ) -> None:
        """Valid names resolve; invalid names appear in failed_names."""
        uid, valid_email, _ = same_domain_user_1
        _, invalid_email, _ = cross_domain_user

        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, [valid_email, invalid_email, "ghost@nowhere.com"]
        )

        assert user_ids == [uid]
        assert set(failed) == {invalid_email, "ghost@nowhere.com"}

    async def test_all_names_fail(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        cross_domain_user: tuple[uuid.UUID, str, str],
    ) -> None:
        """When all names fail, user_ids is empty."""
        _, email, _ = cross_domain_user
        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, [email, "fake@example.com"]
        )

        assert user_ids == []
        assert set(failed) == {email, "fake@example.com"}

    async def test_empty_names_returns_empty(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
    ) -> None:
        """Empty names list returns ([], [])."""
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [])

        assert user_ids == []
        assert failed == []

    async def test_duplicate_names_deduplicated(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
    ) -> None:
        """Duplicate names in input resolve to a single user."""
        uid, email, _ = same_domain_user_1
        user_ids, failed = await group_db_source.resolve_users_by_name(test_project, [email, email])

        assert user_ids == [uid]
        assert failed == []

    async def test_ambiguity_all_failure_reasons_same_output(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
        cross_domain_user: tuple[uuid.UUID, str, str],
    ) -> None:
        """All failure reasons (not found, wrong domain, already assigned) produce
        the same failed_names output without distinguishing the cause."""
        uid, valid_email, _ = same_domain_user_1
        _, cross_email, _ = cross_domain_user

        # Pre-assign user_1
        await self._pre_assign_user(db_with_cleanup, uid, test_project)

        # All three failure types: already assigned, cross-domain, non-existent
        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, [valid_email, cross_email, "ghost@x.com"]
        )

        assert user_ids == []
        assert set(failed) == {valid_email, cross_email, "ghost@x.com"}

    async def test_collision_email_vs_username_treated_as_failed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> None:
        """When a name matches one user's email and another user's username,
        the name is treated as ambiguous and appears in failed_names."""
        # user_a has email "shared@example.com"
        uid_a, _, _ = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="user_a",
            email="shared@example.com",
        )
        # user_b has username "shared@example.com"
        uid_b, _, _ = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="shared@example.com",
            email="user_b@example.com",
        )

        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, ["shared@example.com"]
        )

        # Ambiguous: neither user should be assigned
        assert user_ids == []
        assert failed == ["shared@example.com"]

    async def test_same_user_email_and_username_both_match(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: tuple[uuid.UUID, str, str],
    ) -> None:
        """When email and username both match the SAME user, it resolves correctly."""
        uid, email, username = same_domain_user_1
        user_ids, failed = await group_db_source.resolve_users_by_name(
            test_project, [email, username]
        )

        # Both names resolve to the same user — deduplicated
        assert user_ids == [uid]
        assert failed == []
