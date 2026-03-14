import asyncio
import logging
import math
import uuid
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    cast,
)

import aiohttp
import msgpack
import yarl
from aiohttp import hdrs, web
from sqlalchemy import exc as sa_exc

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import VFOLDER_GROUP_PERMISSION_MODE
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderData,
    VFolderMountPermission,
)
from ai.backend.manager.errors.common import Forbidden, InternalServerError, ObjectNotFound
from ai.backend.manager.errors.kernel import BackendAgentError
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    TooManyVFoldersFound,
    UnexpectedStorageProxyResponseError,
    VFolderAlreadyExists,
    VFolderBadRequest,
    VFolderCreationFailure,
    VFolderFilterStatusFailed,
    VFolderFilterStatusNotAvailable,
    VFolderGone,
    VFolderInvalidParameter,
    VFolderNotFound,
    VFolderOperationFailed,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderCloneInfo,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderRow,
    VFolderStatusSet,
    is_unmanaged,
    verify_vfolder_name,
    vfolder_status_map,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.updaters import VFolderAttributeUpdaterSpec
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetAccessibleVFolderAction,
    GetAccessibleVFolderActionResult,
    GetTaskLogsAction,
    GetTaskLogsActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    PurgeVFolderAction,
    PurgeVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    ChangeVFolderOwnershipActionResult,
    GetFstabContentsAction,
    GetFstabContentsActionResult,
    GetQuotaAction,
    GetQuotaActionResult,
    GetVFolderUsageAction,
    GetVFolderUsageActionResult,
    GetVFolderUsedBytesAction,
    GetVFolderUsedBytesActionResult,
    GetVolumePerfMetricAction,
    GetVolumePerfMetricActionResult,
    ListAllHostsAction,
    ListAllHostsActionResult,
    ListAllowedTypesAction,
    ListAllowedTypesActionResult,
    ListHostsAction,
    ListHostsActionResult,
    ListMountsAction,
    ListMountsActionResult,
    MountHostAction,
    MountHostActionResult,
    MountResultData,
    UmountHostAction,
    UmountHostActionResult,
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.vfolder.types import (
    VFolderBaseInfo,
    VFolderOwnershipInfo,
    VFolderUsageInfo,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _check_vfolder_status(
    vfolder_status: VFolderOperationStatus,
    status: VFolderStatusSet,
) -> None:
    """
    Checks if the target vfolder status matches one of the status sets aliased by `status` VFolderStatusSet,
    """

    available_vf_statuses = vfolder_status_map.get(status)
    if not available_vf_statuses:
        raise VFolderFilterStatusNotAvailable
    if vfolder_status not in available_vf_statuses:
        raise VFolderFilterStatusFailed


class VFolderService:
    _config_provider: ManagerConfigProvider
    _etcd: AsyncEtcd
    _storage_manager: StorageSessionManager
    _background_task_manager: BackgroundTaskManager
    _vfolder_repository: VfolderRepository
    _user_repository: UserRepository
    _valkey_stat_client: ValkeyStatClient

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
        storage_manager: StorageSessionManager,
        background_task_manager: BackgroundTaskManager,
        vfolder_repository: VfolderRepository,
        user_repository: UserRepository,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        self._config_provider = config_provider
        self._etcd = etcd
        self._storage_manager = storage_manager
        self._vfolder_repository = vfolder_repository
        self._user_repository = user_repository
        self._background_task_manager = background_task_manager
        self._valkey_stat_client = valkey_stat_client

    async def create(self, action: CreateVFolderAction) -> CreateVFolderActionResult:
        user_role = action.user_role
        user_uuid = action.user_uuid
        keypair_resource_policy = action.keypair_resource_policy
        domain_name = action.domain_name
        group_id_or_name = action.group_id_or_name
        folder_host = action.folder_host
        unmanaged_path = action.unmanaged_path
        # Resolve host for the new virtual folder.
        if not folder_host:
            folder_host = self._config_provider.config.volumes.default_host
            if not folder_host:
                raise VFolderInvalidParameter(
                    "You must specify the vfolder host because the default host is not configured."
                )
        # Check if user is trying to created unmanaged vFolder
        if unmanaged_path:
            # Approve only if user is Admin or Superadmin
            if user_role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
                raise Forbidden("Insufficient permission")
                # Assign ghost host to unmanaged vfolder

        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        if action.name.startswith(".") and action.name != ".local":
            if action.group_id_or_name is not None:
                raise VFolderInvalidParameter("dot-prefixed vfolders cannot be a group folder.")

        group_uuid: uuid.UUID | None = None
        group_type: ProjectType | None = None
        max_vfolder_count: int
        max_quota_scope_size: int
        container_uid: int | None = None

        # Get resource information using repository
        match group_id_or_name:
            case str() | uuid.UUID():
                group_info = await self._vfolder_repository.get_group_resource_info(
                    group_id_or_name, domain_name
                )
                if not group_info:
                    raise ProjectNotFound(f"Project with {group_id_or_name} not found.")
                group_uuid, max_vfolder_count, max_quota_scope_size, group_type = group_info
                container_uid = None
            case None:
                user_info = await self._vfolder_repository.get_user_resource_info(user_uuid)
                if not user_info:
                    raise ObjectNotFound(object_name="User")
                max_vfolder_count, max_quota_scope_size, container_uid = user_info
                group_uuid = None
                group_type = None
            case _:
                raise ProjectNotFound(f"Project with {group_id_or_name} not found.")

        vfolder_permission_mode = (
            VFOLDER_GROUP_PERMISSION_MODE if container_uid is not None else None
        )

        # Check if group exists when it's given a non-empty value.
        if group_id_or_name and group_uuid is None:
            raise ProjectNotFound(f"Project with {group_id_or_name} not found.")

        # Determine the ownership type and the quota scope ID.
        if group_uuid is not None:
            ownership_type = "group"
            quota_scope_id = QuotaScopeID(QuotaScopeType.PROJECT, group_uuid)
            if (
                user_role not in (UserRole.SUPERADMIN, UserRole.ADMIN)
                and group_type != ProjectType.MODEL_STORE
            ):
                raise Forbidden("no permission")
        else:
            ownership_type = "user"
            quota_scope_id = QuotaScopeID(QuotaScopeType.USER, user_uuid)
        if ownership_type not in allowed_vfolder_types:
            raise VFolderInvalidParameter(
                f"{ownership_type}-owned vfolder is not allowed in this cluster"
            )

        if group_type == ProjectType.MODEL_STORE:
            if action.usage_mode != VFolderUsageMode.MODEL:
                raise VFolderInvalidParameter(
                    "Only Model VFolder can be created under the model store project"
                )

        # Check host permissions
        await self._vfolder_repository.ensure_host_permission_allowed(
            folder_host,
            permission=VFolderHostPermission.CREATE,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=user_uuid,
            resource_policy=keypair_resource_policy,
            domain_name=domain_name,
            group_id=group_uuid,
        )

        # Check resource policy's max_vfolder_count using repository
        if max_vfolder_count > 0:
            if ownership_type == "user":
                current_count = await self._vfolder_repository.count_vfolders_by_user(user_uuid)
            else:
                if group_uuid is None:
                    raise VFolderInvalidParameter("Group UUID is required for group-owned vfolders")
                current_count = await self._vfolder_repository.count_vfolders_by_group(group_uuid)

            if current_count >= max_vfolder_count:
                raise VFolderInvalidParameter("You cannot create more vfolders.")

        # Check for duplicate vfolder names using repository
        name_exists = await self._vfolder_repository.check_vfolder_name_exists(
            action.name,
            user_uuid,
            user_role,
            domain_name,
            list(allowed_vfolder_types),
        )
        if name_exists:
            raise VFolderAlreadyExists(
                f"VFolder with the given name already exists. ({action.name})"
            )

        folder_id = uuid.uuid4()
        try:
            vfid = VFolderID(quota_scope_id, folder_id)
            if not unmanaged_path:
                proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
                    folder_host, is_unmanaged(unmanaged_path)
                )
                manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
                await manager_client.create_folder(
                    volume_name,
                    str(vfid),
                    max_quota_scope_size,
                    vfolder_permission_mode,
                )
        except aiohttp.ClientResponseError as e:
            raise VFolderCreationFailure from e

        # By default model store VFolder should be considered as read only for every users but without the creator
        if group_type == ProjectType.MODEL_STORE:
            action.mount_permission = VFolderPermission.READ_ONLY

        # Use repository to create VFolder
        params = VFolderCreateParams(
            id=folder_id,
            name=action.name,
            domain_name=domain_name,
            quota_scope_id=str(quota_scope_id),
            usage_mode=action.usage_mode,
            permission=action.mount_permission,
            host=folder_host,
            creator=action.creator_email,
            ownership_type=VFolderOwnershipType(ownership_type),
            user=user_uuid if ownership_type == "user" else None,
            group=group_uuid if ownership_type == "group" else None,
            unmanaged_path=unmanaged_path,
            cloneable=action.cloneable,
            status=VFolderOperationStatus.READY,
        )

        try:
            # Create with permission if it's a model store
            create_owner_permission = group_type == ProjectType.MODEL_STORE
            await self._vfolder_repository.create_vfolder_with_permission(
                params, create_owner_permission=create_owner_permission
            )
        except sa_exc.DataError as e:
            raise VFolderInvalidParameter from e

        return CreateVFolderActionResult(
            id=folder_id,
            name=action.name,
            quota_scope_id=quota_scope_id,
            host=folder_host,
            unmanaged_path=unmanaged_path,
            usage_mode=action.usage_mode,
            mount_permission=action.mount_permission,
            user_uuid=user_uuid if ownership_type == "user" else None,
            group_uuid=group_uuid if ownership_type == "group" else None,
            creator_email=action.creator_email,
            ownership_type=VFolderOwnershipType(ownership_type),
            cloneable=action.cloneable,
            status=VFolderOperationStatus.READY,
        )

    async def update_attribute(
        self, action: UpdateVFolderAttributeAction
    ) -> UpdateVFolderAttributeActionResult:
        spec = cast(VFolderAttributeUpdaterSpec, action.updater.spec)
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        # Get user info using repository
        user_info = await self._vfolder_repository.get_user_info(action.user_uuid)
        if not user_info:
            raise ObjectNotFound(object_name="User")
        user_role, user_domain_name = user_info

        # Get all accessible vfolders to check for name conflicts
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
        )

        if not vfolder_list_result.vfolders:
            raise VFolderNotFound()

        # Check for name conflicts if name is being updated
        try:
            new_name = spec.name.value()
        except ValueError:
            pass
        else:
            for access_info in vfolder_list_result.vfolders:
                if access_info.vfolder_data.name == new_name:
                    raise VFolderInvalidParameter(
                        "One of your accessible vfolders already has the name you requested."
                    )

        # Update the vfolder using repository
        await self._vfolder_repository.update_vfolder_attribute(action.updater)

        return UpdateVFolderAttributeActionResult(vfolder_uuid=action.vfolder_uuid)

    async def get(self, action: GetVFolderAction) -> GetVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        # Get user info using repository
        user_info = await self._vfolder_repository.get_user_info(action.user_uuid)
        if not user_info:
            raise ObjectNotFound(object_name="User")
        user_role, user_domain_name = user_info

        # Use repository to get accessible vfolders
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
            extra_conditions=(VFolderRow.id == action.vfolder_uuid),
        )

        if not vfolder_list_result.vfolders:
            raise VFolderNotFound()

        vfolder_access_info = vfolder_list_result.vfolders[0]
        vfolder_data = vfolder_access_info.vfolder_data

        if vfolder_access_info.effective_permission is None:
            is_owner = True
            permission = VFolderPermission.OWNER_PERM
        else:
            is_owner = vfolder_access_info.is_owner
            permission = vfolder_access_info.effective_permission

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        usage = await manager_client.get_folder_usage(
            volume_name,
            str(VFolderID(vfolder_data.quota_scope_id, vfolder_data.id)),
        )
        usage_info = VFolderUsageInfo(
            used_bytes=usage["used_bytes"],
            num_files=usage["file_count"],
        )
        return GetVFolderActionResult(
            user_uuid=action.user_uuid,
            base_info=VFolderBaseInfo(
                id=vfolder_data.id,
                quota_scope_id=vfolder_data.quota_scope_id,
                name=vfolder_data.name,
                host=vfolder_data.host,
                status=vfolder_data.status,
                unmanaged_path=vfolder_data.unmanaged_path,
                mount_permission=permission,
                usage_mode=vfolder_data.usage_mode,
                created_at=vfolder_data.created_at,
                cloneable=vfolder_data.cloneable,
            ),
            ownership_info=VFolderOwnershipInfo(
                creator_email=vfolder_data.creator,
                ownership_type=vfolder_data.ownership_type,
                is_owner=is_owner,
                user_uuid=vfolder_data.user,
                group_uuid=vfolder_data.group,
            ),
            usage_info=usage_info,
        )

    async def list(self, action: ListVFolderAction) -> ListVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        # Get user info using repository
        user_info = await self._vfolder_repository.get_user_info(action.user_uuid)
        if not user_info:
            raise ObjectNotFound(object_name="User")
        user_role, user_domain_name = user_info

        # Use repository to get accessible vfolders
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
        )

        vfolders = [
            (
                VFolderBaseInfo(
                    id=access_info.vfolder_data.id,
                    quota_scope_id=access_info.vfolder_data.quota_scope_id,
                    name=access_info.vfolder_data.name,
                    host=access_info.vfolder_data.host,
                    status=access_info.vfolder_data.status,
                    unmanaged_path=access_info.vfolder_data.unmanaged_path,
                    # None means owner, who has full permissions
                    mount_permission=access_info.effective_permission
                    or VFolderMountPermission.RW_DELETE,
                    usage_mode=access_info.vfolder_data.usage_mode,
                    created_at=access_info.vfolder_data.created_at,
                    cloneable=access_info.vfolder_data.cloneable,
                ),
                VFolderOwnershipInfo(
                    creator_email=access_info.vfolder_data.creator,
                    ownership_type=access_info.vfolder_data.ownership_type,
                    is_owner=access_info.is_owner,
                    user_uuid=access_info.vfolder_data.user,
                    group_uuid=access_info.vfolder_data.group,
                ),
            )
            for access_info in vfolder_list_result.vfolders
        ]

        return ListVFolderActionResult(
            user_uuid=action.user_uuid,
            vfolders=vfolders,
            _scope_type=action._scope_type,
            _scope_id=action.scope_id(),
        )

    async def move_to_trash(
        self, action: MoveToTrashVFolderAction
    ) -> MoveToTrashVFolderActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        if not user.domain_name:
            raise VFolderInvalidParameter("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._vfolder_repository.move_vfolders_to_trash([vfolder_data.id])
        return MoveToTrashVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def restore(
        self, action: RestoreVFolderFromTrashAction
    ) -> RestoreVFolderFromTrashActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        if not user.domain_name:
            raise VFolderInvalidParameter("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._vfolder_repository.restore_vfolders_from_trash([vfolder_data.id])
        return RestoreVFolderFromTrashActionResult(vfolder_uuid=action.vfolder_uuid)

    async def _remove_vfolder_from_storage(self, vfolder_data: VFolderData) -> None:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )
        try:
            manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
            await manager_client.delete_folder(
                volume_name,
                str(VFolderID(vfolder_data.quota_scope_id, vfolder_data.id)),
            )
        except VFolderGone as e:
            # If the vfolder is already gone, just delete it from the repository
            log.warning("VFolder {} is already gone: {}", vfolder_data.id, e)
        except VFolderNotFound as e:
            # If the vfolder is not found, just delete it from the repository
            log.warning("VFolder {} not found: {}", vfolder_data.id, e)

    async def delete_forever(
        self, action: DeleteForeverVFolderAction
    ) -> DeleteForeverVFolderActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        if not user.domain_name:
            raise VFolderInvalidParameter("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._vfolder_repository.delete_vfolders_forever([action.vfolder_uuid])
        await self._remove_vfolder_from_storage(vfolder_data)
        return DeleteForeverVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def purge(self, action: PurgeVFolderAction) -> PurgeVFolderActionResult:
        """Purge a DELETE_COMPLETE vfolder from DB (admin only)."""
        data = await self._vfolder_repository.purge_vfolder(action.purger)
        return PurgeVFolderActionResult(vfolder_uuid=data.id)

    async def force_delete(
        self, action: ForceDeleteVFolderAction
    ) -> ForceDeleteVFolderActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        if not user.domain_name:
            raise VFolderInvalidParameter("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._vfolder_repository.delete_vfolders_forever([action.vfolder_uuid])
        await self._remove_vfolder_from_storage(vfolder_data)
        return ForceDeleteVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def clone(self, action: CloneVFolderAction) -> CloneVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        if "user" not in allowed_vfolder_types:
            raise VFolderInvalidParameter("user vfolder cannot be created in this host")

        # Get requester user info
        user_info = await self._vfolder_repository.get_user_info(action.requester_user_uuid)
        if not user_info:
            raise VFolderInvalidParameter("No such user.")
        user_role, user_domain_name = user_info

        # Get accessible vfolders to find the source folder
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.requester_user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
            extra_conditions=(VFolderRow.id == action.source_vfolder_uuid),
        )

        if not vfolder_list_result.vfolders:
            raise VFolderInvalidParameter("No such vfolder.")

        source_vfolder_access_info = vfolder_list_result.vfolders[0]
        source_vfolder_data = source_vfolder_access_info.vfolder_data

        # Check if the source vfolder is allowed to be cloned
        if not source_vfolder_data.cloneable:
            raise Forbidden("The source vfolder is not permitted to be cloned.")

        if action.target_name.startswith("."):
            for entry in vfolder_list_result.vfolders:
                if entry.vfolder_data.name == action.target_name:
                    raise VFolderAlreadyExists

        # Get target host
        target_folder_host = (
            action.target_host
            or source_vfolder_data.host
            or self._config_provider.config.volumes.default_host
        )
        if not target_folder_host:
            raise VFolderInvalidParameter(
                "You must specify the vfolder host because the default host is not configured."
            )

        # Verify target vfolder name
        if not verify_vfolder_name(action.target_name):
            raise VFolderInvalidParameter(
                f"{action.target_name} is reserved for internal operations."
            )

        # Check for duplicate vfolder names
        duplication_exists = await self._vfolder_repository.check_vfolder_name_exists(
            action.target_name,
            action.requester_user_uuid,
            user_role,
            user_domain_name,
            list(allowed_vfolder_types),
        )

        if duplication_exists:
            raise VFolderAlreadyExists(
                f"VFolder with the given name already exists. ({action.target_name})"
            )

        allowed_vfolder_hosts = await self._vfolder_repository.get_allowed_vfolder_hosts(
            action.requester_user_uuid, None
        )

        # Check host permissions using the user's actual resource policy
        await self._vfolder_repository.ensure_host_permission_allowed(
            target_folder_host,
            permission=VFolderHostPermission.CREATE,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=action.requester_user_uuid,
            resource_policy={"allowed_vfolder_hosts": allowed_vfolder_hosts},
            domain_name=user_domain_name,
            group_id=source_vfolder_data.group,
        )

        max_vfolder_count = await self._vfolder_repository.get_max_vfolder_count(
            action.requester_user_uuid, source_vfolder_data.group
        )

        # Check resource policy's max_vfolder_count
        if max_vfolder_count > 0:
            current_count = await self._vfolder_repository.count_vfolders_by_user(
                action.requester_user_uuid
            )
            if current_count >= max_vfolder_count:
                raise VFolderInvalidParameter("You cannot create more vfolders.")

        # Get user email for creator field
        requester_email = await self._vfolder_repository.get_user_email_by_id(
            action.requester_user_uuid
        )
        if not requester_email:
            raise VFolderInvalidParameter("No such user.")

        # Create source and target VFolderID
        source_folder_id = VFolderID(source_vfolder_data.quota_scope_id, source_vfolder_data.id)
        target_quota_scope_id = "..."  # TODO: implement

        # Create VFolderCloneInfo for the cloning operation
        vfolder_clone_info = VFolderCloneInfo(
            source_vfolder_id=source_folder_id,
            source_host=source_vfolder_data.host,
            unmanaged_path=source_vfolder_data.unmanaged_path,
            domain_name=user_domain_name,
            target_quota_scope_id=target_quota_scope_id,
            target_vfolder_name=action.target_name,
            target_host=target_folder_host,
            usage_mode=action.usage_mode,
            permission=action.mount_permission,
            email=requester_email,
            user_id=action.requester_user_uuid,
            cloneable=action.cloneable,
        )

        # Initiate the actual vfolder cloning process using repository
        task_id, target_folder_id = await self._vfolder_repository.initiate_vfolder_clone(
            vfolder_clone_info,
            self._storage_manager,
            self._background_task_manager,
        )

        # Return the information about the destination vfolder
        return CloneVFolderActionResult(
            vfolder_uuid=action.source_vfolder_uuid,
            target_vfolder_id=target_folder_id,
            target_vfolder_name=action.target_name,
            target_vfolder_host=target_folder_host,
            usage_mode=action.usage_mode,
            mount_permission=action.mount_permission,
            creator_email=requester_email,
            ownership_type=VFolderOwnershipType.USER,
            owner_user_uuid=action.requester_user_uuid,
            owner_group_uuid=None,
            cloneable=action.cloneable,
            bgtask_id=task_id,
        )

    async def get_task_logs(self, action: GetTaskLogsAction) -> GetTaskLogsActionResult:
        user_uuid = action.user_id
        user_role = action.user_role
        kernel_id_str = action.kernel_id.hex

        # Get user info using repository
        user_info = await self._vfolder_repository.get_user_info(user_uuid)
        if not user_info:
            raise UserNotFound(object_name="User")
        user_role, user_domain_name = user_info

        # Get the .logs vfolder using repository
        log_vfolder_data = await self._vfolder_repository.get_logs_vfolder(
            user_uuid, user_role, user_domain_name
        )
        if not log_vfolder_data:
            raise VFolderNotFound(
                extra_data={"vfolder_name": ".logs"},
            )

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            log_vfolder_data.host, is_unmanaged(log_vfolder_data.unmanaged_path)
        )
        response = web.StreamResponse(status=200)
        response.headers[hdrs.CONTENT_TYPE] = "text/plain"
        prepared = False

        try:
            vfid = str(VFolderID(log_vfolder_data.quota_scope_id, log_vfolder_data.id))
            relpath = str(
                PurePosixPath("task")
                / kernel_id_str[:2]
                / kernel_id_str[2:4]
                / f"{kernel_id_str[4:]}.log",
            )
            storage_proxy_client = self._storage_manager.get_manager_facing_client(proxy_name)

            async for chunk in storage_proxy_client.fetch_file_content_streaming(
                volume_name, vfid, relpath
            ):
                if not prepared:
                    await response.prepare(action.request)
                    prepared = True
                await response.write(chunk)

        except aiohttp.ClientResponseError as e:
            raise UnexpectedStorageProxyResponseError(status=e.status, extra_msg=e.message) from e
        finally:
            if prepared:
                await response.write_eof()
        return GetTaskLogsActionResult(response=response, vfolder_data=log_vfolder_data)

    async def list_allowed_types(
        self, action: ListAllowedTypesAction
    ) -> ListAllowedTypesActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        return ListAllowedTypesActionResult(allowed_types=list(allowed_vfolder_types))

    async def list_all_hosts(self, action: ListAllHostsAction) -> ListAllHostsActionResult:
        all_volumes = await self._storage_manager.get_all_volumes()
        all_hosts = {
            f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes
        }
        default_host = self._config_provider.config.volumes.default_host
        if default_host not in all_hosts:
            default_host = None
        return ListAllHostsActionResult(default=default_host, allowed=sorted(all_hosts))

    async def get_volume_perf_metric(
        self, action: GetVolumePerfMetricAction
    ) -> GetVolumePerfMetricActionResult:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(action.folder_host)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        storage_reply = await manager_client.get_volume_performance_metric(volume_name)
        return GetVolumePerfMetricActionResult(data=dict(storage_reply))

    async def get_usage(self, action: GetVFolderUsageAction) -> GetVFolderUsageActionResult:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            action.folder_host, is_unmanaged(action.unmanaged_path)
        )
        client = self._storage_manager.get_manager_facing_client(proxy_name)
        usage = await client.get_folder_usage(volume_name, action.vfolder_id)
        return GetVFolderUsageActionResult(data=dict(usage))

    async def get_used_bytes(
        self, action: GetVFolderUsedBytesAction
    ) -> GetVFolderUsedBytesActionResult:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            action.folder_host, is_unmanaged(action.unmanaged_path)
        )
        client = self._storage_manager.get_manager_facing_client(proxy_name)
        usage = await client.get_used_bytes(volume_name, action.vfolder_id)
        return GetVFolderUsedBytesActionResult(data=dict(usage))

    async def list_hosts(self, action: ListHostsAction) -> ListHostsActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        allowed_hosts = await self._vfolder_repository.get_allowed_hosts_for_listing(
            user_uuid=action.user_uuid,
            domain_name=action.domain_name,
            group_id=action.group_id,
            resource_policy=action.resource_policy,
            allowed_vfolder_types=list(allowed_vfolder_types),
        )
        all_volumes = await self._storage_manager.get_all_volumes()
        all_hosts = {
            f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes
        }
        allowed_hosts = VFolderHostPermissionMap({
            host: perms for host, perms in allowed_hosts.items() if host in all_hosts
        })

        default_host = self._config_provider.config.volumes.default_host
        if default_host not in allowed_hosts:
            default_host = None

        volumes = [
            (proxy_name, volume_data)
            for proxy_name, volume_data in all_volumes
            if f"{proxy_name}:{volume_data['name']}" in allowed_hosts
        ]

        fetch_volume_tasks = [
            self._fetch_exposed_volume_fields(proxy_name, volume_data["name"])
            for proxy_name, volume_data in volumes
        ]
        get_sftp_tasks = [
            self._storage_manager.get_sftp_scaling_groups(proxy_name)
            for proxy_name, volume_data in volumes
        ]

        fetch_results, sftp_results = await asyncio.gather(
            asyncio.gather(*fetch_volume_tasks),
            asyncio.gather(*get_sftp_tasks),
        )

        volume_info: dict[str, Any] = {}
        for (proxy_name, volume_data), usage, sftp_scaling_groups in zip(
            volumes,
            fetch_results,
            sftp_results,
            strict=True,
        ):
            host_key = f"{proxy_name}:{volume_data['name']}"
            volume_info[host_key] = {
                "backend": volume_data["backend"],
                "capabilities": volume_data["capabilities"],
                "usage": usage,
                "sftp_scaling_groups": sftp_scaling_groups,
            }

        return ListHostsActionResult(
            default=default_host,
            allowed=sorted(allowed_hosts),
            volume_info=volume_info,
        )

    async def _fetch_exposed_volume_fields(
        self,
        proxy_name: str,
        volume_name: str,
    ) -> dict[str, int | float]:
        """Fetch exposed volume usage fields (percentage, used_bytes, capacity_bytes)."""
        volume_usage: dict[str, int | float] = {}
        exposed = self._storage_manager._exposed_volume_info

        show_percentage = "percentage" in exposed
        show_used = "used_bytes" in exposed
        show_total = "capacity_bytes" in exposed

        if show_percentage or show_used or show_total:
            volume_usage_cache = await self._valkey_stat_client.get_volume_usage(
                proxy_name, volume_name
            )
            if volume_usage_cache:
                volume_usage = msgpack.unpackb(volume_usage_cache)
            else:
                manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
                storage_reply = await manager_client.get_fs_usage(volume_name)
                storage_used_bytes = storage_reply["used_bytes"]
                storage_capacity_bytes = storage_reply["capacity_bytes"]

                if show_used:
                    volume_usage["used"] = storage_used_bytes
                if show_total:
                    volume_usage["total"] = storage_capacity_bytes
                if show_percentage:
                    try:
                        volume_usage["percentage"] = storage_used_bytes / storage_capacity_bytes
                    except ZeroDivisionError:
                        volume_usage["percentage"] = 0.0

        return volume_usage

    async def get_quota(self, action: GetQuotaAction) -> GetQuotaActionResult:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            action.folder_host, is_unmanaged(action.unmanaged_path)
        )

        if action.user_role != UserRole.SUPERADMIN:
            allowed_vfolder_types = (
                await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
            )
            await self._vfolder_repository.check_vfolder_accessible(
                vfolder_id=action.vfolder_id,
                user_uuid=action.user_uuid,
                user_role=action.user_role,
                domain_name=action.domain_name,
                allowed_vfolder_types=list(allowed_vfolder_types),
            )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        storage_reply = await manager_client.get_volume_quota(volume_name, action.vfid)
        return GetQuotaActionResult(data=dict(storage_reply))

    async def update_quota(self, action: UpdateQuotaAction) -> UpdateQuotaActionResult:
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            action.folder_host, is_unmanaged(action.unmanaged_path)
        )
        quota = action.size_bytes

        if action.user_role != UserRole.SUPERADMIN:
            allowed_vfolder_types = (
                await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
            )
            await self._vfolder_repository.ensure_host_permission_allowed(
                action.folder_host,
                permission=VFolderHostPermission.MODIFY,
                allowed_vfolder_types=list(allowed_vfolder_types),
                user_uuid=action.user_uuid,
                resource_policy=action.resource_policy,
                domain_name=action.domain_name,
            )
            await self._vfolder_repository.check_vfolder_accessible(
                vfolder_id=action.vfolder_id,
                user_uuid=action.user_uuid,
                user_role=action.user_role,
                domain_name=action.domain_name,
                allowed_vfolder_types=list(allowed_vfolder_types),
            )

        max_quota_scope_size = action.resource_policy.get("max_quota_scope_size", 0)
        if max_quota_scope_size > 0 and (quota <= 0 or quota > max_quota_scope_size):
            quota = max_quota_scope_size

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.update_volume_quota(volume_name, action.vfid, quota)

        await self._vfolder_repository.update_vfolder_max_size(
            action.vfolder_id, math.ceil(quota / 2**20)
        )

        return UpdateQuotaActionResult(size_bytes=quota)

    async def change_vfolder_ownership(
        self, action: ChangeVFolderOwnershipAction
    ) -> ChangeVFolderOwnershipActionResult:
        await self._vfolder_repository.change_vfolder_ownership(
            action.vfolder_id, action.user_email
        )
        return ChangeVFolderOwnershipActionResult()

    # ------------------------------------------------------------------
    # Mount operations (superadmin-only, agent watcher orchestration)
    # ------------------------------------------------------------------

    async def _get_watcher_info(self, agent_id: str) -> dict[str, Any]:
        """Get watcher connection info for an agent."""
        token = self._config_provider.config.watcher.token
        if token is None:
            token = "insecure"
        agent_ip = await self._etcd.get(f"nodes/agents/{agent_id}/ip")
        raw_watcher_port = await self._etcd.get(
            f"nodes/agents/{agent_id}/watcher_port",
        )
        watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
        addr = yarl.URL(f"http://{agent_ip}:{watcher_port}")
        return {
            "addr": addr,
            "token": token,
        }

    async def _get_mount_prefix(self) -> str:
        mount_prefix = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "volumes/_mount"
        )
        if mount_prefix is None:
            mount_prefix = "/mnt"
        return mount_prefix

    async def list_mounts(self, action: ListMountsAction) -> ListMountsActionResult:
        """List mount points from manager, storage proxy, and agents."""
        mount_prefix = await self._get_mount_prefix()
        _ = mount_prefix  # mount_prefix used contextually by caller if needed

        all_volumes = [*await self._storage_manager.get_all_volumes()]
        all_mounts: list[Any] = [volume_data["path"] for _proxy_name, volume_data in all_volumes]
        all_vfolder_hosts = [
            f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes
        ]

        manager_result = MountResultData(
            success=True,
            mounts=all_mounts,
            message="(legacy)",
        )
        storage_proxy_result = MountResultData(
            success=True,
            mounts=[list(pair) for pair in zip(all_vfolder_hosts, all_mounts, strict=True)],
            message="",
        )

        agent_ids = await self._vfolder_repository.get_alive_agent_ids()

        async def _fetch_mounts(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultData]:
            async with sema:
                watcher_info = await self._get_watcher_info(agent_id)
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                async with sess.get(url, headers=headers) as watcher_resp:
                    if watcher_resp.status == 200:
                        data = MountResultData(
                            success=True,
                            mounts=await watcher_resp.json(),
                            message="",
                        )
                    else:
                        data = MountResultData(
                            success=False,
                            mounts=[],
                            message=await watcher_resp.text(),
                        )
                    return (agent_id, data)

        agents_result: dict[str, MountResultData] = {}
        client_timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=client_timeout) as sess:
            sema = asyncio.Semaphore(8)
            mounts = await asyncio.gather(
                *[_fetch_mounts(sema, sess, aid) for aid in agent_ids],
                return_exceptions=True,
            )
            for mount in mounts:
                if isinstance(mount, BaseException):
                    continue
                agents_result[mount[0]] = mount[1]

        return ListMountsActionResult(
            manager=manager_result,
            storage_proxy=storage_proxy_result,
            agents=agents_result,
        )

    async def mount_host(self, action: MountHostAction) -> MountHostActionResult:
        """Mount a filesystem on agents via agent watchers."""
        manager_result = MountResultData(
            success=True,
            message="Managers do not have mountpoints since v20.09.",
        )

        agent_ids = await self._vfolder_repository.get_alive_agent_ids(action.scaling_group)

        mount_params = {
            "fs_location": action.fs_location,
            "name": action.name,
            "fs_type": action.fs_type,
            "options": action.options,
            "scaling_group": action.scaling_group,
            "fstab_path": action.fstab_path,
            "edit_fstab": action.edit_fstab,
        }

        async def _mount(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultData]:
            async with sema:
                watcher_info = await self._get_watcher_info(agent_id)
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                async with sess.post(url, json=mount_params, headers=headers) as resp:
                    if resp.status == 200:
                        data = MountResultData(
                            success=True,
                            message=await resp.text(),
                        )
                    else:
                        data = MountResultData(
                            success=False,
                            message=await resp.text(),
                        )
                    return (agent_id, data)

        agents_result: dict[str, MountResultData] = {}
        client_timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=client_timeout) as sess:
            sema = asyncio.Semaphore(8)
            mount_results = await asyncio.gather(
                *[_mount(sema, sess, aid) for aid in agent_ids],
                return_exceptions=True,
            )
            for mount_result in mount_results:
                if isinstance(mount_result, BaseException):
                    continue
                agents_result[mount_result[0]] = mount_result[1]

        return MountHostActionResult(
            manager=manager_result,
            agents=agents_result,
        )

    async def umount_host(self, action: UmountHostAction) -> UmountHostActionResult:
        """Unmount a filesystem from agents via agent watchers."""
        mount_prefix = await self._get_mount_prefix()
        mountpoint = Path(mount_prefix) / action.name
        if Path(mount_prefix) == mountpoint:
            raise VFolderBadRequest("Mount prefix and mountpoint cannot be the same")

        # Check that no active kernel is using this mount
        mounted_names = await self._vfolder_repository.get_active_kernel_mount_names()
        if action.name in mounted_names:
            raise VFolderOperationFailed("Target host is used in sessions")

        agent_ids = await self._vfolder_repository.get_alive_agent_ids(action.scaling_group)

        manager_result = MountResultData(
            success=True,
            message="Managers do not have mountpoints since v20.09.",
        )

        umount_params = {
            "name": action.name,
            "scaling_group": action.scaling_group,
            "fstab_path": action.fstab_path,
            "edit_fstab": action.edit_fstab,
        }

        async def _umount(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultData]:
            async with sema:
                watcher_info = await self._get_watcher_info(agent_id)
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                async with sess.delete(url, json=umount_params, headers=headers) as resp:
                    if resp.status == 200:
                        data = MountResultData(
                            success=True,
                            message=await resp.text(),
                        )
                    else:
                        data = MountResultData(
                            success=False,
                            message=await resp.text(),
                        )
                    return (agent_id, data)

        agents_result: dict[str, MountResultData] = {}
        client_timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=client_timeout) as sess:
            sema = asyncio.Semaphore(8)
            umount_results = await asyncio.gather(
                *[_umount(sema, sess, aid) for aid in agent_ids],
                return_exceptions=True,
            )
            for umount_result in umount_results:
                if isinstance(umount_result, BaseException):
                    continue
                agents_result[umount_result[0]] = umount_result[1]

        return UmountHostActionResult(
            manager=manager_result,
            agents=agents_result,
        )

    async def get_fstab_contents(
        self, action: GetFstabContentsAction
    ) -> GetFstabContentsActionResult:
        """Get fstab contents from an agent watcher or return a manager stub."""
        fstab_path = action.fstab_path if action.fstab_path is not None else "/etc/fstab"
        if action.agent_id is None:
            return GetFstabContentsActionResult(
                content=(
                    "# Since Backend.AI 20.09, reading the manager fstab is no longer supported."
                ),
                node="manager",
                node_id="manager",
            )

        watcher_info = await self._get_watcher_info(action.agent_id)
        try:
            client_timeout = aiohttp.ClientTimeout(total=10.0)
            async with aiohttp.ClientSession(timeout=client_timeout) as sess:
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "fstab"
                params = {"fstab_path": fstab_path}
                async with sess.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        return GetFstabContentsActionResult(
                            content=content,
                            node="agent",
                            node_id=action.agent_id,
                        )
                    message = await resp.text()
                    raise BackendAgentError(
                        "FAILURE",
                        f"({resp.status}: {resp.reason}) {message}",
                    )
        except asyncio.CancelledError:
            raise
        except BackendAgentError:
            raise
        except TimeoutError as e:
            raise BackendAgentError("TIMEOUT", "Could not fetch fstab data from agent") from e
        except Exception as e:
            raise InternalServerError from e

    async def get_accessible_vfolder(
        self, action: GetAccessibleVFolderAction
    ) -> GetAccessibleVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        entries = await self._vfolder_repository.get_accessible_rows(
            user_uuid=action.user_uuid,
            user_role=action.user_role,
            domain_name=action.domain_name,
            is_admin=action.is_admin,
            allowed_vfolder_types=allowed_vfolder_types,
            perm=action.perm,
            folder_id_or_name=action.folder_id_or_name,
            allow_privileged_access=action.allow_privileged_access,
        )
        if len(entries) == 0:
            raise VFolderNotFound(extra_data=action.folder_id_or_name)
        if len(entries) > 1:
            raise TooManyVFoldersFound(entries)
        row = entries[0]
        if action.required_status is not None:
            await _check_vfolder_status(row["status"], action.required_status)
        return GetAccessibleVFolderActionResult(row=row)
