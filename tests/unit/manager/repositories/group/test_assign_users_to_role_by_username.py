"""Tests for GroupDBSource.resolve_users_by_username()"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import ResolveUsersByUsernameResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
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


class TestResolveUsersByUsername:
    """Tests for GroupDBSource.resolve_users_by_username — pure name→UUID resolution."""

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

    @pytest.fixture
    async def user_alice(
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
    async def user_bob(
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
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

    # --- Helpers ---

    async def _resolve(
        self, db_source: GroupDBSource, names: list[str]
    ) -> ResolveUsersByUsernameResult:
        return await db_source.resolve_users_by_username(names)

    # --- Test cases ---

    async def test_resolve_by_email(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve a user by email address."""
        uid, email, _ = user_alice
        result = await self._resolve(group_db_source, [email])

        assert result.name_to_uid == {email: uid}
        assert result.failed_names == []

    async def test_resolve_by_username(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve a user by username."""
        uid, _, username = user_alice
        result = await self._resolve(group_db_source, [username])

        assert result.name_to_uid == {username: uid}
        assert result.failed_names == []

    async def test_resolve_mixed_email_and_username(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
        user_bob: tuple[uuid.UUID, str, str],
    ) -> None:
        """Resolve users using a mix of emails and usernames."""
        uid1, email1, _ = user_alice
        uid2, _, username2 = user_bob
        result = await self._resolve(group_db_source, [email1, username2])

        assert result.name_to_uid == {email1: uid1, username2: uid2}
        assert result.failed_names == []

    async def test_nonexistent_name_in_failed(
        self,
        group_db_source: GroupDBSource,
    ) -> None:
        """Non-existent email/username appears in failed_names."""
        result = await self._resolve(group_db_source, ["nobody@example.com"])

        assert result.name_to_uid == {}
        assert result.failed_names == ["nobody@example.com"]

    async def test_inactive_user_resolves_successfully(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> None:
        """Inactive users are resolved (no status restriction)."""
        uid, email, _ = await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="inactive_dave",
            email="dave@example.com",
            status=UserStatus.INACTIVE,
        )
        result = await self._resolve(group_db_source, [email])

        assert result.name_to_uid == {email: uid}
        assert result.failed_names == []

    async def test_mixed_valid_and_invalid_names(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
    ) -> None:
        """Valid names resolve; invalid names appear in failed_names."""
        uid, email, _ = user_alice
        result = await self._resolve(
            group_db_source,
            [
                email,
                "ghost@nowhere.com",
            ],
        )

        assert result.name_to_uid == {email: uid}
        assert result.failed_names == ["ghost@nowhere.com"]

    async def test_empty_names_returns_empty(
        self,
        group_db_source: GroupDBSource,
    ) -> None:
        """Empty names list returns ({}, [])."""
        result = await self._resolve(group_db_source, [])

        assert result.name_to_uid == {}
        assert result.failed_names == []

    async def test_duplicate_names_deduplicated(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
    ) -> None:
        """Duplicate names in input resolve to a single entry."""
        uid, email, _ = user_alice
        result = await self._resolve(group_db_source, [email, email])

        assert result.name_to_uid == {email: uid}
        assert result.failed_names == []

    async def test_collision_email_vs_username_treated_as_failed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> None:
        """When a name matches one user's email and another user's username,
        the name is treated as ambiguous and appears in failed_names."""
        await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="user_a",
            email="shared@example.com",
        )
        await self._create_user(
            db_with_cleanup,
            test_domain,
            user_resource_policy,
            test_password_info,
            username="shared@example.com",
            email="user_b@example.com",
        )

        result = await self._resolve(group_db_source, ["shared@example.com"])

        assert result.name_to_uid == {}
        assert result.failed_names == ["shared@example.com"]

    async def test_same_user_email_and_username_both_match(
        self,
        group_db_source: GroupDBSource,
        user_alice: tuple[uuid.UUID, str, str],
    ) -> None:
        """When email and username both match the SAME user, both resolve correctly."""
        uid, email, username = user_alice
        result = await self._resolve(group_db_source, [email, username])

        assert result.name_to_uid == {email: uid, username: uid}
        assert result.failed_names == []
