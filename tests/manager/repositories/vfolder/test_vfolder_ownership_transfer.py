"""
Tests for RBAC cleanup during vfolder ownership transfer.

Verifies that the ownership transfer logic properly cleans up
ObjectPermissionRow RBAC records to prevent unique constraint violations
on re-invite after A→B→A round-trip transfer.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import (
    BinarySize,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
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
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager

VFOLDER_HOST = "local:volume1"


class TestVFolderOwnershipTransferRBACCleanup:
    """Test that RoleManager.delete_object_permission_of_user correctly
    cleans up RBAC records during ownership transfer scenarios."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        yield database_engine

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ObjectPermissionRow))
            await db_sess.execute(sa.delete(PermissionGroupRow))
            await db_sess.execute(sa.delete(UserRoleRow))
            await db_sess.execute(sa.delete(RoleRow))
            await db_sess.execute(sa.delete(VFolderPermissionRow))
            await db_sess.execute(sa.delete(VFolderRow))
            await db_sess.execute(sa.delete(KeyPairRow))
            await db_sess.execute(sa.delete(GroupRow))
            await db_sess.execute(sa.delete(UserRow))
            await db_sess.execute(sa.delete(KeyPairResourcePolicyRow))
            await db_sess.execute(sa.delete(ProjectResourcePolicyRow))
            await db_sess.execute(sa.delete(UserResourcePolicyRow))
            await db_sess.execute(sa.delete(DomainRow))

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
                total_resource_slots={},
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
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
                total_resource_slots={},
                allowed_vfolder_hosts={},
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()
        return group_uuid

    async def _create_user_with_rbac_role(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        user_policy_name: str,
        kp_policy_name: str,
    ) -> tuple[uuid.UUID, str]:
        """Create a user with RBAC role, permission group, and keypair.
        Returns (user_uuid, email)."""
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

            # Create permission group scoped to this user
            perm_group = PermissionGroupRow(
                id=uuid.uuid4(),
                role_id=role_row.id,
                scope_type=ScopeType.USER,
                scope_id=str(user_uuid),
            )
            db_sess.add(perm_group)
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

    async def _add_object_permission(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        vfolder_id: uuid.UUID,
    ) -> None:
        """Add an ObjectPermissionRow for the given user and vfolder."""
        async with db.begin_session() as db_sess:
            perm_group = await db_sess.scalar(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.scope_id == str(user_id))
            )
            assert perm_group is not None
            obj_perm = ObjectPermissionRow(
                id=uuid.uuid4(),
                role_id=perm_group.role_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder_id),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm)
            await db_sess.flush()

    async def _count_object_permissions(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        vfolder_id: uuid.UUID,
    ) -> int:
        """Count ObjectPermissionRow records for a user and vfolder."""
        async with db.begin_session() as db_sess:
            perm_group = await db_sess.scalar(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.scope_id == str(user_id))
            )
            if perm_group is None:
                return 0
            count = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        ObjectPermissionRow.role_id == perm_group.role_id,
                        ObjectPermissionRow.entity_id == str(vfolder_id),
                    )
                )
            )
            return count or 0

    async def test_delete_object_permission_cleans_up_new_owner_invitee_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        test_group: uuid.UUID,
    ) -> None:
        """
        Verify that delete_object_permission_of_user removes the new owner's
        invitee RBAC records during ownership transfer.

        Scenario: B was invited to A's vfolder (B has ObjectPermissionRow).
        On ownership transfer A→B, B's invitee RBAC records must be removed.
        """
        role_manager = RoleManager()

        user_a_id, _ = await self._create_user_with_rbac_role(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )
        user_b_id, _ = await self._create_user_with_rbac_role(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

        vfolder_id = uuid.uuid4()

        # Create vfolder owned by A
        async with db_with_cleanup.begin_session() as db_sess:
            vfolder_row = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                domain_name=test_domain_name,
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.OWNER_PERM,
                host=VFOLDER_HOST,
                creator=f"test-{user_a_id.hex[:8]}@example.com",
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

        # B has invitee RBAC permission (simulates accepted invitation)
        await self._add_object_permission(db_with_cleanup, user_b_id, vfolder_id)

        # Verify B has RBAC permission before cleanup
        count_before = await self._count_object_permissions(db_with_cleanup, user_b_id, vfolder_id)
        assert count_before == 1, "User B should have RBAC permission before cleanup"

        # Simulate ownership transfer cleanup: delete B's invitee RBAC records
        async with db_with_cleanup.begin_session() as db_session:
            await role_manager.delete_object_permission_of_user(db_session, user_b_id, vfolder_id)

        # Verify B's RBAC records are cleaned up
        count_after = await self._count_object_permissions(db_with_cleanup, user_b_id, vfolder_id)
        assert count_after == 0, "User B's RBAC permission should be removed after cleanup"

    async def test_round_trip_transfer_no_unique_constraint_violation(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        test_group: uuid.UUID,
    ) -> None:
        """
        Regression test for BA-5277:
        1. A owns vfolder, B has invitee RBAC permission
        2. Transfer A→B: B's invitee RBAC records cleaned up
        3. Transfer B→A: A's RBAC records cleaned up
        4. Re-invite B: inserting new ObjectPermissionRow must NOT
           hit unique constraint violation
        """
        role_manager = RoleManager()

        user_a_id, _ = await self._create_user_with_rbac_role(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )
        user_b_id, _ = await self._create_user_with_rbac_role(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

        vfolder_id = uuid.uuid4()

        # Create vfolder owned by A
        async with db_with_cleanup.begin_session() as db_sess:
            vfolder_row = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                domain_name=test_domain_name,
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.OWNER_PERM,
                host=VFOLDER_HOST,
                creator=f"test-{user_a_id.hex[:8]}@example.com",
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

        # B has invitee RBAC permission
        await self._add_object_permission(db_with_cleanup, user_b_id, vfolder_id)
        # A has owner RBAC permission
        await self._add_object_permission(db_with_cleanup, user_a_id, vfolder_id)

        # Step 1: Transfer A→B — clean up B's invitee records and A's owner records
        async with db_with_cleanup.begin_session() as db_session:
            await role_manager.delete_object_permission_of_user(db_session, user_b_id, vfolder_id)
        async with db_with_cleanup.begin_session() as db_session:
            await role_manager.delete_object_permission_of_user(db_session, user_a_id, vfolder_id)

        assert await self._count_object_permissions(db_with_cleanup, user_b_id, vfolder_id) == 0
        assert await self._count_object_permissions(db_with_cleanup, user_a_id, vfolder_id) == 0

        # Step 2: Transfer B→A — no records to clean up, should not error
        # (both users have no RBAC records at this point)

        # Step 3: Re-invite B — must not hit unique constraint violation
        await self._add_object_permission(db_with_cleanup, user_b_id, vfolder_id)

        count_b_final = await self._count_object_permissions(db_with_cleanup, user_b_id, vfolder_id)
        assert count_b_final == 1, "User B should have new RBAC permission after re-invite"

    async def test_delete_permission_no_error_when_no_records_exist(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
        test_group: uuid.UUID,
    ) -> None:
        """
        Verify that deleting RBAC permissions for a user who has a permission
        group but no object permissions does not raise an error.
        """
        role_manager = RoleManager()

        user_id, _ = await self._create_user_with_rbac_role(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

        vfolder_id = uuid.uuid4()

        # User has a permission group but no ObjectPermissionRow for this vfolder
        # delete_object_permission_of_user should succeed without error
        async with db_with_cleanup.begin_session() as db_session:
            await role_manager.delete_object_permission_of_user(db_session, user_id, vfolder_id)

        count = await self._count_object_permissions(db_with_cleanup, user_id, vfolder_id)
        assert count == 0
