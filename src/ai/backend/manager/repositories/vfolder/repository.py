# import logging
# import uuid
# from dataclasses import dataclass
# from typing import Any, Mapping, Optional, Sequence, cast

# import sqlalchemy as sa
# from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
# from sqlalchemy.orm import selectinload

# # TODO: api.exceptions should not be imported here
# from ai.backend.common.defs import VFOLDER_GROUP_PERMISSION_MODE
# from ai.backend.common.exception import InvalidAPIParameters
# from ai.backend.common.types import (
#     QuotaScopeID,
#     QuotaScopeType,
#     VFolderHostPermission,
#     VFolderHostPermissionMap,
#     VFolderID,
# )
# from ai.backend.logging.utils import BraceStyleAdapter
# from ai.backend.manager.api.exceptions import (
#     GenericForbidden,
#     GroupNotFound,
#     VFolderAlreadyExists,
#     VFolderCreationFailed,
#     VFolderNotFound,
# )
# from ai.backend.manager.models.domain import domains
# from ai.backend.manager.models.group import GroupRow, ProjectType, association_groups_users, groups
# from ai.backend.manager.models.storage import StorageSessionManager
# from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# from ai.backend.manager.models.vfolder import (
#     HARD_DELETED_VFOLDER_STATUSES,
#     VFolderOperationStatus,
#     VFolderOwnershipType,
#     VFolderPermission,
#     VFolderPermissionSetAlias,
#     VFolderStatusSet,
#     vfolder_permissions,
#     vfolder_status_map,
#     vfolders,
# )

# log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# # TODO: Should use dataclass instead of Mapping
# type VFolderInfoMap = Mapping[str, Any]


# @dataclass
# class UserInfo:
#     uuid: uuid.UUID
#     role: UserRole
#     domain_name: str
#     is_admin: bool


class VFolderRepository:
    _db: ExtendedAsyncSAEngine


#     def __init__(self, db: ExtendedAsyncSAEngine):
#         self._db = db

#     async def get_vfolder_info(
#         self,
#         group_id_or_name: str | uuid.UUID | None,
#         user_info: UserInfo,
#         allowed_vfolder_types: Sequence[str],
#     ):
#         async with self._db.begin_session() as sess:
#             match group_id_or_name:
#                 case str():
#                     # Convert the group name to group uuid.
#                     log.debug("group_id_or_name(str):{}", group_id_or_name)
#                     query = (
#                         sa.select(GroupRow)
#                         .where(
#                             sa.and_(
#                                 GroupRow.domain_name == user_info.domain_name,
#                                 GroupRow.name == group_id_or_name,
#                             )
#                         )
#                         .options(selectinload(GroupRow.resource_policy_row))
#                     )
#                     result = await sess.execute(query)
#                     group_row = cast(GroupRow | None, result.scalar())
#                     if group_row is None:
#                         raise GroupNotFound(extra_data=group_id_or_name)
#                     _gid, max_vfolder_count, max_quota_scope_size = (
#                         cast(uuid.UUID | None, group_row.id),
#                         cast(int, group_row.resource_policy_row.max_vfolder_count),
#                         cast(int, group_row.resource_policy_row.max_quota_scope_size),
#                     )
#                     if _gid is None:
#                         raise GroupNotFound(extra_data=group_id_or_name)
#                     group_uuid = _gid
#                     group_type = cast(ProjectType, group_row.type)
#                 case uuid.UUID():
#                     # Check if the group belongs to the current domain.
#                     log.debug("group_id_or_name(uuid):{}", group_id_or_name)
#                     query = (
#                         sa.select(GroupRow)
#                         .where(
#                             (GroupRow.domain_name == user_info.domain_name)
#                             & (GroupRow.id == group_id_or_name)
#                         )
#                         .options(selectinload(GroupRow.resource_policy_row))
#                     )
#                     result = await sess.execute(query)
#                     group_row = cast(GroupRow | None, result.scalar())
#                     if group_row is None:
#                         raise GroupNotFound(extra_data=group_id_or_name)
#                     _gid, max_vfolder_count, max_quota_scope_size = (
#                         group_row.id,
#                         cast(int, group_row.resource_policy_row.max_vfolder_count),
#                         cast(int, group_row.resource_policy_row.max_quota_scope_size),
#                     )
#                     if _gid is None:
#                         raise GroupNotFound(extra_data=group_id_or_name)
#                     group_uuid = group_id_or_name
#                     group_type = cast(ProjectType, group_row.type)
#                 case None:
#                     query = (
#                         sa.select(UserRow)
#                         .where(UserRow.uuid == user_info.uuid)
#                         .options(selectinload(UserRow.resource_policy_row))
#                     )
#                     result = await sess.execute(query)
#                     user_row = result.scalar()
#                     max_vfolder_count, max_quota_scope_size = (
#                         cast(int, user_row.resource_policy_row.max_vfolder_count),
#                         cast(int, user_row.resource_policy_row.max_quota_scope_size),
#                     )
#                     container_uid = cast(Optional[int], user_row.container_uid)
#                 case _:
#                     raise GroupNotFound(extra_data=group_id_or_name)

