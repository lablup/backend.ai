"""The mount level filter of a vfolder search, against the level each user mounts at."""

from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.queries import mount_permission_of_user
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


class _FolderOwner(enum.StrEnum):
    CALLER = "caller"
    ANOTHER_USER = "another-user"
    PROJECT = "project"


@dataclass(frozen=True)
class _MountPermissionCase:
    name: str
    folder_owner: _FolderOwner
    default_mount_permission: VFolderMountPolicy
    expected: VFolderMountPolicy
    caller_role: UserRole = UserRole.USER
    caller_role_grants_read: bool = True
    folder_has_node: bool = True
    policy_of_caller: VFolderMountPolicy | None = None
    policy_of_another_user: VFolderMountPolicy | None = None


@dataclass(frozen=True)
class _MountPermissionSituation:
    caller_id: UserID
    vfolder_id: VFolderUUID
    expected: VFolderMountPolicy


class TestMountPermissionFilter:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                ProjectRow,
                RoleRow,
                UserRoleRow,
                PermissionRow,
                VFolderRow,
                VFolderUserMountPolicyRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def mount_permission_situation(
        self, db_with_cleanup: ExtendedAsyncSAEngine, case: _MountPermissionCase
    ) -> _MountPermissionSituation:
        domain_id, domain_name = DomainID(uuid.uuid4()), "test-domain"
        caller_id, another_user_id = UserID(uuid.uuid4()), UserID(uuid.uuid4())
        project_id = ProjectID(uuid.uuid4())
        role_id = RoleID(uuid.uuid4())
        vfolder_id = VFolderUUID(uuid.uuid4())
        owner_user_id = {
            _FolderOwner.CALLER: caller_id,
            _FolderOwner.ANOTHER_USER: another_user_id,
            _FolderOwner.PROJECT: None,
        }[case.folder_owner]
        seeder = VirtualEntitySeeder()
        async with db_with_cleanup.begin_session() as sess:
            sess.add_all([
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()),
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                ),
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                ),
            ])
            await sess.flush()
            sess.add_all([
                UserRow(
                    uuid=user_id,
                    username=f"user-{user_id.hex[:8]}",
                    email=f"{user_id.hex[:8]}@example.com",
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    domain_name=domain_name,
                    domain_id=domain_id,
                    role=user_role,
                    resource_policy="default",
                )
                for user_id, user_role in (
                    (caller_id, case.caller_role),
                    (another_user_id, UserRole.USER),
                )
            ])
            sess.add(
                ProjectRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
            await sess.flush()
            sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name="test-folder",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"project:{project_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    default_mount_permission=case.default_mount_permission,
                    ownership_type=(
                        VFolderOwnershipType.GROUP
                        if owner_user_id is None
                        else VFolderOwnershipType.USER
                    ),
                    user=owner_user_id,
                    group=project_id if owner_user_id is None else None,
                    status=VFolderOperationStatus.READY,
                )
            )
            await sess.flush()
            sess.add_all([
                VFolderUserMountPolicyRow(
                    vfolder_id=vfolder_id, user_id=user_id, permission=permission
                )
                for user_id, permission in (
                    (caller_id, case.policy_of_caller),
                    (another_user_id, case.policy_of_another_user),
                )
                if permission is not None
            ])
            await seeder.provision(sess, ProjectEntityType(), project_id)
            if case.folder_has_node:
                await seeder.create_in(
                    sess, VFolderEntityType(), vfolder_id, [(ProjectEntityType(), project_id)]
                )
            if case.caller_role_grants_read:
                sess.add(
                    RoleRow(
                        id=role_id,
                        name="test-role",
                        scope_type=ProjectEntityType(),
                        scope_id=project_id,
                    )
                )
                await sess.flush()
                sess.add_all([
                    PermissionRow(
                        role_id=role_id,
                        entity_type=VFolderEntityType(),
                        permission=Permission.READ,
                    ),
                    UserRoleRow(user_id=caller_id, role_id=role_id),
                ])
        return _MountPermissionSituation(
            caller_id=caller_id, vfolder_id=vfolder_id, expected=case.expected
        )

    @pytest.mark.parametrize(
        "case",
        [
            _MountPermissionCase(
                name="no-read-access",
                folder_owner=_FolderOwner.CALLER,
                caller_role_grants_read=False,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                policy_of_caller=VFolderMountPolicy.READ_WRITE,
                expected=VFolderMountPolicy.NONE,
            ),
            _MountPermissionCase(
                name="owner",
                folder_owner=_FolderOwner.CALLER,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                policy_of_caller=VFolderMountPolicy.READ_ONLY,
                expected=VFolderMountPolicy.READ_WRITE,
            ),
            _MountPermissionCase(
                name="policy-of-caller",
                folder_owner=_FolderOwner.ANOTHER_USER,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                policy_of_caller=VFolderMountPolicy.READ_ONLY,
                expected=VFolderMountPolicy.READ_ONLY,
            ),
            _MountPermissionCase(
                name="default-when-only-another-user-has-a-policy",
                folder_owner=_FolderOwner.PROJECT,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                policy_of_another_user=VFolderMountPolicy.READ_WRITE,
                expected=VFolderMountPolicy.READ_ONLY,
            ),
            _MountPermissionCase(
                name="superadmin-without-a-role",
                folder_owner=_FolderOwner.PROJECT,
                caller_role=UserRole.SUPERADMIN,
                caller_role_grants_read=False,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                expected=VFolderMountPolicy.READ_ONLY,
            ),
            _MountPermissionCase(
                name="superadmin-on-a-folder-without-a-node",
                folder_owner=_FolderOwner.PROJECT,
                caller_role=UserRole.SUPERADMIN,
                caller_role_grants_read=False,
                folder_has_node=False,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                expected=VFolderMountPolicy.NONE,
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_folder_matches_only_the_level_the_caller_mounts_it_at(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mount_permission_situation: _MountPermissionSituation,
    ) -> None:
        conditions = EnumConditions(
            mount_permission_of_user(mount_permission_situation.caller_id), VFolderMountPolicy
        )
        async with db_with_cleanup.begin_readonly_session() as sess:
            matched_levels = [
                level
                for level in VFolderMountPolicy
                if await sess.scalar(sa.select(VFolderRow.id).where(conditions.equals(level)()))
                == mount_permission_situation.vfolder_id
            ]
        assert matched_levels == [mount_permission_situation.expected]
