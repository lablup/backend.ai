import logging
import uuid
from pathlib import PurePosixPath
from typing import (
    Optional,
)

import aiohttp
from aiohttp import hdrs, web
from sqlalchemy import exc as sa_exc

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.defs import VFOLDER_GROUP_PERMISSION_MODE
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
)
from ai.backend.manager.errors.common import Forbidden, ObjectNotFound
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    UnexpectedStorageProxyResponseError,
    VFolderAlreadyExists,
    VFolderCreationFailure,
    VFolderFilterStatusFailed,
    VFolderFilterStatusNotAvailable,
    VFolderGone,
    VFolderInvalidParameter,
    VFolderNotFound,
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

from ..actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetTaskLogsAction,
    GetTaskLogsActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ..types import VFolderBaseInfo, VFolderOwnershipInfo, VFolderUsageInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


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
    _storage_manager: StorageSessionManager
    _background_task_manager: BackgroundTaskManager
    _vfolder_repository: VfolderRepository
    _user_repository: UserRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        storage_manager: StorageSessionManager,
        background_task_manager: BackgroundTaskManager,
        vfolder_repository: VfolderRepository,
        user_repository: UserRepository,
    ) -> None:
        self._config_provider = config_provider
        self._storage_manager = storage_manager
        self._vfolder_repository = vfolder_repository
        self._user_repository = user_repository
        self._background_task_manager = background_task_manager

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

        group_uuid: Optional[uuid.UUID] = None
        group_type: Optional[ProjectType] = None
        max_vfolder_count: int
        max_quota_scope_size: int
        container_uid: Optional[int] = None

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
                assert group_uuid is not None
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
        from ai.backend.manager.data.vfolder.types import VFolderCreateParams

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
        except sa_exc.DataError:
            raise VFolderInvalidParameter

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
        modifier = action.modifier
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
            new_name = modifier.name.value()
        except ValueError:
            pass
        else:
            for access_info in vfolder_list_result.vfolders:
                if access_info.vfolder_data.name == new_name:
                    raise VFolderInvalidParameter(
                        "One of your accessible vfolders already has the name you requested."
                    )

        # Update the vfolder using repository
        to_update = modifier.fields_to_update()
        await self._vfolder_repository.update_vfolder_attribute(action.vfolder_uuid, to_update)

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
                    mount_permission=access_info.effective_permission,
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
            _scope_type=action.scope_type(),
            _scope_id=action.scope_id(),
        )

    async def move_to_trash(
        self, action: MoveToTrashVFolderAction
    ) -> MoveToTrashVFolderActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
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
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._remove_vfolder_from_storage(vfolder_data)
        await self._vfolder_repository.delete_vfolders_forever([action.vfolder_uuid])
        return DeleteForeverVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def force_delete(
        self, action: ForceDeleteVFolderAction
    ) -> ForceDeleteVFolderActionResult:
        # TODO: Implement proper permission checking and business logic
        # For now, use admin repository for the operation
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        await self._remove_vfolder_from_storage(vfolder_data)
        await self._vfolder_repository.delete_vfolders_forever([action.vfolder_uuid])
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
        target_folder_host = action.target_host or source_vfolder_data.host
        if not target_folder_host:
            target_folder_host = self._config_provider.config.volumes.default_host
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
            action.requester_user_uuid, source_vfolder_data.group
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
            raise UnexpectedStorageProxyResponseError(status=e.status, extra_msg=e.message)
        finally:
            if prepared:
                await response.write_eof()
        return GetTaskLogsActionResult(response=response, vfolder_data=log_vfolder_data)
