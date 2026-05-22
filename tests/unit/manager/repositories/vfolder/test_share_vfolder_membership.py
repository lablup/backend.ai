"""Tests for `VfolderRepository.share_vfolder_with_users` project-membership lookup.

Only the membership filter — powered by `association_scopes_entities` after BA-5819 —
is verified. The host-permission gate is patched out so the test focuses purely on
which users can or cannot be returned by the membership lookup.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.permission.types import (
    EntityType as PermissionEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as PermissionScopeType,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
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
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder import repository as vfolder_repo_module
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData

REQUESTER_EMAIL = "requester@example.com"
DOMAIN_NAME_FIXED = "test-domain-share"


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


class TestShareVfolderWithUsersMembership:
    """Membership-lookup behavior of `share_vfolder_with_users`.

    `ensure_host_permission_allowed` is patched to a no-op so the test isolates the
    project-membership branch.
    """

    @pytest.fixture(autouse=True)
    def _patch_host_permission(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            vfolder_repo_module,
            "ensure_host_permission_allowed",
            AsyncMock(return_value=None),
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
                VFolderRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain_name(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        return await domain_factory(db_with_cleanup, name=DOMAIN_NAME_FIXED)

    @pytest.fixture
    async def project_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        policy_name = f"proj-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=5,
                )
            )
            await sess.flush()
        yield policy_name

    @pytest.fixture
    async def user_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        policy_name = f"user-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await sess.flush()
        yield policy_name

    @pytest.fixture
    async def project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        gid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=gid,
                    name=f"proj-{gid.hex[:8]}",
                    domain_name=domain_name.domain_name,
                    domain_id=domain_name.domain_id,
                    resource_policy=project_resource_policy,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    type=ProjectType.GENERAL,
                )
            )
            await sess.flush()
        yield gid

    @pytest.fixture
    async def requester(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        user_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        user_uuid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"requester_{user_uuid.hex[:8]}",
                    email=REQUESTER_EMAIL,
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name.domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            await sess.flush()
        yield user_uuid

    @pytest.fixture
    async def vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
    ) -> AsyncGenerator[UUID, None]:
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"vf-{vfolder_id.hex[:8]}",
                    host="local",
                    domain_name=domain_name.domain_name,
                    quota_scope_id=f"project:{project}",
                    ownership_type=VFolderOwnershipType.GROUP,
                    user=None,
                    group=project,
                    creator=REQUESTER_EMAIL,
                    creator_id=requester,
                    unmanaged_path=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await sess.flush()
        yield vfolder_id

    @pytest.fixture
    async def member_user_email(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        user_resource_policy: str,
        project: UUID,
    ) -> AsyncGenerator[str, None]:
        """An ACTIVE user with an ASE membership row in `project`."""
        user_uuid = uuid4()
        email = f"member-{user_uuid.hex[:8]}@example.com"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u_{user_uuid.hex[:8]}",
                    email=email,
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name.domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(project),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(user_uuid),
                )
            )
            await sess.flush()
        yield email

    @pytest.fixture
    async def non_member_user_email(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        user_resource_policy: str,
    ) -> AsyncGenerator[str, None]:
        """An ACTIVE user with no project membership."""
        user_uuid = uuid4()
        email = f"stranger-{user_uuid.hex[:8]}@example.com"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u_{user_uuid.hex[:8]}",
                    email=email,
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name.domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            await sess.flush()
        yield email

    @pytest.fixture
    async def inactive_member_user_email(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        user_resource_policy: str,
        project: UUID,
    ) -> AsyncGenerator[str, None]:
        """An INACTIVE user that nonetheless has an ASE membership row in `project`."""
        user_uuid = uuid4()
        email = f"inactive-{user_uuid.hex[:8]}@example.com"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u_{user_uuid.hex[:8]}",
                    email=email,
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.INACTIVE,
                    status_info="inactive",
                    domain_name=domain_name.domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(project),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(user_uuid),
                )
            )
            await sess.flush()
        yield email

    @pytest.fixture
    async def other_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        """A separate project in the same domain (used to verify cross-project isolation)."""
        gid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=gid,
                    name=f"other-{gid.hex[:8]}",
                    domain_name=domain_name.domain_name,
                    domain_id=domain_name.domain_id,
                    resource_policy=project_resource_policy,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    type=ProjectType.GENERAL,
                )
            )
            await sess.flush()
        yield gid

    @pytest.fixture
    async def other_project_member_email(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        user_resource_policy: str,
        other_project: UUID,
    ) -> AsyncGenerator[str, None]:
        """An ACTIVE user with an ASE membership row in `other_project` (not `project`)."""
        user_uuid = uuid4()
        email = f"elsewhere-{user_uuid.hex[:8]}@example.com"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u_{user_uuid.hex[:8]}",
                    email=email,
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name.domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(other_project),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(user_uuid),
                )
            )
            await sess.flush()
        yield email

    def _share_kwargs(
        self,
        vfolder_id: UUID,
        project: UUID,
        requester: UUID,
        domain_name: str,
        emails: list[str],
    ) -> dict[str, Any]:
        return {
            "vfolder_id": vfolder_id,
            "vfolder_host": "local",
            "vfolder_group": project,
            "requester_uuid": requester,
            "requester_email": REQUESTER_EMAIL,
            "domain_name": domain_name,
            "resource_policy": {},
            "emails": emails,
            "permission": VFolderPermission.READ_ONLY,
            "allowed_vfolder_types": ["group"],
        }

    async def test_member_is_returned(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
        vfolder: UUID,
        member_user_email: str,
    ) -> None:
        """A user that is a project member is returned in the share result."""
        repo = VfolderRepository(db_with_cleanup)
        result = await repo.share_vfolder_with_users(
            **self._share_kwargs(
                vfolder, project, requester, domain_name.domain_name, [member_user_email]
            )
        )

        assert result == [member_user_email]

    async def test_non_member_raises_object_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
        vfolder: UUID,
        non_member_user_email: str,
    ) -> None:
        """A user without an ASE membership row triggers ObjectNotFound."""
        repo = VfolderRepository(db_with_cleanup)
        with pytest.raises(ObjectNotFound):
            await repo.share_vfolder_with_users(
                **self._share_kwargs(
                    vfolder, project, requester, domain_name.domain_name, [non_member_user_email]
                )
            )

    async def test_partial_membership_raises_object_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
        vfolder: UUID,
        member_user_email: str,
        non_member_user_email: str,
    ) -> None:
        """When some emails are not project members, the call must reject the whole batch."""
        repo = VfolderRepository(db_with_cleanup)
        with pytest.raises(ObjectNotFound):
            await repo.share_vfolder_with_users(
                **self._share_kwargs(
                    vfolder,
                    project,
                    requester,
                    domain_name.domain_name,
                    [member_user_email, non_member_user_email],
                )
            )

    async def test_membership_in_other_project_does_not_grant_share(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
        vfolder: UUID,
        other_project_member_email: str,
    ) -> None:
        """Membership in a different project does not satisfy this folder's group filter."""
        repo = VfolderRepository(db_with_cleanup)
        with pytest.raises(ObjectNotFound):
            await repo.share_vfolder_with_users(
                **self._share_kwargs(
                    vfolder,
                    project,
                    requester,
                    domain_name.domain_name,
                    [other_project_member_email],
                )
            )

    async def test_inactive_member_is_filtered_out(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: DomainFixtureData,
        project: UUID,
        requester: UUID,
        vfolder: UUID,
        inactive_member_user_email: str,
    ) -> None:
        """Membership alone is not enough — inactive users are excluded by status filter."""
        repo = VfolderRepository(db_with_cleanup)
        with pytest.raises(ObjectNotFound):
            await repo.share_vfolder_with_users(
                **self._share_kwargs(
                    vfolder,
                    project,
                    requester,
                    domain_name.domain_name,
                    [inactive_member_user_email],
                )
            )
