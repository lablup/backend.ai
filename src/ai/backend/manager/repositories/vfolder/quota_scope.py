from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.types import QuotaScopeID
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.user.row import UserRole, UserRow
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists


async def ensure_quota_scope_accessible_by_user(
    conn: SASession,
    quota_scope: QuotaScopeID,
    user: Mapping[str, Any],
) -> None:
    # Lookup user table to match if quota is scoped to the user
    user_query = sa.select(UserRow).where(UserRow.uuid == quota_scope.scope_id)
    quota_scope_user: UserRow | None = await conn.scalar(user_query)
    if quota_scope_user:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_user.domain_name == user["domain_name"]:
                    return
            case _:
                if quota_scope_user.uuid == user["uuid"]:
                    return
        raise InvalidAPIParameters

    # Lookup group table to match if quota is scoped to the group
    group_query = sa.select(ProjectRow).where(ProjectRow.id == quota_scope.scope_id)
    quota_scope_group: ProjectRow | None = await conn.scalar(group_query)
    if quota_scope_group:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_group.domain_name == user["domain_name"]:
                    return
            case _:
                membership_query = sa.select(
                    user_scope_membership_exists(
                        ProjectEntityType(), quota_scope_group.id, user["uuid"]
                    )
                )
                if await conn.scalar(membership_query):
                    return

    raise InvalidAPIParameters
