"""The mount policy service: who may hand out which mount level."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import QuotaScopeID, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPolicyData,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.storage import (
    VFolderMountPolicyNotApplicable,
    VFolderMountPolicyTooWide,
)
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.mount_policy import (
    SetVFolderMountPolicyAction,
    UnsetVFolderMountPolicyAction,
)
from ai.backend.manager.services.vfolder.services.mount_policy import VFolderMountPolicyService


@pytest.fixture
def requester_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def owner_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def target_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def project_id() -> uuid.UUID:
    return uuid.uuid4()


def _user(user_id: uuid.UUID, *, superadmin: bool = False) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=superadmin,
        is_superadmin=superadmin,
        role=UserRole.SUPERADMIN if superadmin else UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def as_requester(requester_id: uuid.UUID) -> Iterator[None]:
    with with_user(_user(requester_id)):
        yield


def _folder(
    vfolder_id: uuid.UUID,
    *,
    owner: uuid.UUID | None,
    project: uuid.UUID,
    default: VFolderMountPolicy,
) -> VFolderData:
    now = datetime.now(UTC)
    return VFolderData(
        id=VFolderUUID(vfolder_id),
        name="shared",
        host="local",
        domain_name="default",
        quota_scope_id=QuotaScopeID.parse(f"project:{project}"),
        usage_mode=VFolderUsageMode.GENERAL,
        default_mount_permission=default,
        max_files=0,
        max_size=None,
        num_files=0,
        cur_size=0,
        created_at=now,
        last_used=None,
        updated_at=now,
        creator=None,
        creator_id=None,
        unmanaged_path=None,
        ownership_type=VFolderOwnershipType.USER if owner else VFolderOwnershipType.GROUP,
        user=owner,
        group=project,
        cloneable=False,
        status=VFolderOperationStatus.READY,
    )


def _policy(
    vfolder_id: uuid.UUID, user_id: uuid.UUID, level: VFolderMountPolicy
) -> VFolderMountPolicyData:
    now = datetime.now(UTC)
    return VFolderMountPolicyData(
        id=VFolderMountPolicyID(uuid.uuid4()),
        vfolder_id=VFolderUUID(vfolder_id),
        user_id=user_id,
        permission=level,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def vfolder_repo() -> MagicMock:
    repo = MagicMock(spec=VfolderRepository)
    repo.set_user_mount_policy = AsyncMock(
        side_effect=lambda vfolder_id, user_id, permission: _policy(vfolder_id, user_id, permission)
    )
    repo.unset_user_mount_policy = AsyncMock(return_value=True)
    repo.user_mount_policies_of = AsyncMock(return_value={})
    return repo


@pytest.fixture
def permission_check() -> MagicMock:
    check = MagicMock(spec=RbacPermissionCheckRepository)
    check.governed_permissions = AsyncMock(return_value={})
    check.held_permissions = AsyncMock(return_value={})
    return check


@pytest.fixture
def service(vfolder_repo: MagicMock, permission_check: MagicMock) -> VFolderMountPolicyService:
    return VFolderMountPolicyService(vfolder_repo, permission_check)


class TestSetMountPolicy:
    @pytest.mark.usefixtures("as_requester")
    async def test_the_owner_hands_out_any_level(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        requester_id: uuid.UUID,
        target_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=requester_id, project=project_id, default=VFolderMountPolicy.NONE
            )
        )

        result = await service.set(
            SetVFolderMountPolicyAction(
                vfolder_uuid=VFolderUUID(folder_id),
                user_id=UserID(target_id),
                permission=VFolderMountPolicy.READ_WRITE,
            )
        )

        assert result.policy.permission == VFolderMountPolicy.READ_WRITE

    @pytest.mark.usefixtures("as_requester")
    async def test_a_project_role_holder_hands_out_any_level(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        permission_check: MagicMock,
        target_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=None, project=project_id, default=VFolderMountPolicy.READ_ONLY
            )
        )
        permission_check.governed_permissions = AsyncMock(
            side_effect=lambda keys: dict.fromkeys(keys, Permission.UPDATE)
        )

        result = await service.set(
            SetVFolderMountPolicyAction(
                vfolder_uuid=VFolderUUID(folder_id),
                user_id=UserID(target_id),
                permission=VFolderMountPolicy.READ_WRITE,
            )
        )

        assert result.policy.permission == VFolderMountPolicy.READ_WRITE

    @pytest.mark.usefixtures("as_requester")
    async def test_a_shared_in_requester_cannot_exceed_their_own_level(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        permission_check: MagicMock,
        owner_id: uuid.UUID,
        target_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=owner_id, project=project_id, default=VFolderMountPolicy.READ_ONLY
            )
        )
        permission_check.held_permissions = AsyncMock(
            return_value={VFolderUUID(folder_id): Permission.READ | Permission.UPDATE}
        )

        with pytest.raises(VFolderMountPolicyTooWide):
            await service.set(
                SetVFolderMountPolicyAction(
                    vfolder_uuid=VFolderUUID(folder_id),
                    user_id=UserID(target_id),
                    permission=VFolderMountPolicy.READ_WRITE,
                )
            )

    @pytest.mark.usefixtures("as_requester")
    async def test_a_shared_in_requester_may_lower(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        permission_check: MagicMock,
        owner_id: uuid.UUID,
        target_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=owner_id, project=project_id, default=VFolderMountPolicy.READ_ONLY
            )
        )
        permission_check.held_permissions = AsyncMock(
            return_value={VFolderUUID(folder_id): Permission.READ | Permission.UPDATE}
        )

        result = await service.set(
            SetVFolderMountPolicyAction(
                vfolder_uuid=VFolderUUID(folder_id),
                user_id=UserID(target_id),
                permission=VFolderMountPolicy.NONE,
            )
        )

        assert result.policy.permission == VFolderMountPolicy.NONE

    @pytest.mark.usefixtures("as_requester")
    async def test_the_owner_takes_no_row(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        requester_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=requester_id, project=project_id, default=VFolderMountPolicy.NONE
            )
        )

        with pytest.raises(VFolderMountPolicyNotApplicable):
            await service.set(
                SetVFolderMountPolicyAction(
                    vfolder_uuid=VFolderUUID(folder_id),
                    user_id=UserID(requester_id),
                    permission=VFolderMountPolicy.READ_ONLY,
                )
            )

    @pytest.mark.usefixtures("as_requester")
    async def test_a_requester_takes_no_row_on_themselves(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        requester_id: uuid.UUID,
        owner_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=owner_id, project=project_id, default=VFolderMountPolicy.NONE
            )
        )

        with pytest.raises(VFolderMountPolicyNotApplicable):
            await service.set(
                SetVFolderMountPolicyAction(
                    vfolder_uuid=VFolderUUID(folder_id),
                    user_id=UserID(requester_id),
                    permission=VFolderMountPolicy.READ_WRITE,
                )
            )

    async def test_a_superadmin_hands_out_any_level(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        owner_id: uuid.UUID,
        target_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.get_by_id = AsyncMock(
            return_value=_folder(
                folder_id, owner=owner_id, project=project_id, default=VFolderMountPolicy.NONE
            )
        )

        with with_user(_user(uuid.uuid4(), superadmin=True)):
            result = await service.set(
                SetVFolderMountPolicyAction(
                    vfolder_uuid=VFolderUUID(folder_id),
                    user_id=UserID(target_id),
                    permission=VFolderMountPolicy.READ_WRITE,
                )
            )

        assert result.policy.permission == VFolderMountPolicy.READ_WRITE


class TestUnsetMountPolicy:
    @pytest.mark.usefixtures("as_requester")
    async def test_unset_answers_whether_a_row_went(
        self,
        service: VFolderMountPolicyService,
        vfolder_repo: MagicMock,
        target_id: uuid.UUID,
    ) -> None:
        folder_id = uuid.uuid4()
        vfolder_repo.unset_user_mount_policy = AsyncMock(return_value=False)

        result = await service.unset(
            UnsetVFolderMountPolicyAction(
                vfolder_uuid=VFolderUUID(folder_id), user_id=UserID(target_id)
            )
        )

        assert result.removed is False