#             vfolder_permission_mode = (
#                 VFOLDER_GROUP_PERMISSION_MODE if container_uid is not None else None
#             )

#             # Check if group exists when it's given a non-empty value.
#             if group_id_or_name and group_uuid is None:
#                 raise GroupNotFound(extra_data=group_id_or_name)

#             # Determine the ownership type and the quota scope ID.
#             if group_uuid is not None:
#                 ownership_type = "group"
#                 quota_scope_id = QuotaScopeID(QuotaScopeType.PROJECT, group_uuid)
#                 if not user_info.is_admin and group_type != ProjectType.MODEL_STORE:
#                     raise GenericForbidden("no permission")
#             else:
#                 ownership_type = "user"
#                 quota_scope_id = QuotaScopeID(QuotaScopeType.USER, user_info.uuid)
#             if ownership_type not in allowed_vfolder_types:
#                 raise InvalidAPIParameters(
#                     f"{ownership_type}-owned vfolder is not allowed in this cluster"
#                 )

#     # async def create_vfolder_if_not_exists(
#     #     self,
#     #     vfolder_name: str,
#     #     allowed_vfolder_types: Sequence[str],
#     #     folder_host: str,
#     #     user_uuid: uuid.UUID,
#     #     user_role: UserRole,
#     #     domain_name: str,
#     #     group_uuid: Optional[uuid.UUID],
#     #     max_vfolder_count: int,
#     #     max_quota_scope_size: int,
#     #     keypair_resource_policy: Mapping[str, Any],
#     #     quota_scope_id: QuotaScopeID,
#     #     vfolder_permission_mode: Optional[str],
#     #     ownership_type: str,
#     #     unmanaged_path: Optional[str],
#     # ) -> None:
#     #     async with self._db.begin() as conn:
#     #         await self._ensure_host_permission_allowed(
#     #             conn,
#     #             folder_host,
#     #             allowed_vfolder_types=allowed_vfolder_types,
#     #             user_uuid=user_uuid,
#     #             resource_policy=keypair_resource_policy,
#     #             domain_name=domain_name,
#     #             group_id=group_uuid,
#     #             permission=VFolderHostPermission.CREATE,
#     #         )

#     #         # Check resource policy's max_vfolder_count
#     #         if max_vfolder_count > 0:
#     #             if ownership_type == "user":
#     #                 query = (
#     #                     sa.select([sa.func.count()])
#     #                     .select_from(vfolders)
#     #                     .where(
#     #                         sa.and_(
#     #                             vfolders.c.user == user_uuid,
#     #                             vfolders.c.status.not_in(HARD_DELETED_VFOLDER_STATUSES),
#     #                         )
#     #                     )
#     #                 )
#     #             else:
#     #                 assert group_uuid is not None
#     #                 query = (
#     #                     sa.select([sa.func.count()])
#     #                     .select_from(vfolders)
#     #                     .where(
#     #                         (vfolders.c.group == group_uuid)
#     #                         & (vfolders.c.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
#     #                     )
#     #                 )
#     #             result = cast(int, await conn.scalar(query))
#     #             if result >= max_vfolder_count:
#     #                 raise InvalidAPIParameters("You cannot create more vfolders.")

#     #         # DEPRECATED: Limit vfolder size quota if it is larger than max_vfolder_size of the resource policy.
#     #         # max_vfolder_size = resource_policy.get("max_vfolder_size", 0)
#     #         # if max_vfolder_size > 0 and (
#     #         #     params["quota"] is None or params["quota"] <= 0 or params["quota"] > max_vfolder_size
#     #         # ):
#     #         #     params["quota"] = max_vfolder_size

