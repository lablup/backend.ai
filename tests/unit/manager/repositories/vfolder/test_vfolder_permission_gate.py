"""Tests for `VfolderRepository.get_by_id_for_operation` share-permission gating.

A folder shared read-only must reject write operations while still allowing reads;
the owner is never gated.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import (
    BinarySize,
    QuotaScopeID,
    QuotaScopeType,
    ResourceSlot,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.errors.storage import VFolderNotFound, VFolderPermissionError
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
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
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

DOMAIN_NAME_FIXED = "test-domain-perm-gate"


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


class TestGetByIdForOperation:
    """Share-permission gating on the single choke point every file operation passes."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK order: parents first
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                VFolderRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
                VirtualScopeRow,
                EntityMembershipRow,
                EntityLabelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain_fixture(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DomainFixtureData, None]:
        domain_id = DomainID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=DOMAIN_NAME_FIXED,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            await sess.flush()
        yield DomainFixtureData(domain_name=DomainName(DOMAIN_NAME_FIXED), domain_id=domain_id)

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

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_fixture: DomainFixtureData,
        resource_policy: str,
        label: str,
    ) -> UUID:
        user_uuid = uuid4()
        async with db.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"{label}_{user_uuid.hex[:8]}",
                    email=f"{label}-{user_uuid.hex[:8]}@example.com",
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_fixture.domain_name,
                    role=UserRole.USER,
                    resource_policy=resource_policy,
                    domain_id=domain_fixture.domain_id,
                )
            )
            await sess.flush()
        return user_uuid

    @pytest.fixture
    async def owner(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        user_resource_policy: str,
    ) -> UUID:
        return await self._create_user(
            db_with_cleanup,
            domain_fixture=domain_fixture,
            resource_policy=user_resource_policy,
            label="owner",
        )

    @pytest.fixture
    async def grantee(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        user_resource_policy: str,
    ) -> UUID:
        return await self._create_user(
            db_with_cleanup,
            domain_fixture=domain_fixture,
            resource_policy=user_resource_policy,
            label="grantee",
        )

    @pytest.fixture
    async def outsider(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        user_resource_policy: str,
    ) -> UUID:
        return await self._create_user(
            db_with_cleanup,
            domain_fixture=domain_fixture,
            resource_policy=user_resource_policy,
            label="outsider",
        )

    @pytest.fixture
    async def vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        owner: UUID,
    ) -> UUID:
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"vf-{vfolder_id.hex[:8]}",
                    host="local",
                    domain_name=domain_fixture.domain_name,
                    quota_scope_id=QuotaScopeID(QuotaScopeType.USER, owner),
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderPermission.READ_WRITE,
                    ownership_type=VFolderOwnershipType.USER,
                    user=owner,
                    group=None,
                    creator_id=owner,
                    unmanaged_path=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await sess.flush()
        return vfolder_id

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> VfolderRepository:
        return VfolderRepository(
            db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup)
        )

    async def _share(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        vfolder_id: UUID,
        user_id: UUID,
        permission: VFolderPermission,
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                VFolderPermissionRow(
                    id=uuid4(),
                    vfolder=vfolder_id,
                    user=user_id,
                    permission=permission,
                )
            )
            await sess.flush()

    async def test_owner_passes_writable(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        repository: VfolderRepository,
        owner: UUID,
        vfolder: UUID,
    ) -> None:
        data = await repository.get_by_id_for_operation(
            vfolder,
            owner,
            domain_fixture.domain_name,
            required=VFolderPermissionSetAlias.WRITABLE,
        )
        assert data.id == vfolder

    async def test_read_only_grantee_passes_readable(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        repository: VfolderRepository,
        grantee: UUID,
        vfolder: UUID,
    ) -> None:
        await self._share(
            db_with_cleanup,
            vfolder_id=vfolder,
            user_id=grantee,
            permission=VFolderPermission.READ_ONLY,
        )

        data = await repository.get_by_id_for_operation(
            vfolder,
            grantee,
            domain_fixture.domain_name,
            required=VFolderPermissionSetAlias.READABLE,
        )
        assert data.id == vfolder

    async def test_read_only_grantee_rejected_for_writable(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        repository: VfolderRepository,
        grantee: UUID,
        vfolder: UUID,
    ) -> None:
        await self._share(
            db_with_cleanup,
            vfolder_id=vfolder,
            user_id=grantee,
            permission=VFolderPermission.READ_ONLY,
        )

        with pytest.raises(VFolderPermissionError):
            await repository.get_by_id_for_operation(
                vfolder,
                grantee,
                domain_fixture.domain_name,
                required=VFolderPermissionSetAlias.WRITABLE,
            )

    @pytest.mark.parametrize(
        "shared_permission",
        [VFolderPermission.READ_WRITE, VFolderPermission.RW_DELETE],
    )
    async def test_writable_grantee_passes_writable(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        repository: VfolderRepository,
        grantee: UUID,
        vfolder: UUID,
        shared_permission: VFolderPermission,
    ) -> None:
        await self._share(
            db_with_cleanup,
            vfolder_id=vfolder,
            user_id=grantee,
            permission=shared_permission,
        )

        data = await repository.get_by_id_for_operation(
            vfolder,
            grantee,
            domain_fixture.domain_name,
            required=VFolderPermissionSetAlias.WRITABLE,
        )
        assert data.id == vfolder

    async def test_unshared_user_is_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_fixture: DomainFixtureData,
        repository: VfolderRepository,
        outsider: UUID,
        vfolder: UUID,
    ) -> None:
        with pytest.raises(VFolderNotFound):
            await repository.get_by_id_for_operation(
                vfolder,
                outsider,
                domain_fixture.domain_name,
                required=VFolderPermissionSetAlias.READABLE,
            )
