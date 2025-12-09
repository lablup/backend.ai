import uuid
from typing import Any, Mapping, Optional, Sequence, Union

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import VFolderHostPermission, VFolderID
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.manager.data.vfolder.types import (
    VFolderAccessInfo,
    VFolderCreateParams,
    VFolderData,
    VFolderInvitationData,
    VFolderListResult,
    VFolderPermissionData,
)
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    VFolderDeletionNotAllowed,
    VFolderNotFound,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.models.vfolder import (
    VFolderCloneInfo,
    VFolderDeletionInfo,
    VFolderInvitationRow,
    VFolderInvitationState,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
    delete_vfolder_relation_rows,
    ensure_host_permission_allowed,
    get_sessions_by_mounted_folder,
    is_unmanaged,
    query_accessible_vfolders,
    vfolders,
)
from ai.backend.manager.services.vfolder.exceptions import VFolderInvalidParameter

from ..permission_controller.role_manager import RoleManager

# Layer-specific decorator for vfolder repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.VFOLDER)


class VfolderRepository:
    _db: ExtendedAsyncSAEngine
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

    @repository_decorator()
    async def get_by_id_validated(
        self, vfolder_id: uuid.UUID, user_id: uuid.UUID, domain_name: str
    ) -> VFolderData:
        """
        Get a VFolder by ID with ownership/permission validation.
        Returns VFolderData if user has access.
        Raises VFolderNotFound if vfolder doesn't exist or user has no access.
        """
        async with self._db.begin_session() as session:
            vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
            if not vfolder_row:
                raise VFolderNotFound()

            # Check access permissions
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            if not user_row:
                raise ObjectNotFound(object_name="User")

            # Check if user has access to this vfolder
            allowed_vfolder_types = ["user", "group"]  # TODO: get from config
            vfolder_dicts = await query_accessible_vfolders(
                session.bind,
                user_id,
                allow_privileged_access=True,
                user_role=user_row.role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=(VFolderRow.id == vfolder_id),
            )

            if not vfolder_dicts:
                raise VFolderNotFound()

            return self._vfolder_row_to_data(vfolder_row)

    @repository_decorator()
    async def get_by_id(self, vfolder_id: uuid.UUID) -> Optional[VFolderData]:
        """
        Get a VFolder by ID without validation.
        Returns VFolderData if found, None otherwise.
        """
        async with self._db.begin_session() as session:
            vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
            if not vfolder_row:
                return None
            return self._vfolder_row_to_data(vfolder_row)

    @repository_decorator()
    async def get_allowed_vfolder_hosts(
        self, user_uuid: uuid.UUID, group_uuid: Optional[uuid.UUID]
    ) -> str:
        """
        Get the allowed VFolder hosts for a user.
        """
        async with self._db.begin_readonly_session() as db_session:
            if group_uuid:
                group_row: Optional[GroupRow] = await db_session.scalar(
                    sa.select(GroupRow).where(GroupRow.id == group_uuid)
                )
                if group_row is None:
                    raise ProjectNotFound(f"Project with {group_uuid} not found.")

                return group_row.allowed_vfolder_hosts

            user_row: Optional[UserRow] = await db_session.scalar(
                sa.select(UserRow)
                .where(UserRow.uuid == user_uuid)
                .options(
                    selectinload(UserRow.main_keypair).selectinload(KeyPairRow.resource_policy_row)
                )
            )
            if user_row is None:
                raise UserNotFound(f"User with UUID {user_uuid} not found.")

            return user_row.main_keypair.resource_policy_row.allowed_vfolder_hosts

    @repository_decorator()
    async def get_max_vfolder_count(
        self, user_uuid: uuid.UUID, group_uuid: Optional[uuid.UUID]
    ) -> int:
        """
        Get the maximum VFolder count for a user or group.
        """
        async with self._db.begin_readonly_session() as db_session:
            if group_uuid:
                group_row: Optional[GroupRow] = await db_session.scalar(
                    sa.select(GroupRow)
                    .where(GroupRow.id == group_uuid)
                    .options(selectinload(GroupRow.resource_policy_row))
                )
                if group_row is None:
                    raise ProjectNotFound(f"Project with {group_uuid} not found.")

                return group_row.resource_policy_row.max_vfolder_count

            user_row: Optional[UserRow] = await db_session.scalar(
                sa.select(UserRow)
                .where(UserRow.uuid == user_uuid)
                .options(selectinload(UserRow.resource_policy_row))
            )
            if user_row is None:
                raise UserNotFound(f"User with UUID {user_uuid} not found.")

            return user_row.resource_policy_row.max_vfolder_count

    @repository_decorator()
    async def list_accessible_vfolders(
        self,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        allowed_vfolder_types: list[str],
        extra_conditions: Optional[sa.sql.expression.BinaryExpression] = None,
    ) -> VFolderListResult:
        """
        List all VFolders accessible to a user.
        Returns VFolderListResult with access information.
        """
        async with self._db.begin_session() as session:
            vfolder_dicts = await query_accessible_vfolders(
                session.bind,
                user_id,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=extra_conditions,
            )

            vfolder_access_infos = []
            for vfolder_dict in vfolder_dicts:
                vfolder_data = self._vfolder_dict_to_data(dict(vfolder_dict))
                is_owner = vfolder_dict.get("is_owner", False)
                permission = vfolder_dict.get("permission", VFolderPermission.READ_ONLY)

                vfolder_access_infos.append(
                    VFolderAccessInfo(
                        vfolder_data=vfolder_data,
                        is_owner=is_owner,
                        effective_permission=permission,
                    )
                )

            return VFolderListResult(vfolders=vfolder_access_infos)

    @repository_decorator()
    async def create_vfolder_with_permission(
        self, params: VFolderCreateParams, create_owner_permission: bool = False
    ) -> VFolderData:
        """
        Create a new VFolder with the given parameters and optionally create owner permission.
        Returns the created VFolderData.
        """
        async with self._db.begin_session() as session:
            # Create the VFolder
            insert_values = {
                "id": params.id.hex,
                "name": params.name,
                "domain_name": params.domain_name,
                "quota_scope_id": params.quota_scope_id,
                "usage_mode": params.usage_mode,
                "permission": params.permission,
                "last_used": None,
                "host": params.host,
                "creator": params.creator,
                "ownership_type": params.ownership_type,
                "user": params.user,
                "group": params.group,
                "unmanaged_path": params.unmanaged_path,
                "cloneable": params.cloneable,
                "status": params.status,
            }

            query = sa.insert(VFolderRow, insert_values)
            result = await session.execute(query)
            assert result.rowcount == 1
            match params.ownership_type:
                case VFolderOwnershipType.USER:
                    scope_id = ScopeId(ScopeType.USER, str(params.user))
                case VFolderOwnershipType.GROUP:
                    scope_id = ScopeId(ScopeType.PROJECT, str(params.group))
            await self._role_manager.map_entity_to_scope(
                session,
                entity_id=ObjectId(
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(params.id),
                ),
                scope_id=scope_id,
            )

            # Create owner permission if requested
            if create_owner_permission and params.user:
                permission_insert = sa.insert(VFolderPermissionRow).values({
                    "user": params.user,
                    "vfolder": params.id.hex,
                    "permission": VFolderPermission.OWNER_PERM,
                })
                await session.execute(permission_insert)
                await self._role_manager.map_entity_to_scope(
                    session,
                    entity_id=ObjectId(
                        entity_type=EntityType.VFOLDER,
                        entity_id=str(params.id),
                    ),
                    scope_id=ScopeId(ScopeType.USER, str(params.user)),
                )
                await self._role_manager.add_object_permission_to_user_role(
                    session,
                    user_id=params.user,
                    entity_id=ObjectId(
                        entity_type=EntityType.VFOLDER,
                        entity_id=str(params.id),
                    ),
                    operations=[OperationType.READ],
                )

            # Return the created vfolder data
            created_vfolder = await self._get_vfolder_by_id(session, params.id)
            if not created_vfolder:
                raise VFolderNotFound()
            return self._vfolder_row_to_data(created_vfolder)

    @repository_decorator()
    async def update_vfolder_attribute(
        self, vfolder_id: uuid.UUID, field_updates: dict[str, Any]
    ) -> VFolderData:
        """
        Update VFolder attributes.
        Returns updated VFolderData.
        """
        async with self._db.begin_session() as session:
            vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
            if not vfolder_row:
                raise VFolderNotFound()

            for key, value in field_updates.items():
                if hasattr(vfolder_row, key):
                    setattr(vfolder_row, key, value)

            await session.flush()
            return self._vfolder_row_to_data(vfolder_row)

    @repository_decorator()
    async def move_vfolders_to_trash(self, vfolder_ids: list[uuid.UUID]) -> list[VFolderData]:
        """
        Move VFolders to trash.
        """

        async with self._db.begin_session() as session:
            vfolder_rows = []
            for vfolder_id in vfolder_ids:
                vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
                if vfolder_row:
                    vfolder_rows.append(vfolder_row)

            # Create deletion info for each vfolder
            deletion_infos = []
            for vfolder_row in vfolder_rows:
                vfolder_id_obj = VFolderID(
                    quota_scope_id=vfolder_row.quota_scope_id,
                    folder_id=vfolder_row.id,
                )
                deletion_info = VFolderDeletionInfo(
                    vfolder_id=vfolder_id_obj,
                    host=vfolder_row.host,
                    unmanaged_path=vfolder_row.unmanaged_path,
                )
                deletion_infos.append(deletion_info)

            # Note: initiate_vfolder_deletion requires storage_manager parameter
            # This would need to be passed to the repository method or handled differently
            # For now, we'll update the status directly instead of using the full deletion process
            for vfolder_row in vfolder_rows:
                mount_sessions = await get_sessions_by_mounted_folder(
                    session, VFolderID.from_row(vfolder_row)
                )
                if mount_sessions:
                    session_ids = [str(session_id) for session_id in mount_sessions]
                    raise VFolderDeletionNotAllowed(
                        "Cannot delete the vfolder. "
                        f"The vfolder(id: {vfolder_row.id}) is mounted on sessions(ids: {session_ids})."
                    )
                vfolder_row.status = VFolderOperationStatus.DELETE_PENDING

            await session.flush()

            return [self._vfolder_row_to_data(row) for row in vfolder_rows]

    @repository_decorator()
    async def restore_vfolders_from_trash(self, vfolder_ids: list[uuid.UUID]) -> list[VFolderData]:
        """
        Restore VFolders from trash.
        """
        async with self._db.begin_session() as session:
            vfolder_rows = []
            for vfolder_id in vfolder_ids:
                vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
                if vfolder_row:
                    vfolder_row.status = VFolderOperationStatus.READY
                    vfolder_rows.append(vfolder_row)

            await session.flush()
            return [self._vfolder_row_to_data(row) for row in vfolder_rows]

    @repository_decorator()
    async def delete_vfolders_forever(self, vfolder_ids: list[uuid.UUID]) -> list[VFolderData]:
        """
        Delete VFolders forever
        """

        async with self._db.connect() as db_conn:
            async with self._db.begin_session(db_conn) as db_session:
                vfolder_rows = []
                for vfolder_id in vfolder_ids:
                    vfolder_row = await self._get_vfolder_by_id(db_session, vfolder_id)
                    if vfolder_row:
                        vfolder_rows.append(vfolder_row)
                delete_stmt = (
                    sa.update(VFolderRow)
                    .where(VFolderRow.id.in_(vfolder_ids))
                    .values(status=VFolderOperationStatus.DELETE_ONGOING)
                )
                await db_session.execute(delete_stmt)

            # Delete relation rows
            await delete_vfolder_relation_rows(db_conn, self._db.begin_session, vfolder_ids)

            return [self._vfolder_row_to_data(row) for row in vfolder_rows]

    @repository_decorator()
    async def get_vfolder_permissions(self, vfolder_id: uuid.UUID) -> list[VFolderPermissionData]:
        """
        Get all permissions for a VFolder.
        """
        async with self._db.begin_session() as session:
            query = sa.select(VFolderPermissionRow).where(
                VFolderPermissionRow.vfolder == vfolder_id
            )
            result = await session.execute(query)
            permission_rows = result.scalars().all()

            return [
                VFolderPermissionData(
                    id=row.id,
                    vfolder=row.vfolder,
                    user=row.user,
                    permission=row.permission,
                )
                for row in permission_rows
            ]

    @repository_decorator()
    async def create_vfolder_permission(
        self,
        vfolder_id: uuid.UUID,
        user_id: uuid.UUID,
        permission: VFolderPermission,
    ) -> VFolderPermissionData:
        """
        Create a VFolder permission entry.
        """
        async with self._db.begin_session() as session:
            permission_id = uuid.uuid4()
            insert_values = {
                "id": permission_id,
                "vfolder": vfolder_id,
                "user": user_id,
                "permission": permission,
            }

            query = sa.insert(VFolderPermissionRow, insert_values)
            await session.execute(query)

            await self._role_manager.map_entity_to_scope(
                session,
                entity_id=ObjectId(
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(vfolder_id),
                ),
                scope_id=ScopeId(ScopeType.USER, str(user_id)),
            )
            await self._role_manager.add_object_permission_to_user_role(
                session,
                user_id=user_id,
                entity_id=ObjectId(
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(vfolder_id),
                ),
                operations=permission.to_rbac_operation(),
            )

            return VFolderPermissionData(
                id=permission_id,
                vfolder=vfolder_id,
                user=user_id,
                permission=permission,
            )

    @repository_decorator()
    async def delete_vfolder_permission(self, vfolder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Delete a VFolder permission entry.
        """
        async with self._db.begin_session() as session:
            query = sa.delete(VFolderPermissionRow).where(
                (VFolderPermissionRow.vfolder == vfolder_id)
                & (VFolderPermissionRow.user == user_id)
            )
            await session.execute(query)
            await self._role_manager.unmap_entity_from_scope(
                session,
                entity_id=ObjectId(
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(vfolder_id),
                ),
                scope_id=ScopeId(ScopeType.USER, str(user_id)),
            )
            await self._role_manager.delete_object_permission_of_user(
                session,
                user_id,
                vfolder_id,
            )

    @repository_decorator()
    async def get_vfolder_invitations_by_vfolder(
        self, vfolder_id: uuid.UUID
    ) -> list[VFolderInvitationData]:
        """
        Get all invitations for a VFolder.
        """
        async with self._db.begin_session() as session:
            query = sa.select(VFolderInvitationRow).where(
                VFolderInvitationRow.vfolder == vfolder_id
            )
            result = await session.execute(query)
            invitation_rows = result.scalars().all()

            return [
                VFolderInvitationData(
                    id=row.id,
                    vfolder=row.vfolder,
                    inviter=row.inviter,
                    invitee=row.invitee,
                    permission=row.permission,
                    created_at=row.created_at,
                    modified_at=row.modified_at,
                )
                for row in invitation_rows
            ]

    @repository_decorator()
    async def count_vfolders_by_user(self, user_id: uuid.UUID) -> int:
        """
        Count VFolders owned by a user (excluding hard deleted ones).
        """
        from ai.backend.manager.models.vfolder import HARD_DELETED_VFOLDER_STATUSES

        async with self._db.begin_session() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderRow)
                .where(
                    (VFolderRow.user == user_id)
                    & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                )
            )
            result = await session.scalar(query)
            return result or 0

    @repository_decorator()
    async def count_vfolders_by_group(self, group_id: uuid.UUID) -> int:
        """
        Count VFolders owned by a group (excluding hard deleted ones).
        """
        from ai.backend.manager.models.vfolder import HARD_DELETED_VFOLDER_STATUSES

        async with self._db.begin_session() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderRow)
                .where(
                    (VFolderRow.group == group_id)
                    & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                )
            )
            result = await session.scalar(query)
            return result or 0

    @repository_decorator()
    async def check_vfolder_name_exists(
        self,
        name: str,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        allowed_vfolder_types: list[str],
    ) -> bool:
        """
        Check if a VFolder with the given name already exists for the user.
        """
        from ai.backend.manager.models.vfolder import HARD_DELETED_VFOLDER_STATUSES

        async with self._db.begin_session() as session:
            # Use query_accessible_vfolders to check accessible folders
            extra_vf_conds = sa.and_(
                (VFolderRow.name == name),
                (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES)),
            )

            vfolder_dicts = await query_accessible_vfolders(
                session.bind,
                user_id,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=extra_vf_conds,
            )

            return len(vfolder_dicts) > 0

    @repository_decorator()
    async def get_user_info(self, user_id: uuid.UUID) -> Optional[tuple[UserRole, str]]:
        """
        Get user role and domain name for a user.
        Returns (role, domain_name) or None if user not found.
        """
        async with self._db.begin_session() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            if not user_row:
                return None
            return user_row.role, user_row.domain_name

    @repository_decorator()
    async def get_user_email_by_id(self, user_id: uuid.UUID) -> Optional[str]:
        """
        Get user email by user ID.
        Returns email or None if user not found.
        """
        async with self._db.begin_session() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            if not user_row:
                return None
            return user_row.email

    @repository_decorator()
    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple user IDs.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_session() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.uuid.in_(user_ids)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

    @repository_decorator()
    async def get_group_resource_info(
        self, group_id_or_name: Union[str, uuid.UUID], domain_name: str
    ) -> Optional[tuple[uuid.UUID, int, int, ProjectType]]:
        """
        Get group resource information by group ID or name.
        Returns (group_uuid, max_vfolder_count, max_quota_scope_size, group_type) or None.
        """

        async with self._db.begin_session() as session:
            if isinstance(group_id_or_name, str):
                query = (
                    sa.select(GroupRow)
                    .where(
                        (GroupRow.domain_name == domain_name) & (GroupRow.name == group_id_or_name)
                    )
                    .options(selectinload(GroupRow.resource_policy_row))
                )
            else:  # UUID
                query = (
                    sa.select(GroupRow)
                    .where(
                        (GroupRow.domain_name == domain_name) & (GroupRow.id == group_id_or_name)
                    )
                    .options(selectinload(GroupRow.resource_policy_row))
                )

            result = await session.execute(query)
            group_row = result.scalar()

            if not group_row:
                return None

            return (
                group_row.id,
                group_row.resource_policy_row.max_vfolder_count,
                group_row.resource_policy_row.max_quota_scope_size,
                group_row.type,
            )

    @repository_decorator()
    async def get_user_resource_info(
        self, user_id: uuid.UUID
    ) -> Optional[tuple[int, int, Optional[int]]]:
        """
        Get user resource information.
        Returns (max_vfolder_count, max_quota_scope_size, container_uid) or None.
        """
        async with self._db.begin_session() as session:
            query = (
                sa.select(UserRow)
                .where(UserRow.uuid == user_id)
                .options(selectinload(UserRow.resource_policy_row))
            )
            result = await session.execute(query)
            user_row = result.scalar()

            if not user_row:
                return None

            return (
                user_row.resource_policy_row.max_vfolder_count,
                user_row.resource_policy_row.max_quota_scope_size,
                user_row.container_uid,
            )

    async def _get_vfolder_by_id(
        self, session: SASession, vfolder_id: uuid.UUID
    ) -> Optional[VFolderRow]:
        """
        Private method to get a VFolder by ID using an existing session.
        """
        query = sa.select(VFolderRow).where(VFolderRow.id == vfolder_id)
        result = await session.execute(query)
        return result.scalar()

    async def _validate_vfolder_ownership(
        self, session: SASession, vfolder_id: uuid.UUID, user_id: uuid.UUID
    ) -> VFolderRow:
        """
        Private method to validate VFolder ownership.
        Raises VFolderNotFound if vfolder doesn't exist or user doesn't own it.
        """
        vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
        if not vfolder_row:
            raise VFolderNotFound()

        # Check ownership
        is_owner = False
        if vfolder_row.ownership_type == VFolderOwnershipType.USER:
            is_owner = vfolder_row.user == user_id
        elif vfolder_row.ownership_type == VFolderOwnershipType.GROUP:
            # TODO: check group membership
            pass

        if not is_owner:
            raise VFolderNotFound()

        return vfolder_row

    def _vfolder_row_to_data(self, row: VFolderRow) -> VFolderData:
        """
        Convert VFolderRow to VFolderData.
        """
        return VFolderData(
            id=row.id,
            name=row.name,
            host=row.host,
            domain_name=row.domain_name,
            quota_scope_id=row.quota_scope_id,
            usage_mode=row.usage_mode,
            permission=row.permission,
            max_files=row.max_files,
            max_size=row.max_size,
            num_files=row.num_files,
            cur_size=row.cur_size,
            created_at=row.created_at,
            last_used=row.last_used,
            creator=row.creator,
            unmanaged_path=row.unmanaged_path,
            ownership_type=row.ownership_type,
            user=row.user,
            group=row.group,
            cloneable=row.cloneable,
            status=row.status,
        )

    @repository_decorator()
    async def check_user_has_vfolder_permission(
        self, vfolder_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> bool:
        """
        Check if any of the users already have permission for the vfolder.
        Returns True if any user already has permission.
        """
        from ai.backend.manager.models.vfolder import VFolderPermissionRow

        async with self._db.begin_session() as session:
            # Check direct permissions and ownership
            j = sa.join(
                VFolderPermissionRow, VFolderRow, VFolderRow.id == VFolderPermissionRow.vfolder
            )
            count_query = (
                sa.select(sa.func.count())
                .select_from(j)
                .where(
                    sa.and_(
                        sa.or_(
                            VFolderPermissionRow.user.in_(user_ids),
                            VFolderRow.user.in_(user_ids),
                        ),
                        VFolderPermissionRow.vfolder == vfolder_id,
                    )
                )
            )
            count = await session.scalar(count_query)
            return count > 0

    @repository_decorator()
    async def get_user_by_email(self, email: str) -> Optional[tuple[uuid.UUID, str]]:
        """
        Get user info by email.
        Returns (user_id, domain_name) or None if user not found.
        """
        async with self._db.begin_session() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.email == email))
            if not user_row:
                return None
            return user_row.uuid, user_row.domain_name

    @repository_decorator()
    async def get_users_by_emails(self, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple emails.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_session() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.email.in_(emails)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

    @repository_decorator()
    async def count_vfolder_with_name_for_user(self, user_id: uuid.UUID, vfolder_name: str) -> int:
        """
        Count VFolders with the given name accessible to the user.
        Used to check for duplicates when accepting invitations.
        """
        from ai.backend.manager.models.vfolder import VFolderStatusSet, vfolder_status_map

        async with self._db.begin_session() as session:
            j = sa.join(
                VFolderRow,
                VFolderPermissionRow,
                VFolderRow.id == VFolderPermissionRow.vfolder,
                isouter=True,
            )
            query = (
                sa.select(sa.func.count())
                .select_from(j)
                .where(
                    sa.and_(
                        sa.or_(
                            VFolderRow.user == user_id,
                            VFolderPermissionRow.user == user_id,
                        ),
                        VFolderRow.name == vfolder_name,
                        VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]),
                    )
                )
            )
            result = await session.scalar(query)
            return result or 0

    @repository_decorator()
    async def check_pending_invitation_exists(
        self, vfolder_id: uuid.UUID, inviter_email: str, invitee_email: str
    ) -> bool:
        """
        Check if a pending invitation already exists.
        Returns True if a pending invitation exists.
        """
        async with self._db.begin_session() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderInvitationRow)
                .where(
                    (VFolderInvitationRow.inviter == inviter_email)
                    & (VFolderInvitationRow.invitee == invitee_email)
                    & (VFolderInvitationRow.vfolder == vfolder_id)
                    & (VFolderInvitationRow.state == VFolderInvitationState.PENDING),
                )
            )
            result = await session.scalar(query)
            return result > 0

    @repository_decorator()
    async def create_vfolder_invitation(
        self,
        vfolder_id: uuid.UUID,
        inviter_email: str,
        invitee_email: str,
        permission: VFolderPermission,
    ) -> Optional[str]:
        """
        Create a VFolder invitation.
        Returns the invitee email on success, None on failure.
        """
        from sqlalchemy import exc as sa_exc

        async with self._db.begin_session() as session:
            query = sa.insert(
                VFolderInvitationRow,
                {
                    "permission": permission,
                    "vfolder": vfolder_id,
                    "inviter": inviter_email,
                    "invitee": invitee_email,
                    "state": VFolderInvitationState.PENDING,
                },
            )
            try:
                await session.execute(query)
                return invitee_email
            except sa_exc.DataError:
                return None

    @repository_decorator()
    async def get_invitation_by_id(
        self, invitation_id: uuid.UUID
    ) -> Optional[VFolderInvitationData]:
        """
        Get invitation by ID.
        Returns VFolderInvitationData or None if not found.
        """
        async with self._db.begin_session() as session:
            query = sa.select(VFolderInvitationRow).where(
                (VFolderInvitationRow.id == invitation_id)
                & (VFolderInvitationRow.state == VFolderInvitationState.PENDING),
            )
            invitation_row = await session.scalar(query)
            if not invitation_row:
                return None

            return VFolderInvitationData(
                id=invitation_row.id,
                vfolder=invitation_row.vfolder,
                inviter=invitation_row.inviter,
                invitee=invitation_row.invitee,
                permission=invitation_row.permission,
                created_at=invitation_row.created_at,
                modified_at=invitation_row.modified_at,
            )

    @repository_decorator()
    async def update_invitation_state(
        self, invitation_id: uuid.UUID, new_state: VFolderInvitationState
    ) -> None:
        """
        Update invitation state.
        """
        async with self._db.begin_session() as session:
            query = (
                sa.update(VFolderInvitationRow)
                .where(VFolderInvitationRow.id == invitation_id)
                .values(state=new_state)
            )
            await session.execute(query)

    @repository_decorator()
    async def update_invitation_permission(
        self, invitation_id: uuid.UUID, inviter_email: str, permission: VFolderPermission
    ) -> None:
        """
        Update invitation permission (only by inviter).
        """
        async with self._db.begin_session() as session:
            query = (
                sa.update(VFolderInvitationRow)
                .values(permission=permission)
                .where(
                    sa.and_(
                        VFolderInvitationRow.id == invitation_id,
                        VFolderInvitationRow.inviter == inviter_email,
                        VFolderInvitationRow.state == VFolderInvitationState.PENDING,
                    )
                )
            )
            await session.execute(query)

    @repository_decorator()
    async def update_invited_vfolder_mount_permission(
        self, vfolder_id: uuid.UUID, user_id: uuid.UUID, permission: VFolderPermission
    ) -> None:
        """
        Update the permission of an invited user for a specific vfolder.
        """
        async with self._db.begin_session() as session:
            query = (
                sa.update(VFolderPermissionRow)
                .where(
                    sa.and_(
                        VFolderPermissionRow.vfolder == vfolder_id,
                        VFolderPermissionRow.user == user_id,
                    )
                )
                .values(permission=permission)
            )
            await session.execute(query)

    @repository_decorator()
    async def get_pending_invitations_for_user(
        self, user_email: str
    ) -> list[tuple[VFolderInvitationData, VFolderData]]:
        """
        Get all pending invitations for a user with VFolder info.
        Returns list of (invitation_data, vfolder_data) tuples.
        """
        from sqlalchemy.orm import contains_eager

        async with self._db.begin_session() as session:
            j = sa.join(
                VFolderInvitationRow, VFolderRow, VFolderInvitationRow.vfolder == VFolderRow.id
            )
            query = (
                sa.select(VFolderInvitationRow)
                .select_from(j)
                .where(
                    sa.and_(
                        VFolderInvitationRow.invitee == user_email,
                        VFolderInvitationRow.state == VFolderInvitationState.PENDING,
                    )
                )
                .options(
                    contains_eager(VFolderInvitationRow.vfolder_row),
                )
            )
            invitation_rows = await session.scalars(query)
            invitation_rows = invitation_rows.all()

            results = []
            for inv_row in invitation_rows:
                invitation_data = VFolderInvitationData(
                    id=inv_row.id,
                    vfolder=inv_row.vfolder,
                    inviter=inv_row.inviter,
                    invitee=inv_row.invitee,
                    permission=inv_row.permission,
                    created_at=inv_row.created_at,
                    modified_at=inv_row.modified_at,
                )
                vfolder_data = self._vfolder_row_to_data(inv_row.vfolder_row)
                results.append((invitation_data, vfolder_data))

            return results

    @repository_decorator()
    async def ensure_host_permission_allowed(
        self,
        folder_host: str,
        *,
        permission: VFolderHostPermission,
        allowed_vfolder_types: Sequence[str],
        user_uuid: uuid.UUID,
        resource_policy: Mapping[str, Any],
        domain_name: str,
        group_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Ensure that the user has the required permission on the specified vfolder host.
        """
        async with self._db.begin_session() as session:
            await ensure_host_permission_allowed(
                session.bind,
                folder_host,
                permission=permission,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=user_uuid,
                resource_policy=resource_policy,
                domain_name=domain_name,
                group_id=group_id,
            )

    def _vfolder_dict_to_data(self, vfolder_dict: dict[str, Any]) -> VFolderData:
        """
        Convert vfolder dictionary from query_accessible_vfolders to VFolderData.
        """
        return VFolderData(
            id=vfolder_dict["id"],
            name=vfolder_dict["name"],
            host=vfolder_dict["host"],
            domain_name=vfolder_dict["domain_name"],
            quota_scope_id=vfolder_dict["quota_scope_id"],
            usage_mode=vfolder_dict["usage_mode"],
            permission=vfolder_dict.get("permission"),
            max_files=vfolder_dict["max_files"],
            max_size=vfolder_dict["max_size"],
            num_files=vfolder_dict.get("num_files", 0),
            cur_size=vfolder_dict["cur_size"],
            created_at=vfolder_dict["created_at"],
            last_used=vfolder_dict["last_used"],
            creator=vfolder_dict["creator"],
            unmanaged_path=vfolder_dict["unmanaged_path"],
            ownership_type=vfolder_dict["ownership_type"],
            user=uuid.UUID(vfolder_dict["user"]) if vfolder_dict["user"] else None,
            group=uuid.UUID(vfolder_dict["group"]) if vfolder_dict["group"] else None,
            cloneable=vfolder_dict["cloneable"],
            status=vfolder_dict["status"],
        )

    @repository_decorator()
    async def initiate_vfolder_clone(
        self,
        vfolder_info: VFolderCloneInfo,
        storage_manager: StorageSessionManager,
        background_task_manager: BackgroundTaskManager,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """
        Initiate VFolder cloning process.
        Returns (task_id, target_folder_id).
        """
        source_vf_cond = vfolders.c.id == vfolder_info.source_vfolder_id.folder_id

        async def _update_source_status() -> None:
            async with self._db.begin_session() as db_session:
                query = (
                    sa.update(vfolders)
                    .values(status=VFolderOperationStatus.CLONING)
                    .where(source_vf_cond)
                )
                await db_session.execute(query)

        await execute_with_retry(_update_source_status)

        target_proxy, target_volume = storage_manager.get_proxy_and_volume(vfolder_info.target_host)
        source_proxy, source_volume = storage_manager.get_proxy_and_volume(
            vfolder_info.source_host, is_unmanaged(vfolder_info.unmanaged_path)
        )

        if source_proxy != target_proxy:
            raise VFolderInvalidParameter(
                f"Proxy names of source and target vfolders must be equal. "
                f"Source proxy: {source_proxy}, Target proxy: {target_proxy}."
            )

        # Generate the ID of the destination vfolder.
        # TODO: If we refactor to use ORM, the folder ID will be created from the database by inserting
        #       the actual object (with RETURNING clause).  In that case, we need to temporarily
        #       mark the object to be "unusable-yet" until the storage proxy creates the destination
        #       vfolder.  After done, we need to make another transaction to clear the unusable state.
        target_folder_id = VFolderID(vfolder_info.source_vfolder_id.quota_scope_id, uuid.uuid4())

        # Clone the vfolder contents
        manager_client = storage_manager.get_manager_facing_client(source_proxy)
        clone_response = await manager_client.clone_folder(
            source_volume,
            str(vfolder_info.source_vfolder_id),
            target_volume,
            str(target_folder_id),
        )
        task_id = clone_response.bgtask_id

        async def _insert_vfolder() -> None:
            async with self._db.begin_session() as db_session:
                insert_values = {
                    "id": target_folder_id.folder_id,
                    "name": vfolder_info.target_vfolder_name,
                    "domain_name": vfolder_info.domain_name,
                    "usage_mode": vfolder_info.usage_mode,
                    "permission": vfolder_info.permission,
                    "last_used": None,
                    "host": vfolder_info.target_host,
                    # TODO: add quota_scope_id
                    "creator": vfolder_info.email,
                    "ownership_type": VFolderOwnershipType("user"),
                    "user": vfolder_info.user_id,
                    "group": None,
                    "unmanaged_path": None,
                    "cloneable": vfolder_info.cloneable,
                    "quota_scope_id": vfolder_info.source_vfolder_id.quota_scope_id,
                }
                query = sa.insert(vfolders).values(**insert_values)
                await db_session.execute(query)

        # Insert the new vfolder record
        await execute_with_retry(_insert_vfolder)

        return task_id, target_folder_id.folder_id

    @repository_decorator()
    async def get_logs_vfolder(
        self,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[VFolderData]:
        """
        Get the accessible .logs vfolder for a user.
        Returns VFolderData if found, None otherwise.
        """
        async with self._db.begin_readonly() as conn:
            vfolder_dicts = await query_accessible_vfolders(
                conn,
                user_id,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=["user"],
                extra_vf_conds=(vfolders.c.name == ".logs"),
            )

            if not vfolder_dicts:
                return None

            # Return the first (and should be only) matching .logs vfolder
            vfolder_dict = vfolder_dicts[0]
            return self._vfolder_dict_to_data(dict(vfolder_dict))