#     #         # Prevent creation of vfolder with duplicated name on all hosts.
#     #         extra_vf_conds = [
#     #             (vfolders.c.name == vfolder_name),
#     #             (vfolders.c.status.not_in(HARD_DELETED_VFOLDER_STATUSES)),
#     #         ]
#     #         entries = await self._query_accessible_vfolders(
#     #             conn,
#     #             user_uuid,
#     #             user_role=user_role,
#     #             domain_name=domain_name,
#     #             allowed_vfolder_types=allowed_vfolder_types,
#     #             extra_vf_conds=(sa.and_(*extra_vf_conds)),
#     #         )
#     #         if len(entries) > 0:
#     #             raise VFolderAlreadyExists(extra_data=vfolder_name)
#     #         try:
#     #             folder_id = uuid.uuid4()
#     #             vfid = VFolderID(quota_scope_id, folder_id)
#     #             if not unmanaged_path:
#     #                 # Create the vfolder only when it is a managed one
#     #                 # TODO: Create the quota scope with an unlimited quota config if not exists
#     #                 #       The quota may be set later by the admin...
#     #                 # TODO: Introduce "default quota config" for users and projects (which cannot be
#     #                 #       modified by users)
#     #                 # async with root_ctx.storage_manager.request(
#     #                 #     folder_host,
#     #                 #     "POST",
#     #                 #     "quota-scope",
#     #                 #     json={
#     #                 #         "volume": root_ctx.storage_manager.split_host(folder_host)[1],
#     #                 #         "qsid": str(quota_scope_id),
#     #                 #         "options": None,
#     #                 #     },
#     #                 # ):
#     #                 #     pass
#     #                 options = {}
#     #                 if max_quota_scope_size and max_quota_scope_size > 0:
#     #                     options["initial_max_size_for_quota_scope"] = max_quota_scope_size
#     #                 body_data: dict[str, Any] = {
#     #                     "volume": root_ctx.storage_manager.get_proxy_and_volume(
#     #                         folder_host, is_unmanaged(unmanaged_path)
#     #                     )[1],
#     #                     "vfid": str(vfid),
#     #                     "options": options,
#     #                 }
#     #                 if vfolder_permission_mode is not None:
#     #                     body_data["mode"] = vfolder_permission_mode
#     #                 async with root_ctx.storage_manager.request(
#     #                     folder_host,
#     #                     "POST",
#     #                     "folder/create",
#     #                     json=body_data,
#     #                 ):
#     #                     pass
#     #         except aiohttp.ClientResponseError as e:
#     #             raise VFolderCreationFailed from e

#     #         # By default model store VFolder should be considered as read only for every users but without the creator
#     #         if group_type == ProjectType.MODEL_STORE:
#     #             params.permission = VFolderPermission.READ_ONLY

#     #         # TODO: include quota scope ID in the database
#     #         # TODO: include quota scope ID in the API response
#     #         insert_values = {
#     #             "id": vfid.folder_id.hex,
#     #             "name": params.name,
#     #             "domain_name": domain_name,
#     #             "quota_scope_id": str(quota_scope_id),
#     #             "usage_mode": params.usage_mode,
#     #             "permission": params.permission,
#     #             "last_used": None,
#     #             "host": folder_host,
#     #             "creator": request["user"]["email"],
#     #             "ownership_type": VFolderOwnershipType(ownership_type),
#     #             "user": user_uuid if ownership_type == "user" else None,
#     #             "group": group_uuid if ownership_type == "group" else None,
#     #             "unmanaged_path": unmanaged_path,
#     #             "cloneable": params.cloneable,
#     #             "status": VFolderOperationStatus.READY,
#     #         }
#     #         resp = {
#     #             "id": vfid.folder_id.hex,
#     #             "name": params.name,
#     #             "quota_scope_id": str(quota_scope_id),
#     #             "host": folder_host,
#     #             "usage_mode": params.usage_mode.value,
#     #             "permission": params.permission.value,
#     #             "max_size": 0,  # migrated to quota scopes, no longer valid
#     #             "creator": request["user"]["email"],
#     #             "ownership_type": ownership_type,
#     #             "user": str(user_uuid) if ownership_type == "user" else None,
#     #             "group": str(group_uuid) if ownership_type == "group" else None,
#     #             "cloneable": params.cloneable,
#     #             "status": VFolderOperationStatus.READY,
#     #         }
#     #         if unmanaged_path:
#     #             resp["unmanaged_path"] = unmanaged_path
#     #         try:
#     #             query = sa.insert(vfolders, insert_values)
#     #             result = await conn.execute(query)

