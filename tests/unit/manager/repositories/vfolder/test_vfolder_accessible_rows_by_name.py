"""Regression test for resolving a project vfolder by name with `VfolderRepository.get_accessible_rows`."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
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
    VFolderPermissionSetAlias,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables

_DOMAIN_NAME = "test-domain-accessible-by-name"
_REUSED_VFOLDER_NAME = "reused-name"


@dataclass(frozen=True)
class _ProjectHoldingDeletedAndLiveVFolderOfSameName:
    member_id: UUID
    live_vfolder_id: UUID


class TestGetAccessibleRowsByName:
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
    async def project_holding_deleted_and_live_vfolder_of_same_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _ProjectHoldingDeletedAndLiveVFolderOfSameName:
        user_policy_name = f"user-{uuid4().hex[:8]}"
        project_policy_name = f"proj-{uuid4().hex[:8]}"
        project_id = uuid4()
        member_id = uuid4()
        deleted_vfolder_id = uuid4()
        live_vfolder_id = uuid4()

        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=_DOMAIN_NAME,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=5,
                )
            )
            await sess.flush()

            sess.add(
                GroupRow(
                    id=project_id,
                    name=f"proj-{project_id.hex[:8]}",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=project_policy_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    type=ProjectType.GENERAL,
                )
            )
            sess.add(
                UserRow(
                    uuid=member_id,
                    username=f"u_{member_id.hex[:8]}",
                    email=f"member-{member_id.hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="dummy",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=_DOMAIN_NAME,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
            )
            await sess.flush()

            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(project_id),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(member_id),
                )
            )
            for vfolder_id, status in (
                (deleted_vfolder_id, VFolderOperationStatus.DELETE_COMPLETE),
                (live_vfolder_id, VFolderOperationStatus.READY),
            ):
                sess.add(
                    VFolderRow(
                        id=vfolder_id,
                        name=_REUSED_VFOLDER_NAME,
                        host="local",
                        domain_name=_DOMAIN_NAME,
                        quota_scope_id=f"project:{project_id}",
                        ownership_type=VFolderOwnershipType.GROUP,
                        permission=VFolderPermission.READ_WRITE,
                        user=None,
                        group=project_id,
                        creator=f"u_{member_id.hex[:8]}@example.com",
                        creator_id=member_id,
                        unmanaged_path=None,
                        cloneable=False,
                        status=status,
                    )
                )
            await sess.flush()

        return _ProjectHoldingDeletedAndLiveVFolderOfSameName(
            member_id=member_id,
            live_vfolder_id=live_vfolder_id,
        )

    async def test_name_resolves_to_live_project_vfolder_only(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project_holding_deleted_and_live_vfolder_of_same_name: _ProjectHoldingDeletedAndLiveVFolderOfSameName,
    ) -> None:
        situation = project_holding_deleted_and_live_vfolder_of_same_name

        rows = await VfolderRepository(db_with_cleanup).get_accessible_rows(
            user_uuid=situation.member_id,
            user_role=UserRole.USER,
            domain_name=_DOMAIN_NAME,
            is_admin=False,
            allowed_vfolder_types=["user", "group"],
            perm=VFolderPermissionSetAlias.READABLE,
            folder_id_or_name=_REUSED_VFOLDER_NAME,
        )

        assert [row["id"] for row in rows] == [situation.live_vfolder_id]
