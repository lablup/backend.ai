from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import AssignedUserData, RoleData
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    EntityScopeConditions,
    RoleConditions,
    ScopedPermissionConditions,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)


async def load_roles_by_ids(
    processor: PermissionControllerProcessors,
    role_ids: Sequence[uuid.UUID],
) -> list[RoleData | None]:
    if not role_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[RoleConditions.by_ids(role_ids)],
    )

    action_result = await processor.search_roles.wait_for_complete(
        SearchRolesAction(querier=querier)
    )

    role_map = {role.id: role for role in action_result.result.items}
    return [role_map.get(role_id) for role_id in role_ids]


async def load_permissions_by_ids(
    processor: PermissionControllerProcessors,
    permission_ids: Sequence[uuid.UUID],
) -> list[PermissionData | None]:
    if not permission_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[ScopedPermissionConditions.by_ids(permission_ids)],
    )

    action_result = await processor.search_permissions.wait_for_complete(
        SearchPermissionsAction(querier=querier)
    )

    permission_map = {p.id: p for p in action_result.result.items}
    return [permission_map.get(pid) for pid in permission_ids]


async def load_role_assignments_by_ids(
    processor: PermissionControllerProcessors,
    assignment_ids: Sequence[uuid.UUID],
) -> list[AssignedUserData | None]:
    if not assignment_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[AssignedUserConditions.by_ids(assignment_ids)],
    )

    action_result = await processor.search_users_assigned_to_role.wait_for_complete(
        SearchUsersAssignedToRoleAction(querier=querier)
    )

    assignment_map = {a.id: a for a in action_result.result.items}
    return [assignment_map.get(aid) for aid in assignment_ids]


async def load_role_assignments_by_role_and_user_ids(
    processor: PermissionControllerProcessors,
    keys: Sequence[tuple[uuid.UUID, uuid.UUID]],
) -> list[AssignedUserData | None]:
    if not keys:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[AssignedUserConditions.by_role_and_user_ids(keys)],
    )

    action_result = await processor.search_users_assigned_to_role.wait_for_complete(
        SearchUsersAssignedToRoleAction(querier=querier)
    )

    assignment_map = {(a.role_id, a.user_id): a for a in action_result.result.items}
    return [assignment_map.get(key) for key in keys]


async def load_entities_by_type_and_ids(
    processor: PermissionControllerProcessors,
    keys: Sequence[tuple[EntityType, str]],
) -> list[EntityData | None]:
    if not keys:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[EntityScopeConditions.by_entity_type_and_ids(keys)],
    )

    action_result = await processor.search_entities.wait_for_complete(
        SearchEntitiesAction(querier=querier)
    )

    entity_map = {(e.entity_type, e.entity_id): e for e in action_result.result.items}
    return [entity_map.get(key) for key in keys]