#     #             # Here we grant creator the permission to alter VFolder contents
#     #             if group_type == ProjectType.MODEL_STORE:
#     #                 query = sa.insert(vfolder_permissions).values({
#     #                     "user": request["user"]["uuid"],
#     #                     "vfolder": vfid.folder_id.hex,
#     #                     "permission": VFolderPermission.OWNER_PERM,
#     #                 })
#     #                 await conn.execute(query)
#     #         except sa.exc.DataError:
#     #             raise InvalidAPIParameters
#     #         assert result.rowcount == 1

#     async def resolve_vfolder_rows(
#         self,
#         user_info: UserInfo,
#         allowed_vfolder_types: Sequence[str],
#         perm: VFolderPermissionSetAlias | VFolderPermission | str,
#         folder_id_or_name: str | uuid.UUID,
#         *,
#         allowed_status_set: VFolderStatusSet | None = None,
#         allow_privileged_access: bool = False,
#     ) -> Sequence[VFolderInfoMap]:
#         """
#         Checks if the target VFolder exists and is either:
#         - owned by requester, or
#         - original owner (of target VFolder) has granted certain level of access to the requester

#         When requester passes VFolder name to `folder_id_or_name` parameter then there is a possibility for
#         this helper to return multiple entries of VFolder rows which are considered deleted,
#         since Backend.AI also is aware of both deleted and purged VFolders. Resolving VFolder row by ID
#         will not fall in such cases as it is guaranted by DB side that every VFolder ID is unique across whole table.
#         To avoid such behavior, either do not consider VFolder name as an index to resolve VFolder row or
#         pass every returned elements of this helper to a separate check_vfolder_status() call, so that
#         the handler can figure out which row is the actual row that is aware of.
#         """

#         vf_user_cond = None
#         vf_group_cond = None

#         # TODO: Use Options pattern
#         match perm:
#             case VFolderPermissionSetAlias():
#                 invited_perm_cond = vfolder_permissions.c.permission.in_(list(perm.value))
#                 if not user_info.is_admin:
#                     vf_group_cond = vfolders.c.permission.in_(list(perm.value))
#             case _:
#                 # Otherwise, just compare it as-is (for future compatibility).
#                 invited_perm_cond = vfolder_permissions.c.permission == perm
#                 if not user_info.is_admin:
#                     vf_group_cond = vfolders.c.permission == perm

#         match folder_id_or_name:
#             case str():
#                 extra_vf_conds = vfolders.c.name == folder_id_or_name
#             case uuid.UUID():
#                 extra_vf_conds = vfolders.c.id == folder_id_or_name
#             case _:
#                 raise RuntimeError(f"Unsupported VFolder index type {type(folder_id_or_name)}")

#         async with self._db.begin_readonly() as conn:
#             entries = await self._query_accessible_vfolders(
#                 conn,
#                 user_info.uuid,
#                 allow_privileged_access=allow_privileged_access,
#                 user_role=user_info.role,
#                 domain_name=user_info.domain_name,
#                 allowed_vfolder_types=allowed_vfolder_types,
#                 extra_vf_conds=extra_vf_conds,
#                 extra_invited_vf_conds=invited_perm_cond,
#                 extra_vf_user_conds=vf_user_cond,
#                 extra_vf_group_conds=vf_group_cond,
#                 allowed_status_set=allowed_status_set,
#             )
#             if len(entries) == 0:
#                 raise VFolderNotFound(extra_data=folder_id_or_name)
#             return entries

#     async def _query_accessible_vfolders(
#         self,
#         conn: SAConnection,
#         user_uuid: uuid.UUID,
#         *,
#         # when enabled, skip vfolder ownership check if user role is admin or superadmin
#         allow_privileged_access=False,
#         user_role=None,
#         domain_name: Optional[str] = None,
#         allowed_vfolder_types=None,
#         extra_vf_conds=None,
#         extra_invited_vf_conds=None,
#         extra_vf_user_conds=None,
#         extra_vf_group_conds=None,
#         allowed_status_set: VFolderStatusSet | None = None,
#     ) -> Sequence[Mapping[str, Any]]:
#         from ai.backend.manager.models import association_groups_users as agus
#         from ai.backend.manager.models import groups, users

