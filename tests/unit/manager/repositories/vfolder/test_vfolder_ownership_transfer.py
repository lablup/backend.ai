"""
Tests for RBAC cleanup during vfolder ownership transfer.

Verifies that change_vfolder_ownership properly revokes the old owner's
RBAC records (scope-entity mapping and permissions) when transferring
ownership to a new user.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.types import EntityType, RoleSource
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables

VFOLDER_HOST = "local:volume1"


class TestVFolderOwnershipTransferRBACCleanup:
    """Test that ownership transfer cleans up old owner's RBAC records."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
                VFolderRow,
                VFolderInvitationRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
                ObjectPermissionRow,
                PermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap({
                    VFOLDER_HOST: {
                        VFolderHostPermission.CREATE,
                        VFolderHostPermission.MOUNT_IN_SESSION,
                    }
                }),
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()
        return domain_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            kp_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
                allowed_vfolder_hosts=VFolderHostPermissionMap({
                    VFOLDER_HOST: {
                        VFolderHostPermission.CREATE,
                        VFolderHostPermission.MOUNT_IN_SESSION,
                    }
                }),
            )
            db_sess.add(kp_policy)
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(project_policy)
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        group_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test-group-{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                description="Test group",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()
        return group_uuid

    async def _create_user_with_keypair(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        user_policy_name: str,
        kp_policy_name: str,
    ) -> tuple[uuid.UUID, str]:
        """Create a user with RBAC role and keypair. Returns (user_uuid, email)."""
        user_uuid = uuid.uuid4()
        email = f"test-{user_uuid.hex[:8]}@example.com"
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=email,
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=user_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

            role_row = RoleRow(
                id=uuid.uuid4(),
                name=f"user-role-{user_uuid.hex[:8]}",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role_row)
            await db_sess.flush()

            user_role_row = UserRoleRow(
                id=uuid.uuid4(),
                user_id=user_uuid,
                role_id=role_row.id,
            )
            db_sess.add(user_role_row)
            await db_sess.flush()

            keypair = KeyPairRow(
                user_id=email,
                user=user_uuid,
                access_key=f"AK{user_uuid.hex[:18].upper()}",
                secret_key=f"SK{user_uuid.hex[:38]}",
                is_active=True,
                is_admin=False,
                resource_policy=kp_policy_name,
                rate_limit=30000,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        return user_uuid, email

    async def test_ownership_transfer_cleans_up_old_owner_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        test_group: uuid.UUID,
    ) -> None:
        """
        Verify that after ownership transfer, the old owner's RBAC records
        (scope-entity mapping and permissions) are cleaned up.
        """
        repo = VfolderRepository(db=db_with_cleanup)

        # Create user A (old owner) and user B (new owner) with keypairs
        user_a_id, user_a_email = await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )
        user_b_id, user_b_email = await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

        vfolder_id = uuid.uuid4()

        # Step 1: Create vfolder owned by A, then grant A permission (simulating creation flow)
        async with db_with_cleanup.begin_session() as db_sess:
            vfolder_row = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                domain_name=test_domain_name,
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.OWNER_PERM,
                host=VFOLDER_HOST,
                creator=user_a_email,
                ownership_type=VFolderOwnershipType.USER,
                user=user_a_id,
                group=test_group,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                quota_scope_id=f"user:{user_a_id}",
            )
            db_sess.add(vfolder_row)
            await db_sess.flush()

        # Grant A owner permission (creates scope-entity mapping + permissions)
        await repo.create_vfolder_permission(
            vfolder_id, user_a_id, VFolderMountPermission.OWNER_PERM
        )

        # Verify A's RBAC records exist before transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_a_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert mapping_count == 1, "Old owner should have scope-entity mapping before transfer"

        # Step 2: Transfer ownership to B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Step 3: Verify old owner A's RBAC records are cleaned up
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            mapping_count_after = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_a_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert mapping_count_after == 0, (
                "Old owner's scope-entity mapping should be removed after transfer"
            )

            perm_count_after = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(
                    sa.and_(
                        PermissionRow.scope_id == str(vfolder_id),
                        PermissionRow.entity_type == EntityType.VFOLDER,
                    )
                )
                .join(UserRoleRow, UserRoleRow.role_id == PermissionRow.role_id)
                .where(UserRoleRow.user_id == user_a_id)
            )
            assert perm_count_after == 0, "Old owner's permissions should be removed after transfer"
