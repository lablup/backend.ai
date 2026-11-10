from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.types import VFolderHostPermission, VFolderHostPermissionMap
from ai.backend.manager.defs import is_noop_host
from ai.backend.manager.errors.storage import InsufficientStoragePermission
from ai.backend.manager.models.domain.row import domains
from ai.backend.manager.models.project.row import groups
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists


async def get_allowed_vfolder_hosts_by_group(
    conn: SAConnection,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    group_id: uuid.UUID | None = None,
) -> VFolderHostPermissionMap:
    """
    Union `allowed_vfolder_hosts` from domain, group, and keypair_resource_policy.

    If `group_id` is not None, `allowed_vfolder_hosts` from the group is also merged.
    If the requester is a domain admin, gather all `allowed_vfolder_hosts` of the domain groups.
    """
    # Domain's allowed_vfolder_hosts.
    allowed_hosts = VFolderHostPermissionMap()
    query = sa.select(domains.c.allowed_vfolder_hosts).where(
        (domains.c.name == domain_name) & (domains.c.is_active),
    )
    if values := await conn.scalar(query):
        result_hosts: VFolderHostPermissionMap = allowed_hosts | values
        allowed_hosts = result_hosts
    # Group's allowed_vfolder_hosts.
    if group_id is not None:
        query = sa.select(groups.c.allowed_vfolder_hosts).where(
            (groups.c.domain_name == domain_name)
            & (groups.c.id == group_id)
            & (groups.c.is_active),
        )
        if values := await conn.scalar(query):
            result_hosts = allowed_hosts | values
            allowed_hosts = result_hosts
    # Keypair Resource Policy's allowed_vfolder_hosts
    final_result: VFolderHostPermissionMap = allowed_hosts | resource_policy.get(
        "allowed_vfolder_hosts", VFolderHostPermissionMap()
    )
    return final_result


async def get_allowed_vfolder_hosts_by_user(
    conn: SAConnection,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    user_uuid: uuid.UUID,
    group_id: uuid.UUID | None = None,
) -> VFolderHostPermissionMap:
    """
    Union `allowed_vfolder_hosts` from domain, groups, and keypair_resource_policy.

    All available `allowed_vfolder_hosts` of groups which requester associated will be merged.
    """
    # Domain's allowed_vfolder_hosts.
    allowed_hosts = VFolderHostPermissionMap()
    query = sa.select(domains.c.allowed_vfolder_hosts).where(
        (domains.c.name == domain_name) & (domains.c.is_active),
    )
    if values := await conn.scalar(query):
        result_hosts: VFolderHostPermissionMap = allowed_hosts | values
        allowed_hosts = result_hosts
    # User's Groups' allowed_vfolder_hosts.
    membership_cond: sa.ColumnElement[bool] = user_scope_membership_exists(
        ProjectEntityType(), groups.c.id, user_uuid
    )
    if group_id is not None:
        membership_cond = sa.and_(membership_cond, groups.c.id == group_id)
    query = sa.select(groups.c.allowed_vfolder_hosts).where(
        membership_cond, groups.c.domain_name == domain_name, groups.c.is_active
    )
    if rows := (await conn.execute(query)).fetchall():
        for row in rows:
            result_hosts = allowed_hosts | row.allowed_vfolder_hosts
            allowed_hosts = result_hosts
    # Keypair Resource Policy's allowed_vfolder_hosts
    final_result: VFolderHostPermissionMap = allowed_hosts | resource_policy.get(
        "allowed_vfolder_hosts", VFolderHostPermissionMap()
    )
    return final_result


async def ensure_host_permission_allowed(
    db_conn: SAConnection,
    folder_host: str,
    *,
    permission: VFolderHostPermission,
    allowed_vfolder_types: Sequence[str],
    user_uuid: uuid.UUID,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    group_id: uuid.UUID | None = None,
) -> None:
    if is_noop_host(folder_host):
        return
    allowed_hosts = VFolderHostPermissionMap()
    if "user" in allowed_vfolder_types:
        allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
            db_conn, resource_policy, domain_name, user_uuid, group_id
        )
        allowed_hosts = VFolderHostPermissionMap(allowed_hosts | allowed_hosts_by_user)
    if "group" in allowed_vfolder_types and group_id is not None:
        allowed_hosts_by_group = await get_allowed_vfolder_hosts_by_group(
            db_conn, resource_policy, domain_name, group_id
        )
        allowed_hosts = VFolderHostPermissionMap(allowed_hosts | allowed_hosts_by_group)
    if folder_host not in allowed_hosts or permission not in allowed_hosts[folder_host]:
        raise InsufficientStoragePermission(
            f"`{permission}` Not allowed in vfolder host(`{folder_host}`)"
        )
