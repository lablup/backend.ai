from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import VFolderNotFound
from ai.backend.common.types import AccessKey, ResourceSlot, SessionTypes, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.scaling_group.row import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _ModelServiceValidationRequest:
    repository: ModelServingRepository
    legacy_etcd_loader: MagicMock
    domain_name: str
    project_name: str
    scaling_group: str
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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForDomainRow,
                ScalingGroupForProjectRow,
                ScalingGroupForKeypairsRow,
                AssociationScopesEntitiesRow,
                VFolderRow,
                VFolderPermissionRow,
                RuntimeVariantRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def request_naming_a_delete_pending_model_folder_by_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> _ModelServiceValidationRequest:
        domain_name = f"domain-{uuid.uuid4().hex[:8]}"
        scaling_group = f"sg-{uuid.uuid4().hex[:8]}"
        owner_uuid = uuid.uuid4()
        owner_email = f"{owner_uuid.hex[:8]}@test.com"
        owner_access_key = AccessKey(f"AK{owner_uuid.hex[:18]}")
        project_id = uuid.uuid4()
        project_name = f"project-{project_id.hex[:8]}"
        policy_name = f"policy-{uuid.uuid4().hex[:8]}"
        vfolder_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(DomainRow(name=domain_name, total_resource_slots=ResourceSlot()))
            sess.add(
                ScalingGroupRow(
                    name=scaling_group,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INFERENCE]),
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
            sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name))
            sess.add(
                UserRow(
                    uuid=owner_uuid,
                    email=owner_email,
                    username=f"user-{owner_uuid.hex[:8]}",
                    password=PasswordInfo(
                        password="pw",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_name=domain_name,
                    resource_policy=policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    user_id=owner_email,
                    access_key=owner_access_key,
                    secret_key="secret",
                    is_active=True,
                    is_admin=False,
                    user=owner_uuid,
                    resource_policy=policy_name,
                )
            )
            sess.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=policy_name,
                )
            )
            await sess.flush()
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(project_id),
                    entity_type=EntityType.USER,
                    entity_id=str(owner_uuid),
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
                    ownership_type=VFolderOwnershipType.USER,
                    user=owner_uuid,
                    group=None,
                    creator=owner_email,
                    unmanaged_path=None,
                    cloneable=False,
                    status=VFolderOperationStatus.DELETE_PENDING,
                )
            )
            await sess.flush()

        legacy_etcd_loader = MagicMock()
        legacy_etcd_loader.get_vfolder_types = AsyncMock(return_value=["user"])
        return _ModelServiceValidationRequest(
            repository=ModelServingRepository(db=db_with_cleanup),
            legacy_etcd_loader=legacy_etcd_loader,
            domain_name=domain_name,
            project_name=project_name,
            scaling_group=scaling_group,
            owner_uuid=owner_uuid,
            owner_access_key=owner_access_key,
            model=str(vfolder_id),
        )

    async def test_a_delete_pending_model_folder_id_is_not_found(
        self,
        request_naming_a_delete_pending_model_folder_by_id: _ModelServiceValidationRequest,
    ) -> None:
        request = request_naming_a_delete_pending_model_folder_by_id

        with pytest.raises(VFolderNotFound):
            await request.repository.resolve_model_service_validation_context(
                scaling_group=request.scaling_group,
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
