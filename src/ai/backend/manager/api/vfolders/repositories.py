import uuid
from typing import Any, Awaitable, Callable, Iterable, Optional, ParamSpec, TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.manager.api.exceptions import GroupNotFound, UserNotFound
from ai.backend.manager.data.vfolder.dto import (
    UserIdentity,
    VFolderItem,
    VFolderMetadataToCreate,
    VFolderResourceLimit,
)
from ai.backend.manager.models import (
    HARD_DELETED_VFOLDER_STATUSES,
    ProjectType,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderStatusSet,
    vfolder_status_map,
)
from ai.backend.manager.models.group import AssocGroupUserRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_txn_retry,
)
from ai.backend.manager.models.vfolder import (
    GroupRow,
    UserRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)

_P = ParamSpec("_P")
_TQueryResult = TypeVar("_TQueryResult")


class VFolderRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_group_type(self, group_id: uuid.UUID) -> ProjectType:
        async with self._db.begin_session() as sess:
            query = sa.select(GroupRow).where(GroupRow.id == group_id)
            group_row = await sess.scalar(query)

            if group_row is None:
                raise GroupNotFound(extra_data=group_id)

        return group_row.type

    async def get_user_container_id(self, user_id: uuid.UUID) -> Optional[int]:
        async with self._db.begin_session() as sess:
            query = sa.select(UserRow.container_uid).where(UserRow.uuid == user_id)
            result = await sess.scalar(query)
        return result

    async def get_created_vfolder_count(
        self, owner_id: uuid.UUID, ownership_type: VFolderOwnershipType
    ) -> int:
        async with self._db.begin_session() as sess:
            if ownership_type == VFolderOwnershipType.USER:
                ownership_type_caluse = VFolderRow.user == owner_id
            else:
                ownership_type_caluse = VFolderRow.group == owner_id

            query = (
                sa.select([sa.func.count()])
                .select_from(VFolderRow)
                .where(
                    (ownership_type_caluse)
                    & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                )
            )
            result = await sess.scalar(query)

        return result

    async def get_user_vfolder_resource_limit(
        self, user_identity: UserIdentity
    ) -> VFolderResourceLimit:
        async with self._db.begin_session() as sess:
            query = (
                sa.select(UserRow)
                .where(UserRow.uuid == user_identity.user_uuid)
                .options(selectinload(UserRow.resource_policy_row))
            )
            user_row = await sess.scalar(query)

            if user_row is None:
                raise UserNotFound(extra_data=user_identity.user_uuid)

            max_vfolder_count = user_row.resource_policy_row.max_vfolder_count
            max_quota_scope_size = user_row.resource_policy_row.max_quota_scope_size

        return VFolderResourceLimit(
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
        )

    async def get_group_vfolder_resource_limit(
        self, user_identity: UserIdentity, group_id: uuid.UUID
    ) -> VFolderResourceLimit:
        async with self._db.begin_session() as sess:
            query = (
                sa.select(GroupRow)
                .where(
                    (GroupRow.domain_name == user_identity.domain_name) & (GroupRow.id == group_id)
                )
                .options(selectinload(GroupRow.resource_policy_row))
            )
            group_row = await sess.scalar(query)

            if group_row is None:
                raise GroupNotFound(extra_data=group_id)

            max_vfolder_count = group_row.resource_policy_row.max_vfolder_count
            max_quota_scope_size = group_row.resource_policy_row.max_quota_scope_size

        return VFolderResourceLimit(
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
        )

    async def persist_vfolder_metadata(self, metadata: VFolderMetadataToCreate) -> VFolderItem:
        async with self._db.begin_session() as sess:
            insert_query = sa.insert(VFolderRow).values(metadata.to_dict()).returning(VFolderRow.id)
            vfolder_id = await sess.scalar(insert_query)

            query = sa.select(VFolderRow).where(VFolderRow.id == vfolder_id)
            vfolder: VFolderRow = await sess.scalar(query)
            vfolder_item = VFolderItem.from_orm(orm=vfolder, is_owner=True)
        return vfolder_item

    async def create_vfolder_permission(
        self,
        user_id: uuid.UUID,
        vfolder_id: uuid.UUID,
        permission: VFolderPermission = VFolderPermission.OWNER_PERM,
    ) -> None:
        async with self._db.begin_session() as sess:
            insert_value: dict[str, Any] = {
                "user": user_id,
                "vfolder": vfolder_id.hex,
                "permission": permission,
            }

            stmt = sa.insert(VFolderPermissionRow).values(insert_value)
            await sess.execute(stmt)

    async def get_accessible_folders(
        self,
        user_identity: UserIdentity,
        allowed_vfolder_types: list[str],
        group_id: Optional[uuid.UUID] = None,
    ) -> list[VFolderItem]:
        all_entries: list[VFolderItem] = []
        async with self._db.begin_session() as sess:
            if "user" in allowed_vfolder_types:
                user_type_vfolders: list[
                    VFolderItem
                ] = await self._query_accessible_user_type_vfolders(
                    db_session=sess, user_identity=user_identity, group_id=group_id
                )
                all_entries.extend(user_type_vfolders)

            if "group" in allowed_vfolder_types:
                group_type_vfolders: list[
                    VFolderItem
                ] = await self._query_accessible_group_type_vfolders(
                    db_session=sess, user_identity=user_identity, group_id=group_id
                )

                all_entries.extend(group_type_vfolders)

        return all_entries

    async def _query_accessible_user_type_vfolders(
        self, db_session: SASession, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> list[VFolderItem]:
        owned: list[VFolderItem] = await self._query_owned_vfolders(
            db_session=db_session, user_identity=user_identity, group_id=group_id
        )
        shared: list[VFolderItem] = await self._query_shared_vfolders(
            db_session=db_session, user_identity=user_identity
        )

        return [*owned, *shared]

    async def _query_accessible_group_type_vfolders(
        self, db_session: SASession, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> list[VFolderItem]:
        if group_id is not None:
            return await self._query_specific_group_vfolders(
                db_session=db_session, user_identity=user_identity, group_id=group_id
            )

        return await self._query_all_accessible_group_vfolders(
            db_session=db_session, user_identity=user_identity
        )

    async def _query_specific_group_vfolders(
        self,
        db_session: SASession,
        user_identity: UserIdentity,
        group_id: uuid.UUID,
    ) -> list[VFolderItem]:
        if user_identity.is_admin:
            # check if group belongs to admin's domain
            domain_check_query = (
                sa.select(GroupRow.id)
                .select_from(GroupRow)
                .where(
                    (GroupRow.id == group_id) & (GroupRow.domain_name == user_identity.domain_name)
                )
            )
            if await db_session.scalar(domain_check_query) is None:
                raise GroupNotFound(
                    extra_msg=f"group {group_id} does not belong to domain {user_identity.domain_name}"
                )

        if user_identity.is_normal_user:
            # check if user is in the group
            membership_query = (
                sa.select(AssocGroupUserRow.group_id)
                .select_from(AssocGroupUserRow)
                .where(
                    (AssocGroupUserRow.user_id == user_identity.user_uuid)
                    & (AssocGroupUserRow.group_id == group_id)
                )
            )
            if await db_session.scalar(membership_query) is None:
                raise GroupNotFound(
                    extra_msg=f"user {user_identity.user_uuid} is not a member of group {group_id}"
                )

        query = (
            sa.select(VFolderRow)
            .select_from(VFolderRow.join(GroupRow, VFolderRow.group == GroupRow.id))
            .where(
                (
                    (VFolderRow.group == group_id)
                    | (VFolderRow.user.isnot(None))
                    & VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
                )
            )
        )
        vfolders: list[VFolderRow] = (await db_session.scalars(query)).all()

        entries = [
            VFolderItem.from_orm(
                orm=vfolder,
                is_owner=user_identity.has_privilege_role,
                include_relations=True,
                override_with_group_member_permission=True,
            )
            for vfolder in vfolders
        ]

        return entries

    async def _query_all_accessible_group_vfolders(
        self,
        db_session: SASession,
        user_identity: UserIdentity,
    ) -> list[VFolderItem]:
        base_query = (
            sa.select(VFolderRow)
            .select_from(VFolderRow.join(GroupRow, VFolderRow.group == GroupRow.id))
            .where(VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]))
        )

        if user_identity.is_superadmin:
            query = base_query
        elif user_identity.is_admin:
            query = (
                sa.select(GroupRow.id)
                .select_from(GroupRow)
                .where(GroupRow.domain_name == user_identity.domain_name)
            )
            group_ids = await db_session.scalars(query)
            query = base_query.where(VFolderRow.group.in_(group_ids))
        else:
            query = (
                sa.select(AssocGroupUserRow.group_id)
                .select_from(
                    AssocGroupUserRow.join(UserRow, AssocGroupUserRow.user_id == UserRow.uuid)
                )
                .where(AssocGroupUserRow.user_id == user_identity.user_uuid)
            )
            group_ids = await db_session.scalars(query)
            query = base_query.where(VFolderRow.group.in_(group_ids))

        vfolders: list[VFolderRow] = (await db_session.scalars(query)).all()
        entries = [
            VFolderItem.from_orm(
                orm=vfolder, is_owner=user_identity.has_privilege_role, include_relations=True
            )
            for vfolder in vfolders
        ]

        return entries

    async def _query_owned_vfolders(
        self,
        db_session: SASession,
        user_identity: UserIdentity,
        group_id: Optional[uuid.UUID] = None,
    ) -> list[VFolderItem]:
        user_join = VFolderRow.join(UserRow, VFolderRow.user == UserRow.uuid)

        query = (
            sa.select(VFolderRow)
            .select_from(user_join)
            .where(VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]))
        )
        # If group id is provided, filter user owned vfolders that are in certain group
        if group_id is not None:
            query = query.where((VFolderRow.group == group_id) | (VFolderRow.user.isnot(None)))

        if user_identity.is_normal_user:
            query = query.where(VFolderRow.user == user_identity.user_uuid)

        vfolders: list[VFolderRow] = (await db_session.scalars(query)).all()
        entries = [
            VFolderItem.from_orm(orm=vfolder, is_owner=True, include_relations=True)
            for vfolder in vfolders
        ]

        return entries

    async def _query_shared_vfolders(
        self,
        db_session: SASession,
        user_identity: UserIdentity,
    ) -> list[VFolderItem]:
        shared_join = VFolderRow.join(
            VFolderPermissionRow,
            VFolderRow.id == VFolderPermissionRow.vfolder,
            isouter=True,
        ).join(
            UserRow,
            VFolderRow.user == UserRow.uuid,
            isouter=True,
        )

        query = (
            sa.select(VFolderRow)
            .select_from(shared_join)
            .where(
                (VFolderPermissionRow.user == user_identity.user_uuid)
                & (VFolderRow.ownership_type == VFolderOwnershipType.USER)
                & (VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]))
            )
        )

        vfolders: list[VFolderRow] = (await db_session.scalars(query)).all()
        entries = [
            VFolderItem.from_orm(orm=vfolder, is_owner=False, include_relations=True)
            for vfolder in vfolders
        ]

        return entries

    async def patch_vFolder_name(self, vfolder_id: uuid.UUID, new_name: str) -> None:
        async with self._db.begin_session() as sess:
            stmt = sa.update(VFolderRow).where(VFolderRow.id == vfolder_id).values(name=new_name)
            await sess.execute(stmt)

    async def _delete_vfolder_permission_rows(
        self,
        db_session: SASession,
        vfolder_row_ids: Iterable[uuid.UUID],
    ) -> None:
        stmt = sa.delete(VFolderInvitationRow).where(
            VFolderInvitationRow.vfolder.in_(vfolder_row_ids)
        )
        await db_session.execute(stmt)

    async def _delete_vfolder_invitation_rows(
        self,
        db_session: SASession,
        vfolder_row_ids: Iterable[uuid.UUID],
    ) -> None:
        stmt = sa.delete(VFolderPermissionRow).where(
            VFolderPermissionRow.vfolder.in_(vfolder_row_ids)
        )
        await db_session.execute(stmt)

    async def _delete_vfolder_relation_rows(
        self,
        db_session: SASession,
        vfolder_row_ids: Iterable[uuid.UUID],
    ) -> None:
        await self._delete_vfolder_invitation_rows(
            db_session=db_session, vfolder_row_ids=vfolder_row_ids
        )
        await self._delete_vfolder_permission_rows(
            db_session=db_session, vfolder_row_ids=vfolder_row_ids
        )

    async def _update_vfolder_status(
        self,
        db_session: SASession,
        vfolder_id: uuid.UUID,
        vfolder_status: VFolderOperationStatus,
    ) -> None:
        stmt = sa.update(VFolderRow).where(VFolderRow.id == vfolder_id).value(status=vfolder_status)
        await db_session.execute(stmt)

    """
    NOTICE: _retry method must be used in top level function
    """

    async def _retry(
        self,
        func: Callable[[SASession], Awaitable[_TQueryResult]],
    ) -> None:
        await execute_with_txn_retry(
            txn_func=func, begin_trx=self._db.begin_session, connection=self._db.connect()
        )

    async def delete_vFolder_by_id(
        self,
        vfolder_id: uuid.UUID,
    ) -> None:
        vfolder_ids = [vfolder_id]

        async def _delete_and_update(db_session: SASession) -> None:
            await self._delete_vfolder_relation_rows(
                db_session=db_session, vfolder_row_ids=vfolder_ids
            )
            await self._update_vfolder_status(
                db_session=db_session,
                vfolder_id=vfolder_id,
                vfolder_status=VFolderOperationStatus.DELETE_PENDING,
            )

        await self._retry(func=_delete_and_update)
