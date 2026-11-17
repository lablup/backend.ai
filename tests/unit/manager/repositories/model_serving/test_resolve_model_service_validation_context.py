from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import VFolderNotFound
from ai.backend.common.types import (
    AccessKey,
    ResourceSlot,
    SessionTypes,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


@dataclass(frozen=True)
class _ModelServiceValidationRequest:
    repository: ModelServingRepository
    legacy_etcd_loader: MagicMock
    domain_name: str
    project_name: str
    resource_group: str
    owner_uuid: uuid.UUID
    owner_access_key: AccessKey
    model: str


class TestResolveModelServiceValidationContext:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ResourceGroupForDomainRow,
                ResourceGroupForProjectRow,
                ResourceGroupForKeypairsRow,
                VFolderRow,
                VFolderUserMountPolicyRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
                RuntimeVariantRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def request_naming_a_delete_complete_model_folder_by_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> _ModelServiceValidationRequest:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"domain-{domain_id.hex[:8]}"
        resource_group = f"rg-{uuid.uuid4().hex[:8]}"
        owner_uuid = uuid.uuid4()
        owner_access_key = AccessKey(f"AK{owner_uuid.hex[:18]}")
        project_name = f"project-{uuid.uuid4().hex[:8]}"
        policy_name = f"policy-{uuid.uuid4().hex[:8]}"
        vfolder_id = uuid.uuid4()
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()))
            sess.add(
                ResourceGroupRow(
                    name=resource_group,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(
                        allowed_session_types=[SessionTypes.INFERENCE]
                    ),
                    wsproxy_addr="http://coordinator.test",
                    wsproxy_api_token="coordinator-token",
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=policy_name,
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            resource_group_id = await sess.scalar(
                sa.select(ResourceGroupRow.id).where(ResourceGroupRow.name == resource_group)
            )
            sess.add(
                ResourceGroupForDomainRow(resource_group_id=resource_group_id, domain_id=domain_id)
            )
            sess.add(
                UserRow(
                    uuid=owner_uuid,
                    email=f"{owner_uuid.hex[:8]}@test.com",
                    username=f"user-{owner_uuid.hex[:8]}",
                    password=PasswordInfo(
                        password="pw",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy=policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=owner_access_key,
                    secret_key=SecretValue("secret"),
                    is_active=True,
                    is_admin=False,
                    user=owner_uuid,
                    resource_policy=policy_name,
                    is_default=True,
                )
            )
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=project_name,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=policy_name,
                )
            )
            sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name="model",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{owner_uuid}",
                    usage_mode=VFolderUsageMode.MODEL,
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=owner_uuid,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.DELETE_COMPLETE,
                )
            )
            await sess.flush()
            seeder = VirtualEntitySeeder()
            await seeder.enroll_user_in_project(sess, project_id, owner_uuid)
            await seeder.create_in(
                sess, VFolderEntityType(), vfolder_id, [(UserEntityType(), owner_uuid)]
            )

        async def hold_every_permission(
            user_id: UserID,
            vfolder_ids: Sequence[VFolderUUID],
        ) -> Mapping[EntityIdentifier, Permission]:
            return dict.fromkeys(vfolder_ids, Permission.full())

        legacy_etcd_loader = MagicMock()
        legacy_etcd_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
        permission_check = MagicMock()
        permission_check.held_permissions = AsyncMock(side_effect=hold_every_permission)
        return _ModelServiceValidationRequest(
            repository=ModelServingRepository(
                db=db_with_cleanup,
                v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
                permission_check=permission_check,
            ),
            legacy_etcd_loader=legacy_etcd_loader,
            domain_name=domain_name,
            project_name=project_name,
            resource_group=resource_group,
            owner_uuid=owner_uuid,
            owner_access_key=owner_access_key,
            model=str(vfolder_id),
        )

    async def test_a_delete_complete_model_folder_id_is_not_found(
        self,
        request_naming_a_delete_complete_model_folder_by_id: _ModelServiceValidationRequest,
    ) -> None:
        request = request_naming_a_delete_complete_model_folder_by_id

        with pytest.raises(VFolderNotFound):
            await request.repository.resolve_model_service_validation_context(
                resource_group=request.resource_group,
                owner_access_key=request.owner_access_key,
                domain_name=request.domain_name,
                group_name=request.project_name,
                requester_uuid=request.owner_uuid,
                requester_access_key=request.owner_access_key,
                requester_role=UserRole.USER,
                requester_domain=request.domain_name,
                keypair_resource_policy={},
                owner_access_key_override=None,
                model=request.model,
                model_mount_destination="/models",
                extra_mounts={},
                runtime_variant_name="custom",
                legacy_etcd_loader=request.legacy_etcd_loader,
                storage_manager=MagicMock(),
            )
