import uuid
from pathlib import PurePosixPath
from typing import (
    Any,
    Optional,
    cast,
)

import aiohttp
import sqlalchemy as sa
from aiohttp import hdrs, web
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.defs import VFOLDER_GROUP_PERMISSION_MODE
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.manager.config.constant import DEFAULT_CHUNK_SIZE
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.exceptions import ObjectNotFound, StorageProxyError
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry
from ai.backend.manager.models.vfolder import (
    HARD_DELETED_VFOLDER_STATUSES,
    VFolderCloneInfo,
    VFolderDeletionInfo,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
    VFolderStatusSet,
    delete_vfolder_relation_rows,
    ensure_host_permission_allowed,
    filter_host_allowed_permission,
    initiate_vfolder_clone,
    initiate_vfolder_deletion,
    is_unmanaged,
    query_accessible_vfolders,
    update_vfolder_status,
    verify_vfolder_name,
    vfolder_status_map,
    vfolders,
)

# from ai.backend.manager.types import SENTINEL
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
from ..exceptions import (
    Forbidden,
    ModelServiceDependencyNotCleared,
    ProjectNotFound,
    TooManyVFoldersFound,
    VFolderAlreadyExists,
    VFolderCreationFailure,
    VFolderFilterStatusFailed,
    VFolderFilterStatusNotAvailable,
    VFolderInvalidParameter,
    VFolderNotFound,
)
from ..types import VFolderBaseInfo, VFolderOwnershipInfo, VFolderUsageInfo


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
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _background_task_manager: BackgroundTaskManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
        storage_manager: StorageSessionManager,
        background_task_manager: BackgroundTaskManager,
    ) -> None:
        self._db = db
        self._config_provider = config_provider
        self._storage_manager = storage_manager
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

        async with self._db.begin_session() as sess:
            match group_id_or_name:
                case str():
                    # Convert the group name to group uuid.
                    # log.debug("group_id_or_name(str):{}", group_id_or_name)
                    query = (
                        sa.select(GroupRow)
                        .where(
                            (GroupRow.domain_name == domain_name)
                            & (GroupRow.name == group_id_or_name)
                        )
                        .options(selectinload(GroupRow.resource_policy_row))
                    )
                    result = await sess.execute(query)
                    group_row = cast(Optional[GroupRow], result.scalar())
                    if group_row is None:
                        raise ProjectNotFound(group_id_or_name)
                    _gid, max_vfolder_count, max_quota_scope_size = (
                        cast(Optional[uuid.UUID], group_row.id),
                        cast(int, group_row.resource_policy_row.max_vfolder_count),
                        cast(int, group_row.resource_policy_row.max_quota_scope_size),
                    )
                    if _gid is None:
                        raise ProjectNotFound(group_id_or_name)
                    group_uuid = _gid
                    group_type = cast(ProjectType, group_row.type)
                case uuid.UUID():
                    # Check if the group belongs to the current domain.
                    # log.debug("group_id_or_name(uuid):{}", group_id_or_name)
                    query = (
                        sa.select(GroupRow)
                        .where(
                            (GroupRow.domain_name == domain_name)
                            & (GroupRow.id == group_id_or_name)
                        )
                        .options(selectinload(GroupRow.resource_policy_row))
                    )
                    result = await sess.execute(query)
                    group_row = cast(Optional[GroupRow], result.scalar())
                    if group_row is None:
                        raise ProjectNotFound(group_id_or_name)
                    _gid, max_vfolder_count, max_quota_scope_size = (
                        group_row.id,
                        cast(int, group_row.resource_policy_row.max_vfolder_count),
                        cast(int, group_row.resource_policy_row.max_quota_scope_size),
                    )
                    if _gid is None:
                        raise ProjectNotFound(group_id_or_name)
                    group_uuid = group_id_or_name
                    group_type = cast(ProjectType, group_row.type)
                case None:
                    query = (
                        sa.select(UserRow)
                        .where(UserRow.uuid == user_uuid)
                        .options(selectinload(UserRow.resource_policy_row))
                    )
                    result = await sess.execute(query)
                    user_row = result.scalar()
                    max_vfolder_count, max_quota_scope_size = (
                        cast(int, user_row.resource_policy_row.max_vfolder_count),
                        cast(int, user_row.resource_policy_row.max_quota_scope_size),
                    )
                    container_uid = cast(Optional[int], user_row.container_uid)
                case _:
                    raise ProjectNotFound(group_id_or_name)

            vfolder_permission_mode = (
                VFOLDER_GROUP_PERMISSION_MODE if container_uid is not None else None
            )

            # Check if group exists when it's given a non-empty value.
            if group_id_or_name and group_uuid is None:
                raise ProjectNotFound(group_id_or_name)

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
            if action.mount_permission != VFolderPermission.READ_WRITE:
                raise VFolderInvalidParameter(
                    "Setting custom permission is not supported for model store vfolder"
                )
            if action.usage_mode != VFolderUsageMode.MODEL:
                raise VFolderInvalidParameter(
                    "Only Model VFolder can be created under the model store project"
                )

        async with self._db.begin() as conn:
            await ensure_host_permission_allowed(
                conn,
                folder_host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=user_uuid,
                resource_policy=keypair_resource_policy,
                domain_name=domain_name,
                group_id=group_uuid,
                permission=VFolderHostPermission.CREATE,
            )

            # Check resource policy's max_vfolder_count
            if max_vfolder_count > 0:
                if ownership_type == "user":
                    query = (
                        sa.select(sa.func.count())
                        .select_from(VFolderRow)
                        .where(
                            (VFolderRow.user == user_uuid)
                            & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                        )
                    )
                else:
                    assert group_uuid is not None
                    query = (
                        sa.select(sa.func.count())
                        .select_from(VFolderRow)
                        .where(
                            (VFolderRow.group == group_uuid)
                            & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                        )
                    )
                result = cast(int, await conn.scalar(query))
                if result >= max_vfolder_count:
                    raise VFolderInvalidParameter("You cannot create more vfolders.")

            # DEPRECATED: Limit vfolder size quota if it is larger than max_vfolder_size of the resource policy.
            # max_vfolder_size = resource_policy.get("max_vfolder_size", 0)
            # if max_vfolder_size > 0 and (
            #     params["quota"] is None or params["quota"] <= 0 or params["quota"] > max_vfolder_size
            # ):
            #     params["quota"] = max_vfolder_size

            # Prevent creation of vfolder with duplicated name on all hosts.
            extra_vf_conds = [
                (VFolderRow.name == action.name),
                (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES)),
            ]
            entries = await query_accessible_vfolders(
                conn,
                user_uuid,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=(sa.and_(*extra_vf_conds)),
            )
            if len(entries) > 0:
                raise VFolderAlreadyExists(
                    f"VFolder with the given name already exists. ({action.name})"
                )
            try:
                folder_id = uuid.uuid4()
                vfid = VFolderID(quota_scope_id, folder_id)
                if not unmanaged_path:
                    options = {}
                    if max_quota_scope_size and max_quota_scope_size > 0:
                        options["initial_max_size_for_quota_scope"] = max_quota_scope_size
                    body_data: dict[str, Any] = {
                        "volume": self._storage_manager.get_proxy_and_volume(
                            folder_host, is_unmanaged(unmanaged_path)
                        )[1],
                        "vfid": str(vfid),
                        "options": options,
                    }
                    if vfolder_permission_mode is not None:
                        body_data["mode"] = vfolder_permission_mode
                    async with self._storage_manager.request(
                        folder_host,
                        "POST",
                        "folder/create",
                        json=body_data,
                    ):
                        pass
            except aiohttp.ClientResponseError as e:
                raise VFolderCreationFailure from e

            # By default model store VFolder should be considered as read only for every users but without the creator
            if group_type == ProjectType.MODEL_STORE:
                action.mount_permission = VFolderPermission.READ_ONLY

            # TODO: include quota scope ID in the database
            # TODO: include quota scope ID in the API response
            insert_values = {
                "id": vfid.folder_id.hex,
                "name": action.name,
                "domain_name": domain_name,
                "quota_scope_id": str(quota_scope_id),
                "usage_mode": action.usage_mode,
                "permission": action.mount_permission,
                "last_used": None,
                "host": folder_host,
                "creator": action.creator_email,
                "ownership_type": VFolderOwnershipType(ownership_type),
                "user": user_uuid if ownership_type == "user" else None,
                "group": group_uuid if ownership_type == "group" else None,
                "unmanaged_path": unmanaged_path,
                "cloneable": action.cloneable,
                "status": VFolderOperationStatus.READY,
            }
            try:
                query = sa.insert(VFolderRow, insert_values)
                result = await conn.execute(query)

                # Here we grant creator the permission to alter VFolder contents
                if group_type == ProjectType.MODEL_STORE:
                    query = sa.insert(VFolderPermissionRow).values({
                        "user": user_uuid,
                        "vfolder": vfid.folder_id.hex,
                        "permission": VFolderPermission.OWNER_PERM,
                    })
                    await conn.execute(query)
            except sa.exc.DataError:
                raise VFolderInvalidParameter
            assert result.rowcount == 1

        return CreateVFolderActionResult(
            id=vfid.folder_id,
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

        async def _update(db_session: AsyncSession) -> None:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            vfolder_dicts = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
            )
            if not vfolder_dicts:
                raise VFolderNotFound
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
            try:
                new_name = modifier.name.value()
            except ValueError:
                pass
            else:
                for row in vfolder_dicts:
                    if row["name"] == new_name:
                        raise VFolderInvalidParameter(
                            "One of your accessible vfolders already has the name you requested."
                        )
            to_update = modifier.fields_to_update()
            for key, value in to_update.items():
                setattr(vfolder_row, key, value)

        async with self._db.connect() as db_conn:
            await execute_with_txn_retry(_update, self._db.begin_session, db_conn)
        return UpdateVFolderAttributeActionResult(vfolder_uuid=action.vfolder_uuid)

    async def get(self, action: GetVFolderAction) -> GetVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            vfolder_dicts = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )
            vfolder_row = vfolder_dicts[0]
        if vfolder_row["permission"] is None:
            is_owner = True
            permission = VFolderPermission.OWNER_PERM
        else:
            is_owner = vfolder_row["is_owner"]
            permission = vfolder_row["permission"]
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row["host"], is_unmanaged(vfolder_row["unmanaged_path"])
        )
        async with self._storage_manager.request(
            proxy_name,
            "GET",
            "folder/usage",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID(vfolder_row["quota_scope_id"], vfolder_row["id"])),
            },
        ) as (_, storage_resp):
            usage = await storage_resp.json()
            usage_info = VFolderUsageInfo(
                used_bytes=usage["used_bytes"],
                num_files=usage["file_count"],
            )
        return GetVFolderActionResult(
            user_uuid=action.user_uuid,
            base_info=VFolderBaseInfo(
                id=vfolder_row["id"],
                quota_scope_id=vfolder_row["quota_scope_id"],
                name=vfolder_row["name"],
                host=vfolder_row["host"],
                status=vfolder_row["status"],
                unmanaged_path=vfolder_row["unmanaged_path"],
                mount_permission=permission,
                usage_mode=vfolder_row["usage_mode"],
                created_at=vfolder_row["created_at"],
                cloneable=vfolder_row["cloneable"],
            ),
            ownership_info=VFolderOwnershipInfo(
                creator_email=vfolder_row["creator"],
                ownership_type=vfolder_row["ownership_type"],
                is_owner=is_owner,
                user_uuid=vfolder_row["user"],
                group_uuid=vfolder_row["group"],
            ),
            usage_info=usage_info,
        )

    async def list(self, action: ListVFolderAction) -> ListVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            vfolder_dicts = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=False,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
            )
        vfolders = [
            (
                VFolderBaseInfo(
                    id=entry["id"],
                    quota_scope_id=entry["quota_scope_id"],
                    name=entry["name"],
                    host=entry["host"],
                    status=entry["status"],
                    unmanaged_path=entry["unmanaged_path"],
                    mount_permission=entry["permission"],
                    usage_mode=entry["usage_mode"],
                    created_at=entry["created_at"],
                    cloneable=entry["cloneable"],
                ),
                VFolderOwnershipInfo(
                    creator_email=entry["creator"],
                    ownership_type=entry["ownership_type"],
                    is_owner=entry["is_owner"],
                    user_uuid=entry["user"],
                    group_uuid=entry["group"],
                ),
            )
            for entry in vfolder_dicts
        ]

        return ListVFolderActionResult(
            user_uuid=action.user_uuid,
            vfolders=vfolders,
        )

    async def move_to_trash(
        self, action: MoveToTrashVFolderAction
    ) -> MoveToTrashVFolderActionResult:
        # Only the effective folder owner can delete the folder.
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.connect() as db_conn:
            async with self._db.begin_session(db_conn) as db_session:
                requester_user_row = await db_session.scalar(
                    sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
                )
                requester_user_row = cast(UserRow, requester_user_row)
                vfolder_dicts = await query_accessible_vfolders(
                    db_session.bind,
                    action.user_uuid,
                    allow_privileged_access=True,
                    user_role=requester_user_row.role,
                    allowed_vfolder_types=allowed_vfolder_types,
                    domain_name=requester_user_row.domain_name,
                    extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
                )
                vfolder_row = vfolder_dicts[0]
                if not vfolder_row["is_owner"]:
                    raise VFolderInvalidParameter(
                        "Cannot delete the vfolder that is not owned by myself."
                    )
                await _check_vfolder_status(vfolder_row["status"], VFolderStatusSet.DELETABLE)
                # perform extra check to make sure records of alive model service not removed by foreign key rule
                if vfolder_row["usage_mode"] == VFolderUsageMode.MODEL:
                    live_endpoints = await EndpointRow.list_by_model(db_session, vfolder_row["id"])
                    if (
                        len([
                            e
                            for e in live_endpoints
                            if e.lifecycle_stage == EndpointLifecycle.CREATED
                        ])
                        > 0
                    ):
                        raise ModelServiceDependencyNotCleared
                folder_host = vfolder_row["host"]
                await ensure_host_permission_allowed(
                    db_session.bind,
                    folder_host,
                    allowed_vfolder_types=allowed_vfolder_types,
                    user_uuid=action.user_uuid,
                    resource_policy=action.keypair_resource_policy,
                    domain_name=requester_user_row.domain_name,
                    permission=VFolderHostPermission.DELETE,
                )

                vfolder_row_ids = (vfolder_row["id"],)
            await delete_vfolder_relation_rows(db_conn, self._db.begin_session, vfolder_row_ids)
        await update_vfolder_status(
            self._db,
            vfolder_row_ids,
            VFolderOperationStatus.DELETE_PENDING,
        )
        return MoveToTrashVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def restore(
        self, action: RestoreVFolderFromTrashAction
    ) -> RestoreVFolderFromTrashActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            restore_targets = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )

            if len(restore_targets) > 1:
                raise TooManyVFoldersFound(restore_targets)
            elif len(restore_targets) == 0:
                raise VFolderInvalidParameter("No such vfolder.")

            row = restore_targets[0]
            await _check_vfolder_status(row["status"], VFolderStatusSet.RECOVERABLE)

        # Folder owner OR user who have DELETE permission can restore folder.
        if not row["is_owner"] and row["permission"] != VFolderPermission.RW_DELETE:
            raise VFolderInvalidParameter("Cannot restore the vfolder that is not owned by myself.")

        # fs-level mv may fail or take longer time
        # but let's complete the db transaction to reflect that it's deleted.
        await update_vfolder_status(self._db, (row["id"],), VFolderOperationStatus.READY)
        return RestoreVFolderFromTrashActionResult(vfolder_uuid=action.vfolder_uuid)

    async def delete_forever(
        self, action: DeleteForeverVFolderAction
    ) -> DeleteForeverVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            entries = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )

            if len(entries) > 1:
                raise TooManyVFoldersFound(entries)
            elif len(entries) == 0:
                raise VFolderInvalidParameter("No such vfolder.")
            row = entries[0]
            await _check_vfolder_status(row["status"], VFolderStatusSet.PURGABLE)

        # fs-level deletion may fail or take longer time
        await initiate_vfolder_deletion(
            self._db,
            [VFolderDeletionInfo(VFolderID.from_row(row), row["host"], row["unmanaged_path"])],
            self._storage_manager,
        )
        return DeleteForeverVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def force_delete(
        self, action: ForceDeleteVFolderAction
    ) -> ForceDeleteVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            entries = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )
            row = entries[0]
            try:
                await _check_vfolder_status(row["status"], VFolderStatusSet.PURGABLE)
            except VFolderFilterStatusFailed:
                await _check_vfolder_status(row["status"], VFolderStatusSet.DELETABLE)
        await initiate_vfolder_deletion(
            self._db,
            [VFolderDeletionInfo(VFolderID.from_row(row), row["host"], row["unmanaged_path"])],
            storage_manager=self._storage_manager,
            force=True,
        )
        return ForceDeleteVFolderActionResult(vfolder_uuid=action.vfolder_uuid)

    async def clone(self, action: CloneVFolderAction) -> CloneVFolderActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        if "user" not in allowed_vfolder_types:
            raise VFolderInvalidParameter("user vfolder cannot be created in this host")
        requester_user_row = await UserRow.get_by_id_with_policies(
            action.requester_user_uuid, db=self._db
        )
        if requester_user_row is None:
            raise VFolderInvalidParameter("No such user.")
        async with self._db.begin_readonly_session() as db_session:
            entries = await query_accessible_vfolders(
                db_session.bind,
                action.requester_user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
            )
            for entry in entries:
                if entry["id"] == action.source_vfolder_uuid:
                    row = entry
                    break
            else:
                raise VFolderInvalidParameter("No such vfolder.")
        project_row: Optional[GroupRow] = None
        if (project_id := row["group"]) is not None:
            project_row = await GroupRow.get_by_id_with_policies(project_id, db=self._db)
        async with self._db.begin_session() as db_session:
            domain_name = requester_user_row.domain_name
            source_folder_host = row["host"]
            source_folder_id = VFolderID(row["quota_scope_id"], row["id"])
            target_folder_host = action.target_host or source_folder_host
            target_quota_scope_id = "..."  # TODO: implement
            source_unmanaged_path = row["unmanaged_path"]
            source_proxy_name, source_volume_name = self._storage_manager.get_proxy_and_volume(
                source_folder_host, is_unmanaged(source_unmanaged_path)
            )
            target_proxy_name, target_volume_name = self._storage_manager.get_proxy_and_volume(
                target_folder_host,
            )

            # check if the source vfolder is allowed to be cloned
            if not row["cloneable"]:
                raise Forbidden("The source vfolder is not permitted to be cloned.")

            if action.target_name.startswith("."):
                for entry in entries:
                    if entry["name"] == action.target_name:
                        raise VFolderAlreadyExists
                    if entry["name"].startswith(".") and entry["path"] == action.target_name:
                        raise VFolderInvalidParameter("VFolder name conflicts with your dotfile.")

            if not target_folder_host:
                target_folder_host = self._config_provider.config.volumes.default_host
                if not target_folder_host:
                    raise VFolderInvalidParameter(
                        "You must specify the vfolder host because the default host is not configured."
                    )

            if not verify_vfolder_name(action.target_name):
                raise VFolderInvalidParameter(
                    f"{action.target_name} is reserved for internal operations."
                )

            if source_proxy_name != target_proxy_name:
                raise VFolderInvalidParameter(
                    "proxy name of source and target vfolders must be equal."
                )

            if project_row is not None:
                vfolder_hosts = project_row.allowed_vfolder_hosts
                max_vfolder_count = project_row.resource_policy_row.max_vfolder_count
            else:
                vfolder_hosts = (
                    requester_user_row.main_keypair.resource_policy_row.allowed_vfolder_hosts
                )
                max_vfolder_count = requester_user_row.resource_policy_row.max_vfolder_count

            allowed_hosts = await filter_host_allowed_permission(
                db_session.bind,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=requester_user_row.uuid,
                resource_policy={"allowed_vfolder_hosts": vfolder_hosts},
                domain_name=domain_name,
            )
            if (
                target_folder_host not in allowed_hosts
                or VFolderHostPermission.CREATE not in allowed_hosts[target_folder_host]
            ):
                raise VFolderInvalidParameter(
                    f"`{VFolderHostPermission.CREATE}` Not allowed in vfolder"
                    f" host(`{target_folder_host}`)"
                )
            # TODO: handle legacy host lists assuming that volume names don't overlap?
            if target_folder_host not in allowed_hosts:
                raise VFolderInvalidParameter("You are not allowed to use this vfolder host.")

            # Check resource policy's max_vfolder_count
            if max_vfolder_count > 0:
                query = sa.select(sa.func.count()).where(
                    sa.and_(
                        VFolderRow.user == requester_user_row.uuid,
                        VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES),
                    )
                )
                result = await db_session.scalar(query)
                if result >= max_vfolder_count:
                    raise VFolderInvalidParameter("You cannot create more vfolders.")

        task_id, target_folder_id = await initiate_vfolder_clone(
            self._db,
            VFolderCloneInfo(
                source_folder_id,
                source_folder_host,
                source_unmanaged_path,
                domain_name,
                target_quota_scope_id,
                action.target_name,
                target_folder_host,
                action.usage_mode,
                action.mount_permission,
                requester_user_row.email,
                requester_user_row.uuid,
                action.cloneable,
            ),
            self._storage_manager,
            self._background_task_manager,
        )

        # Return the information about the destination vfolder.
        return CloneVFolderActionResult(
            vfolder_uuid=source_folder_id.folder_id,
            target_vfolder_id=target_folder_id,
            target_vfolder_name=action.target_name,
            target_vfolder_host=target_folder_host,
            usage_mode=action.usage_mode,
            mount_permission=action.mount_permission,
            creator_email=requester_user_row.email,
            ownership_type=VFolderOwnershipType.USER,
            owner_user_uuid=requester_user_row.uuid,
            owner_group_uuid=None,
            cloneable=action.cloneable,
            bgtask_id=task_id,
        )

    async def get_task_logs(self, action: GetTaskLogsAction) -> GetTaskLogsActionResult:
        user_uuid = action.user_id
        user_role = action.user_role
        domain_name = action.domain_name
        kernel_id_str = action.kernel_id.hex
        request = action.request

        async with self._db.begin_readonly() as conn:
            matched_vfolders = await query_accessible_vfolders(
                conn,
                user_uuid,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=["user"],
                extra_vf_conds=(vfolders.c.name == ".logs"),
            )
            if not matched_vfolders:
                raise ObjectNotFound(
                    extra_data={"vfolder_name": ".logs"},
                    object_name="vfolder",
                )
            log_vfolder = matched_vfolders[0]

        _proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            log_vfolder["host"], is_unmanaged(log_vfolder["unmanaged_path"])
        )
        response = web.StreamResponse(status=200)
        response.headers[hdrs.CONTENT_TYPE] = "text/plain"
        prepared = False

        try:
            async with self._storage_manager.request(
                log_vfolder["host"],
                "POST",
                "folder/file/fetch",
                json={
                    "volume": volume_name,
                    "vfid": str(VFolderID.from_row(log_vfolder)),
                    "relpath": str(
                        PurePosixPath("task")
                        / kernel_id_str[:2]
                        / kernel_id_str[2:4]
                        / f"{kernel_id_str[4:]}.log",
                    ),
                },
                raise_for_status=True,
            ) as (_, storage_resp):
                while True:
                    chunk = await storage_resp.content.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    if not prepared:
                        await response.prepare(request)
                        prepared = True
                    await response.write(chunk)
        except aiohttp.ClientResponseError as e:
            raise StorageProxyError(status=e.status, extra_msg=e.message)
        finally:
            if prepared:
                await response.write_eof()
        return GetTaskLogsActionResult(response=response, vfolder_data=log_vfolder)
