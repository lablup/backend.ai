import uuid
from typing import Any, Optional, Union

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.vfolder.types import (
    VFolderAccessInfo,
    VFolderCreateParams,
    VFolderData,
    VFolderInvitationData,
    VFolderListResult,
    VFolderPermissionData,
)
from ai.backend.manager.errors.exceptions import (
    ObjectNotFound,
    VFolderNotFound,
)
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderInvitationRow,
    VFolderInvitationState,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
    query_accessible_vfolders,
)


class VfolderRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
                user_role=user_row.role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=(VFolderRow.id == vfolder_id),
            )

            if not vfolder_dicts:
                raise VFolderNotFound()

            return self._vfolder_row_to_data(vfolder_row)

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

    async def create_vfolder(self, params: VFolderCreateParams) -> VFolderData:
        """
        Create a new VFolder with the given parameters.
        Returns the created VFolderData.
        """
        async with self._db.begin_session() as session:
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

            # Return the created vfolder data
            created_vfolder = await self._get_vfolder_by_id(session, params.id)
            if not created_vfolder:
                raise VFolderNotFound()
            return self._vfolder_row_to_data(created_vfolder)

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

            # Create owner permission if requested
            if create_owner_permission and params.user:
                permission_insert = sa.insert(VFolderPermissionRow).values({
                    "user": params.user,
                    "vfolder": params.id.hex,
                    "permission": VFolderPermission.OWNER_PERM,
                })
                await session.execute(permission_insert)

            # Return the created vfolder data
            created_vfolder = await self._get_vfolder_by_id(session, params.id)
            if not created_vfolder:
                raise VFolderNotFound()
            return self._vfolder_row_to_data(created_vfolder)

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

            return VFolderPermissionData(
                id=permission_id,
                vfolder=vfolder_id,
                user=user_id,
                permission=permission,
            )

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

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple user IDs.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_session() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.uuid.in_(user_ids)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

    async def get_group_resource_info(
        self, group_id_or_name: Union[str, uuid.UUID], domain_name: str
    ) -> Optional[tuple[uuid.UUID, int, int, ProjectType]]:
        """
        Get group resource information by group ID or name.
        Returns (group_uuid, max_vfolder_count, max_quota_scope_size, group_type) or None.
        """
        from ai.backend.manager.models.group import GroupRow

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

    async def get_users_by_emails(self, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple emails.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_session() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.email.in_(emails)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

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