#         if allowed_vfolder_types is None:
#             allowed_vfolder_types = ["user"]  # legacy default

#         vfolders_selectors = [
#             vfolders.c.name,
#             vfolders.c.id,
#             vfolders.c.host,
#             vfolders.c.quota_scope_id,
#             vfolders.c.usage_mode,
#             vfolders.c.created_at,
#             vfolders.c.last_used,
#             vfolders.c.max_files,
#             vfolders.c.max_size,
#             vfolders.c.ownership_type,
#             vfolders.c.user,
#             vfolders.c.group,
#             vfolders.c.creator,
#             vfolders.c.unmanaged_path,
#             vfolders.c.cloneable,
#             vfolders.c.status,
#             vfolders.c.cur_size,
#             # vfolders.c.permission,
#             # users.c.email,
#         ]

#         async def _append_entries(_query, _is_owner=True):
#             if extra_vf_conds is not None:
#                 _query = _query.where(extra_vf_conds)
#             if extra_vf_user_conds is not None:
#                 _query = _query.where(extra_vf_user_conds)
#             result = await conn.execute(_query)
#             for row in result:
#                 row_keys = row.keys()
#                 _perm = (
#                     row.vfolder_permissions_permission
#                     if "vfolder_permissions_permission" in row_keys
#                     else row.vfolders_permission
#                 )
#                 entries.append({
#                     "name": row.vfolders_name,
#                     "id": row.vfolders_id,
#                     "host": row.vfolders_host,
#                     "quota_scope_id": row.vfolders_quota_scope_id,
#                     "usage_mode": row.vfolders_usage_mode,
#                     "created_at": row.vfolders_created_at,
#                     "last_used": row.vfolders_last_used,
#                     "max_size": row.vfolders_max_size,
#                     "max_files": row.vfolders_max_files,
#                     "ownership_type": row.vfolders_ownership_type,
#                     "user": str(row.vfolders_user) if row.vfolders_user else None,
#                     "group": str(row.vfolders_group) if row.vfolders_group else None,
#                     "creator": row.vfolders_creator,
#                     "user_email": row.users_email if "users_email" in row_keys else None,
#                     "group_name": row.groups_name if "groups_name" in row_keys else None,
#                     "is_owner": _is_owner,
#                     "permission": _perm,
#                     "unmanaged_path": row.vfolders_unmanaged_path,
#                     "cloneable": row.vfolders_cloneable,
#                     "status": row.vfolders_status,
#                     "cur_size": row.vfolders_cur_size,
#                 })

#         entries: list[dict] = []
#         # User vfolders.
#         if "user" in allowed_vfolder_types:
#             # Scan vfolders on requester's behalf.
#             j = vfolders.join(users, vfolders.c.user == users.c.uuid)
#             query = sa.select(
#                 vfolders_selectors + [vfolders.c.permission, users.c.email], use_labels=True
#             ).select_from(j)
#             if allowed_status_set is not None:
#                 query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
#             else:
#                 query = query.where(
#                     vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
#                 )
#             if not allow_privileged_access or user_role not in (
#                 UserRole.ADMIN,
#                 UserRole.SUPERADMIN,
#             ):
#                 query = query.where(vfolders.c.user == user_uuid)
#             await _append_entries(query)

#             # Scan vfolders shared with requester.
#             j = vfolders.join(
#                 vfolder_permissions,
#                 vfolders.c.id == vfolder_permissions.c.vfolder,
#                 isouter=True,
#             ).join(
#                 users,
#                 vfolders.c.user == users.c.uuid,
#                 isouter=True,
#             )
#             query = (
#                 sa.select(
#                     vfolders_selectors + [vfolder_permissions.c.permission, users.c.email],
#                     use_labels=True,
#                 )
#                 .select_from(j)
#                 .where(
#                     (vfolder_permissions.c.user == user_uuid)
#                     & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
#                 )
#             )
#             if allowed_status_set is not None:
#                 query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
#             else:
#                 query = query.where(
#                     vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
#                 )
#             if extra_invited_vf_conds is not None:
#                 query = query.where(extra_invited_vf_conds)
#             await _append_entries(query, _is_owner=False)

