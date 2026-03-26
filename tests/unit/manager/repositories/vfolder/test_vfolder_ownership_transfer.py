"""
Tests for RBAC cleanup during vfolder ownership transfer.

Verifies that change_vfolder_ownership properly revokes the old owner's
RBAC records (scope-entity mapping and permissions) when transferring
ownership to a new user.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import NamedTuple

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
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RelationType,
    RoleSource,
)
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


class UserWithKeypair(NamedTuple):
    user_id: uuid.UUID
    email: str


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
    def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

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

    @pytest.fixture
    async def old_owner(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
    ) -> UserWithKeypair:
        """Create old owner with keypair. Returns (user_uuid, email)."""
        return await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

    @pytest.fixture
    async def new_owner(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
    ) -> UserWithKeypair:
        """Create new owner with keypair. Returns (user_uuid, email)."""
        return await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

    async def _create_user_with_keypair(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        user_policy_name: str,
        kp_policy_name: str,
    ) -> UserWithKeypair:
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

            role_id = uuid.uuid4()
            role_row = RoleRow(
                id=role_id,
                name=f"user-role-{user_uuid.hex[:8]}",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role_row)
            await db_sess.flush()

            user_role_row = UserRoleRow(
                id=uuid.uuid4(),
                user_id=user_uuid,
                role_id=role_id,
            )
            db_sess.add(user_role_row)

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

        return UserWithKeypair(user_id=user_uuid, email=email)

    async def test_ownership_transfer_cleans_up_old_owner_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_group: uuid.UUID,
        old_owner: UserWithKeypair,
        new_owner: UserWithKeypair,
    ) -> None:
        """
        Verify that after ownership transfer, the old owner's RBAC records
        (scope-entity mapping and permissions) are cleaned up.
        """
        repo = vfolder_repository
        user_a_id, user_a_email = old_owner.user_id, old_owner.email
        user_b_id, user_b_email = new_owner.user_id, new_owner.email

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

            # Verify new owner B's RBAC records are created
            b_mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_b_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                        AssociationScopesEntitiesRow.relation_type == RelationType.AUTO,
                    )
                )
            )
            assert b_mapping_count == 1, (
                "New owner should have AUTO scope-entity mapping after transfer"
            )

            b_perm_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(
                    sa.and_(
                        PermissionRow.scope_id == str(vfolder_id),
                        PermissionRow.entity_type == EntityType.VFOLDER,
                        PermissionRow.operation == OperationType.READ,
                    )
                )
                .join(UserRoleRow, UserRoleRow.role_id == PermissionRow.role_id)
                .where(UserRoleRow.user_id == user_b_id)
            )
            assert b_perm_count == 1, "New owner should have READ permission after transfer"

    async def test_round_trip_ownership_transfer_cleans_up_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_group: uuid.UUID,
        old_owner: UserWithKeypair,
        new_owner: UserWithKeypair,
    ) -> None:
        """
        Verify the round-trip scenario (A -> B -> A) works correctly:
        after transferring ownership back to the original owner,
        the intermediate owner's RBAC records are cleaned up and
        the original owner has valid RBAC records.
        """
        repo = vfolder_repository
        user_a_id, user_a_email = old_owner.user_id, old_owner.email
        user_b_id, user_b_email = new_owner.user_id, new_owner.email

        vfolder_id = uuid.uuid4()

        # Create vfolder owned by A with RBAC permission
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

        await repo.create_vfolder_permission(
            vfolder_id, user_a_id, VFolderMountPermission.OWNER_PERM
        )

        # Transfer A -> B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify A's RBAC records are cleaned up after first transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            mapping_count_a = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_a_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert mapping_count_a == 0, (
                "User A's scope-entity mapping should be removed after A -> B transfer"
            )

        # Transfer B -> A (back to original owner)
        await repo.change_vfolder_ownership(vfolder_id, user_a_email)

        # Verify B's RBAC records are cleaned up after second transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            mapping_count_b = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_b_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert mapping_count_b == 0, (
                "User B's scope-entity mapping should be removed after B -> A transfer"
            )

        # Verify A now has valid RBAC records as the new owner
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            mapping_count_a_after = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_a_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert mapping_count_a_after == 1, (
                "User A should have scope-entity mapping after ownership returned"
            )

    async def test_invitee_rbac_cleaned_up_on_ownership_transfer(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_group: uuid.UUID,
        old_owner: UserWithKeypair,
        new_owner: UserWithKeypair,
    ) -> None:
        """
        Regression test for BA-5277:
        1. A owns vfolder, invites B (B accepts -> gets RBAC permission as invitee)
        2. Transfer ownership A -> B (B gets owner RBAC, invitee permission preserved)
        3. Transfer ownership B -> A
        4. A invites B again -> B accepts (must not hit unique constraint violation)
        """
        repo = vfolder_repository
        user_a_id, user_a_email = old_owner.user_id, old_owner.email
        user_b_id, user_b_email = new_owner.user_id, new_owner.email

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

        # A gets owner permission
        await repo.create_vfolder_permission(
            vfolder_id, user_a_id, VFolderMountPermission.OWNER_PERM
        )

        # B gets invitee permission (simulates accepting an invitation)
        await repo.create_vfolder_permission(
            vfolder_id, user_b_id, VFolderMountPermission.READ_ONLY
        )

        # Verify B has RBAC permission before transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            perm_count_b = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(PermissionRow.scope_id == str(vfolder_id))
                .join(UserRoleRow, UserRoleRow.role_id == PermissionRow.role_id)
                .where(UserRoleRow.user_id == user_b_id)
            )
            assert perm_count_b is not None and perm_count_b > 0, (
                "User B should have RBAC permissions as invitee"
            )

        # Transfer ownership A -> B (B gets owner RBAC via Step 6)
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify B has owner RBAC after becoming owner
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            b_mapping_after = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow.relation_type).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_b_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert b_mapping_after == RelationType.AUTO, (
                "User B's mapping should be upgraded to AUTO after becoming owner"
            )

        # Transfer ownership B -> A
        await repo.change_vfolder_ownership(vfolder_id, user_a_email)

        # B accepts invitation again (must not raise unique constraint violation)
        await repo.create_vfolder_permission(
            vfolder_id, user_b_id, VFolderMountPermission.READ_ONLY
        )

        # Verify B has new RBAC permission
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            perm_count_b_final = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(PermissionRow.scope_id == str(vfolder_id))
                .join(UserRoleRow, UserRoleRow.role_id == PermissionRow.role_id)
                .where(UserRoleRow.user_id == user_b_id)
            )
            assert perm_count_b_final is not None and perm_count_b_final > 0, (
                "User B should have RBAC permissions after re-accepting invitation"
            )

    async def test_ownership_transfer_grants_new_owner_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_group: uuid.UUID,
        old_owner: UserWithKeypair,
        new_owner: UserWithKeypair,
    ) -> None:
        """
        Verify that when B was previously an invitee (REF scope-entity mapping),
        ownership transfer upgrades B's mapping to AUTO and grants owner permissions.
        """
        repo = vfolder_repository
        user_a_id, user_a_email = old_owner.user_id, old_owner.email
        user_b_id, user_b_email = new_owner.user_id, new_owner.email

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

        # Grant A owner permission
        await repo.create_vfolder_permission(
            vfolder_id, user_a_id, VFolderMountPermission.OWNER_PERM
        )

        # Grant B invitee permission (creates REF scope-entity mapping)
        await repo.create_vfolder_permission(
            vfolder_id, user_b_id, VFolderMountPermission.READ_ONLY
        )

        # Verify B has REF mapping before transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            b_mapping = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow.relation_type).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_b_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert b_mapping == RelationType.REF, "Invitee should have REF mapping before transfer"

        # Transfer ownership to B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify B's mapping is upgraded to AUTO
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            b_mapping_after = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow.relation_type).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_b_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert b_mapping_after == RelationType.AUTO, (
                "New owner's mapping should be upgraded from REF to AUTO"
            )

            # Verify B has owner-level READ permission
            b_perm_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(
                    sa.and_(
                        PermissionRow.scope_id == str(vfolder_id),
                        PermissionRow.entity_type == EntityType.VFOLDER,
                        PermissionRow.operation == OperationType.READ,
                    )
                )
                .join(UserRoleRow, UserRoleRow.role_id == PermissionRow.role_id)
                .where(UserRoleRow.user_id == user_b_id)
            )
            assert (b_perm_count or 0) >= 1, "New owner should have READ permission after transfer"

    async def test_ownership_transfer_preserves_invitee_legacy_permission(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_group: uuid.UUID,
        old_owner: UserWithKeypair,
        new_owner: UserWithKeypair,
    ) -> None:
        """
        Verify that after ownership transfer, the new owner's legacy
        vfolder_permissions record is preserved (not deleted).
        """
        repo = vfolder_repository
        user_a_id, user_a_email = old_owner.user_id, old_owner.email
        user_b_id, user_b_email = new_owner.user_id, new_owner.email

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

        # Grant B invitee permission (legacy vfolder_permissions record)
        await repo.create_vfolder_permission(
            vfolder_id, user_b_id, VFolderMountPermission.READ_ONLY
        )

        # Verify B has legacy permission before transfer
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            perm_count_before = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(
                    sa.and_(
                        VFolderPermissionRow.vfolder == vfolder_id,
                        VFolderPermissionRow.user == user_b_id,
                    )
                )
            )
            assert perm_count_before == 1, "Invitee should have legacy permission before transfer"

        # Transfer ownership to B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify B's legacy permission is preserved
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            perm_count_after = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(
                    sa.and_(
                        VFolderPermissionRow.vfolder == vfolder_id,
                        VFolderPermissionRow.user == user_b_id,
                    )
                )
            )
            assert perm_count_after == 1, (
                "New owner's legacy vfolder_permissions should be preserved after transfer"
            )
