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

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import (
    RoleSource,
)
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
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
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

VFOLDER_HOST = "local:volume1"


class UserWithKeypair(NamedTuple):
    user_id: uuid.UUID
    email: str


async def _membership_cap(
    db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[bool, Permission | None]:
    """Whether the vfolder sits in the user's virtual scope, and under what cap.

    The v2 shape of what the legacy tables split into an AUTO/REF mapping plus
    permission rows: owning it is a membership with no cap, being shared it is the same
    membership under one.
    """
    async with db.begin_readonly_session() as db_sess:
        row = (
            await db_sess.execute(
                sa.select(EntityMembershipRow.permission_cap)
                .join(
                    VirtualScopeRow,
                    VirtualScopeRow.id == EntityMembershipRow.virtual_scope_id,
                )
                .where(
                    VirtualScopeRow.scope_type == USER_SCOPE_TYPE,
                    VirtualScopeRow.scope_id == user_id,
                    EntityMembershipRow.entity_type == VFOLDER_ENTITY_TYPE,
                    EntityMembershipRow.entity_id == vfolder_id,
                )
            )
        ).first()
    if row is None:
        return False, None
    return True, row.permission_cap


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
                ProjectRow,
                AssocGroupUserRow,
                VFolderRow,
                VFolderInvitationRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
                ObjectPermissionRow,
                PermissionRow,
                VirtualScopeRow,
                EntityMembershipRow,
                LabelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(
            db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup)
        )

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                id=domain_id,
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
        return DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

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
        test_domain: DomainFixtureData,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        group_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            group = ProjectRow(
                id=group_uuid,
                name=f"test-group-{group_uuid.hex[:8]}",
                domain_name=test_domain.domain_name,
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
        test_domain: DomainFixtureData,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
    ) -> UserWithKeypair:
        """Create old owner with keypair. Returns (user_uuid, email)."""
        return await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain.domain_name,
            test_user_resource_policy_name,
            test_keypair_resource_policy_name,
        )

    @pytest.fixture
    async def new_owner(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
    ) -> UserWithKeypair:
        """Create new owner with keypair. Returns (user_uuid, email)."""
        return await self._create_user_with_keypair(
            db_with_cleanup,
            test_domain.domain_name,
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
            domain_id = (
                await db_sess.execute(sa.select(DomainRow.id).where(DomainRow.name == domain_name))
            ).scalar_one()
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
                domain_id=domain_id,
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
                user=user_uuid,
                access_key=f"AK{user_uuid.hex[:18].upper()}",
                secret_key=SecretValue(f"SK{user_uuid.hex[:38]}"),
                is_active=True,
                is_admin=False,
                resource_policy=kp_policy_name,
                rate_limit=30000,
            )
            db_sess.add(keypair)

            # Sharing a vfolder enrolls it in the grantee's virtual scope, which the
            # real user-create path provisions.
            db_sess.add(
                VirtualScopeRow(
                    id=uuid.uuid4(),
                    scope_type=USER_SCOPE_TYPE,
                    scope_id=UserID(user_uuid),
                )
            )
            await db_sess.flush()

        return UserWithKeypair(user_id=user_uuid, email=email)

    async def test_ownership_transfer_cleans_up_old_owner_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain: DomainFixtureData,
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
                domain_name=test_domain.domain_name,
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

        # Verify A holds the vfolder before transfer
        granted, _ = await _membership_cap(db_with_cleanup, vfolder_id, user_a_id)
        assert granted, "Old owner should hold the vfolder before transfer"

        # Step 2: Transfer ownership to B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Step 3: the old owner holds nothing, the new one holds it uncapped
        granted_a, _ = await _membership_cap(db_with_cleanup, vfolder_id, user_a_id)
        assert not granted_a, "Old owner should hold nothing after transfer"

        granted_b, cap_b = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b, "New owner should hold the vfolder after transfer"
        assert cap_b is None, "An owner's hold carries no cap"

    async def test_round_trip_ownership_transfer_cleans_up_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain: DomainFixtureData,
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
                domain_name=test_domain.domain_name,
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

        # Verify A holds nothing after the first transfer
        granted_a, _ = await _membership_cap(db_with_cleanup, vfolder_id, user_a_id)
        assert not granted_a, "User A should hold nothing after the A -> B transfer"

        # Transfer B -> A (back to original owner)
        await repo.change_vfolder_ownership(vfolder_id, user_a_email)

        # Verify B holds nothing after the second transfer, and A holds it again
        granted_b, _ = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert not granted_b, "User B should hold nothing after the B -> A transfer"

        granted_a_after, cap_a_after = await _membership_cap(db_with_cleanup, vfolder_id, user_a_id)
        assert granted_a_after, "User A should hold the vfolder after ownership returned"
        assert cap_a_after is None, "An owner's hold carries no cap"

    async def test_invitee_rbac_cleaned_up_on_ownership_transfer(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain: DomainFixtureData,
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
                domain_name=test_domain.domain_name,
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

        # Verify B holds the vfolder under a cap before transfer
        granted_b, cap_b = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b, "User B should hold the vfolder as invitee"
        assert cap_b is not None, "An invitee's hold is capped"

        # Transfer ownership A -> B (B gets owner RBAC via Step 6)
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify B's hold loses its cap on becoming owner
        granted_b_after, cap_b_after = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b_after, "User B should hold the vfolder as owner"
        assert cap_b_after is None, "The invitee's cap should be gone once B owns it"

        # Transfer ownership B -> A
        await repo.change_vfolder_ownership(vfolder_id, user_a_email)

        # B accepts invitation again (must not raise unique constraint violation)
        await repo.create_vfolder_permission(
            vfolder_id, user_b_id, VFolderMountPermission.READ_ONLY
        )

        # Verify B holds it again, capped, after re-accepting
        granted_b_final, cap_b_final = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b_final, "User B should hold the vfolder after re-accepting"
        assert cap_b_final is not None, "An invitee's hold is capped"

    async def test_ownership_transfer_grants_new_owner_rbac(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain: DomainFixtureData,
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
                domain_name=test_domain.domain_name,
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

        # Verify B's hold is capped before transfer
        granted_b, cap_b = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b, "Invitee should hold the vfolder before transfer"
        assert cap_b is not None, "An invitee's hold is capped"

        # Transfer ownership to B
        await repo.change_vfolder_ownership(vfolder_id, user_b_email)

        # Verify B's hold loses its cap on becoming owner
        granted_b_after, cap_b_after = await _membership_cap(db_with_cleanup, vfolder_id, user_b_id)
        assert granted_b_after, "New owner should hold the vfolder after transfer"
        assert cap_b_after is None, "An owner's hold carries no cap"

    async def test_ownership_transfer_preserves_invitee_legacy_permission(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain: DomainFixtureData,
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
                domain_name=test_domain.domain_name,
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