#         if "group" in allowed_vfolder_types:
#             # Scan group vfolders.
#             if user_role == UserRole.ADMIN or user_role == "admin":
#                 query = (
#                     sa.select([groups.c.id])
#                     .select_from(groups)
#                     .where(groups.c.domain_name == domain_name)
#                 )
#                 result = await conn.execute(query)
#                 grps = result.fetchall()
#                 group_ids = [g.id for g in grps]
#             else:
#                 j = sa.join(agus, users, agus.c.user_id == users.c.uuid)
#                 query = (
#                     sa.select([agus.c.group_id]).select_from(j).where(agus.c.user_id == user_uuid)
#                 )
#                 result = await conn.execute(query)
#                 grps = result.fetchall()
#                 group_ids = [g.group_id for g in grps]
#             j = vfolders.join(groups, vfolders.c.group == groups.c.id)
#             query = sa.select(
#                 vfolders_selectors + [vfolders.c.permission, groups.c.name], use_labels=True
#             ).select_from(j)
#             if user_role != UserRole.SUPERADMIN and user_role != "superadmin":
#                 query = query.where(vfolders.c.group.in_(group_ids))
#             if extra_vf_group_conds is not None:
#                 query = query.where(extra_vf_group_conds)
#             is_owner = (user_role == UserRole.ADMIN or user_role == "admin") or (
#                 user_role == UserRole.SUPERADMIN or user_role == "superadmin"
#             )
#             await _append_entries(query, is_owner)

#             # Override permissions, if exists, for group vfolders.
#             j = sa.join(
#                 vfolders,
#                 vfolder_permissions,
#                 vfolders.c.id == vfolder_permissions.c.vfolder,
#             )
#             query = (
#                 sa.select(vfolder_permissions.c.permission, vfolder_permissions.c.vfolder)
#                 .select_from(j)
#                 .where(
#                     (vfolders.c.group.in_(group_ids)) & (vfolder_permissions.c.user == user_uuid)
#                 )
#             )
#             if allowed_status_set is not None:
#                 query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
#             else:
#                 query = query.where(
#                     vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
#                 )
#             if extra_vf_conds is not None:
#                 query = query.where(extra_vf_conds)
#             if extra_vf_user_conds is not None:
#                 query = query.where(extra_vf_user_conds)
#             result = await conn.execute(query)
#             overriding_permissions: dict = {row.vfolder: row.permission for row in result}
#             for entry in entries:
#                 if (
#                     entry["id"] in overriding_permissions
#                     and entry["ownership_type"] == VFolderOwnershipType.GROUP
#                 ):
#                     entry["permission"] = overriding_permissions[entry["id"]]

#         return entries

#     async def _ensure_host_permission_allowed(
#         self,
#         db_conn,
#         folder_host: str,
#         *,
#         permission: VFolderHostPermission,
#         allowed_vfolder_types: Sequence[str],
#         user_uuid: uuid.UUID,
#         resource_policy: Mapping[str, Any],
#         domain_name: str,
#         group_id: Optional[uuid.UUID] = None,
#     ) -> None:
#         if StorageSessionManager.is_noop_host(folder_host):
#             return
#         allowed_hosts = await self._filter_host_allowed_permission(
#             db_conn,
#             allowed_vfolder_types=allowed_vfolder_types,
#             user_uuid=user_uuid,
#             resource_policy=resource_policy,
#             domain_name=domain_name,
#             group_id=group_id,
#         )
#         if folder_host not in allowed_hosts or permission not in allowed_hosts[folder_host]:
#             raise InvalidAPIParameters(
#                 f"`{permission}` Not allowed in vfolder host(`{folder_host}`)"
#             )

#     async def _filter_host_allowed_permission(
#         self,
#         db_conn,
#         *,
#         allowed_vfolder_types: Sequence[str],
#         user_uuid: uuid.UUID,
#         resource_policy: Mapping[str, Any],
#         domain_name: str,
#         group_id: Optional[uuid.UUID] = None,
#     ) -> VFolderHostPermissionMap:
#         allowed_hosts = VFolderHostPermissionMap()
#         if "user" in allowed_vfolder_types:
#             allowed_hosts_by_user = await self._get_allowed_vfolder_hosts_by_user(
#                 db_conn, resource_policy, domain_name, user_uuid
#             )
#             allowed_hosts = allowed_hosts | allowed_hosts_by_user
#         if "group" in allowed_vfolder_types and group_id is not None:
#             allowed_hosts_by_group = await self._get_allowed_vfolder_hosts_by_group(
#                 db_conn, resource_policy, domain_name, group_id
#             )
#             allowed_hosts = allowed_hosts | allowed_hosts_by_group
#         return allowed_hosts

