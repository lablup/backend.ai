"""
Unit tests for the caller-relative vfolder access rules on VfolderRepository.

These cover the pure parts -- resolving ownership and a grant into an effective
permission, and refusing a write -- so they need no database.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.storage import VFolderPermissionError
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository

VFolderDataFactory = Callable[..., VFolderData]


@pytest.fixture
def owner_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def invitee_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def make_vfolder_data(owner_uuid: uuid.UUID) -> VFolderDataFactory:
    def _make(
        *,
        ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER,
        permission: VFolderMountPermission | None = VFolderMountPermission.RW_DELETE,
        user: uuid.UUID | None = None,
        group: uuid.UUID | None = None,
    ) -> VFolderData:
        now = datetime.now(UTC)
        return VFolderData(
            id=VFolderUUID(uuid.uuid4()),
            name="shared-folder",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID(QuotaScopeType.USER, owner_uuid),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=permission,
            max_files=1000,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=now,
            last_used=None,
            updated_at=now,
            creator="owner@example.com",
            creator_id=owner_uuid,
            unmanaged_path=None,
            ownership_type=ownership_type,
            user=owner_uuid
            if user is None and ownership_type is VFolderOwnershipType.USER
            else user,
            group=group,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    return _make


class TestResolveAccessInfo:
    """Tests for VfolderRepository._resolve_access_info()"""

    def test_owner_of_user_folder_reads_the_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, owner_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(permission=VFolderMountPermission.READ_WRITE)

        access_info = VfolderRepository._resolve_access_info(vfolder_data, owner_uuid, None)

        assert access_info.is_owner is True
        assert access_info.effective_permission is VFolderMountPermission.READ_WRITE

    def test_invitee_holds_the_granted_permission_not_the_folder_default(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        # The folder's own column says rw-delete; the invitee was granted ro.
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        assert access_info.is_owner is False
        assert access_info.effective_permission is VFolderMountPermission.READ_ONLY

    def test_stranger_of_user_folder_holds_no_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, None
        )

        assert access_info.is_owner is False
        assert access_info.effective_permission is None

    def test_project_member_inherits_the_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(
            ownership_type=VFolderOwnershipType.GROUP,
            permission=VFolderMountPermission.READ_WRITE,
            group=uuid.uuid4(),
        )

        access_info = VfolderRepository._resolve_access_info(vfolder_data, invitee_uuid, None)

        assert access_info.is_owner is False
        assert access_info.effective_permission is VFolderMountPermission.READ_WRITE

    def test_explicit_grant_overrides_the_project_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(
            ownership_type=VFolderOwnershipType.GROUP,
            permission=VFolderMountPermission.READ_WRITE,
            group=uuid.uuid4(),
        )

        access_info = VfolderRepository._resolve_access_info(
            vfolder_data, invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        assert access_info.effective_permission is VFolderMountPermission.READ_ONLY


class TestEnsureWritable:
    """Tests for VfolderRepository.ensure_writable()"""

    def test_read_only_permission_is_refused(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        with pytest.raises(VFolderPermissionError):
            VfolderRepository.ensure_writable(access_info, UserRole.USER)

    def test_absent_permission_is_refused(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, None
        )

        with pytest.raises(VFolderPermissionError):
            VfolderRepository.ensure_writable(access_info, UserRole.USER)

    @pytest.mark.parametrize(
        "permission",
        [VFolderMountPermission.READ_WRITE, VFolderMountPermission.RW_DELETE],
    )
    def test_writable_permissions_pass(
        self,
        make_vfolder_data: VFolderDataFactory,
        invitee_uuid: uuid.UUID,
        permission: VFolderMountPermission,
    ) -> None:
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, permission
        )

        VfolderRepository.ensure_writable(access_info, UserRole.USER)

    def test_owner_passes_even_when_the_folder_permission_is_read_only(
        self, make_vfolder_data: VFolderDataFactory, owner_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(permission=VFolderMountPermission.READ_ONLY)

        access_info = VfolderRepository._resolve_access_info(vfolder_data, owner_uuid, None)

        VfolderRepository.ensure_writable(access_info, UserRole.USER)

    @pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.SUPERADMIN])
    def test_admins_keep_privileged_access(
        self,
        make_vfolder_data: VFolderDataFactory,
        invitee_uuid: uuid.UUID,
        role: UserRole,
    ) -> None:
        access_info = VfolderRepository._resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        VfolderRepository.ensure_writable(access_info, role)
