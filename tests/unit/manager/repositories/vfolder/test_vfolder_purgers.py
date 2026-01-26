"""
Tests for vfolder purgers functionality.
Tests the purger pattern implementation for vfolder-related deletions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.vfolder.types import VFolderMountPermission, VFolderOwnershipType
from ai.backend.manager.models.agent import AgentRow  # noqa: F401
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow  # noqa: F401
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder.row import (
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.base.purger import execute_batch_purger
from ai.backend.manager.repositories.vfolder.purgers import (
    create_vfolder_invitation_purger,
    create_vfolder_permission_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestVFolderPurgersIntegration:
    """Integration tests for vfolder purgers with real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                VFolderRow,
                VFolderInvitationRow,
                VFolderPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
        return domain_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a user resource policy."""
        policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
        return policy_name

    @pytest.fixture
    async def sample_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        user_resource_policy: str,
    ) -> UserRow:
        """Create a test user."""
        user_uuid = uuid.uuid4()
        password_info = PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user for integration tests",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=sample_domain,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    @pytest.fixture
    async def sample_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        sample_user: UserRow,
    ) -> VFolderRow:
        """Create a test vfolder."""
        vfolder_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            vfolder = VFolderRow(
                id=vfolder_id,
                host="local",
                domain_name=sample_domain,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, sample_user.uuid),
                name=f"test-vfolder-{uuid.uuid4().hex[:8]}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.USER,
                user=sample_user.uuid,
            )
            session.add(vfolder)
            await session.flush()
            await session.refresh(vfolder)
            return vfolder

    @pytest.fixture
    async def sample_invitations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_vfolder: VFolderRow,
        sample_user: UserRow,
    ) -> list[VFolderInvitationRow]:
        """Create test vfolder invitations."""
        invitations: list[VFolderInvitationRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                invitation = VFolderInvitationRow(
                    vfolder=sample_vfolder.id,
                    inviter=sample_user.email,
                    invitee=f"invitee-{i}@example.com",
                    permission=VFolderMountPermission.READ_ONLY,
                )
                session.add(invitation)
                invitations.append(invitation)
            await session.flush()
            for inv in invitations:
                await session.refresh(inv)
        return invitations

    @pytest.fixture
    async def sample_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_vfolder: VFolderRow,
        sample_user: UserRow,
    ) -> list[VFolderPermissionRow]:
        """Create test vfolder permissions."""
        permissions: list[VFolderPermissionRow] = []
        async with db_with_cleanup.begin_session() as session:
            for _ in range(3):
                # Create additional users for permissions
                perm_user_uuid = uuid.uuid4()
                perm_user = UserRow(
                    uuid=perm_user_uuid,
                    username=f"permuser-{uuid.uuid4().hex[:8]}",
                    email=f"perm-{uuid.uuid4().hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name="Permission User",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=sample_vfolder.domain_name,
                    role=UserRole.USER,
                    resource_policy=sample_user.resource_policy,
                )
                session.add(perm_user)
                await session.flush()

                permission = VFolderPermissionRow(
                    vfolder=sample_vfolder.id,
                    user=perm_user_uuid,
                    permission=VFolderMountPermission.READ_ONLY,
                )
                session.add(permission)
                permissions.append(permission)
            await session.flush()
            for perm in permissions:
                await session.refresh(perm)
        return permissions

    @pytest.mark.asyncio
    async def test_purge_vfolder_invitations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_vfolder: VFolderRow,
        sample_invitations: list[VFolderInvitationRow],
    ) -> None:
        """Test purging vfolder invitations."""
        vfolder_ids = [sample_vfolder.id]

        # Verify invitations exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderInvitationRow)
                .where(VFolderInvitationRow.vfolder.in_(vfolder_ids))
            )
            assert count == len(sample_invitations)

        # Purge invitations
        async with db_with_cleanup.begin_session() as session:
            purger = create_vfolder_invitation_purger(vfolder_ids)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_invitations)

        # Verify invitations are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderInvitationRow)
                .where(VFolderInvitationRow.vfolder.in_(vfolder_ids))
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_vfolder_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_vfolder: VFolderRow,
        sample_permissions: list[VFolderPermissionRow],
    ) -> None:
        """Test purging vfolder permissions."""
        vfolder_ids = [sample_vfolder.id]

        # Verify permissions exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(VFolderPermissionRow.vfolder.in_(vfolder_ids))
            )
            assert count == len(sample_permissions)

        # Purge permissions
        async with db_with_cleanup.begin_session() as session:
            purger = create_vfolder_permission_purger(vfolder_ids)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_permissions)

        # Verify permissions are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(VFolderPermissionRow.vfolder.in_(vfolder_ids))
            )
            assert count == 0