#     async def _get_allowed_vfolder_hosts_by_group(
#         conn: SAConnection,
#         resource_policy,
#         domain_name: str,
#         group_id: Optional[uuid.UUID] = None,
#         domain_admin: bool = False,
#     ) -> VFolderHostPermissionMap:
#         """
#         Union `allowed_vfolder_hosts` from domain, group, and keypair_resource_policy.

#         If `group_id` is not None, `allowed_vfolder_hosts` from the group is also merged.
#         If the requester is a domain admin, gather all `allowed_vfolder_hosts` of the domain groups.
#         """

#         # Domain's allowed_vfolder_hosts.
#         allowed_hosts = VFolderHostPermissionMap()
#         query = sa.select([domains.c.allowed_vfolder_hosts]).where(
#             (domains.c.name == domain_name) & (domains.c.is_active),
#         )
#         if values := await conn.scalar(query):
#             allowed_hosts = allowed_hosts | values
#         # Group's allowed_vfolder_hosts.
#         if group_id is not None:
#             query = sa.select([groups.c.allowed_vfolder_hosts]).where(
#                 (groups.c.domain_name == domain_name)
#                 & (groups.c.id == group_id)
#                 & (groups.c.is_active),
#             )
#             if values := await conn.scalar(query):
#                 allowed_hosts = allowed_hosts | values
#         elif domain_admin:
#             query = sa.select([groups.c.allowed_vfolder_hosts]).where(
#                 (groups.c.domain_name == domain_name) & (groups.c.is_active),
#             )
#             if rows := (await conn.execute(query)).fetchall():
#                 for row in rows:
#                     allowed_hosts = allowed_hosts | row.allowed_vfolder_hosts
#         # Keypair Resource Policy's allowed_vfolder_hosts
#         allowed_hosts = allowed_hosts | resource_policy["allowed_vfolder_hosts"]
#         return allowed_hosts

#     async def _get_allowed_vfolder_hosts_by_user(
#         conn: SAConnection,
#         resource_policy: Mapping[str, Any],
#         domain_name: str,
#         user_uuid: uuid.UUID,
#         group_id: Optional[uuid.UUID] = None,
#     ) -> VFolderHostPermissionMap:
#         """
#         Union `allowed_vfolder_hosts` from domain, groups, and keypair_resource_policy.

#         All available `allowed_vfolder_hosts` of groups which requester associated will be merged.
#         """

#         # Domain's allowed_vfolder_hosts.
#         allowed_hosts = VFolderHostPermissionMap()
#         query = sa.select([domains.c.allowed_vfolder_hosts]).where(
#             (domains.c.name == domain_name) & (domains.c.is_active),
#         )
#         if values := await conn.scalar(query):
#             allowed_hosts = allowed_hosts | values
#         # User's Groups' allowed_vfolder_hosts.
#         if group_id is not None:
#             j = groups.join(
#                 association_groups_users,
#                 (
#                     (groups.c.id == association_groups_users.c.group_id)
#                     & (groups.c.id == group_id)
#                     & (association_groups_users.c.user_id == user_uuid)
#                 ),
#             )
#         else:
#             j = groups.join(
#                 association_groups_users,
#                 (
#                     (groups.c.id == association_groups_users.c.group_id)
#                     & (association_groups_users.c.user_id == user_uuid)
#                 ),
#             )
#         query = (
#             sa.select([groups.c.allowed_vfolder_hosts])
#             .select_from(j)
#             .where(
#                 (groups.c.domain_name == domain_name) & (groups.c.is_active),
#             )
#         )
#         if rows := (await conn.execute(query)).fetchall():
#             for row in rows:
#                 allowed_hosts = allowed_hosts | row.allowed_vfolder_hosts
#         # Keypair Resource Policy's allowed_vfolder_hosts
#         allowed_hosts = allowed_hosts | resource_policy["allowed_vfolder_hosts"]
#         return allowed_hosts
