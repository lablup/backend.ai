from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    AssignRoleAction,
    AssignRoleActionResult,
    CreateRoleAction,
    CreateRoleActionResult,
    DeleteRoleAction,
    DeleteRoleActionResult,
    GetRoleDetailAction,
    GetRoleDetailActionResult,
    PurgeRoleAction,
    RevokeRoleAction,
    RevokeRoleActionResult,
    SearchObjectPermissionsAction,
    SearchObjectPermissionsActionResult,
    SearchPermissionGroupsAction,
    SearchPermissionGroupsActionResult,
    SearchRolesAction,
    SearchRolesActionResult,
    SearchScopedPermissionsAction,
    SearchScopedPermissionsActionResult,
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
    UpdateRoleAction,
    UpdateRoleActionResult,
    UpdateRolePermissionsAction,
    UpdateRolePermissionsActionResult,
)
from .actions.get_entity_types import (
    GetEntityTypesAction,
    GetEntityTypesActionResult,
)
from .actions.get_scope_types import (
    GetScopeTypesAction,
    GetScopeTypesActionResult,
)
from .actions.search_entities import (
    SearchEntitiesAction,
    SearchEntitiesActionResult,
)
from .actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from .service import PermissionControllerService


class PermissionControllerProcessors(AbstractProcessorPackage):
    """Processor package for RBAC permission controller operations."""

    create_role: ActionProcessor[CreateRoleAction, CreateRoleActionResult]
    update_role: ActionProcessor[UpdateRoleAction, UpdateRoleActionResult]
    delete_role: ActionProcessor[DeleteRoleAction, DeleteRoleActionResult]
    assign_role: ActionProcessor[AssignRoleAction, AssignRoleActionResult]
    revoke_role: ActionProcessor[RevokeRoleAction, RevokeRoleActionResult]
    get_role_detail: ActionProcessor[GetRoleDetailAction, GetRoleDetailActionResult]
    search_roles: ActionProcessor[SearchRolesAction, SearchRolesActionResult]
    search_users_assigned_to_role: ActionProcessor[
        SearchUsersAssignedToRoleAction, SearchUsersAssignedToRoleActionResult
    ]
    update_role_permissions: ActionProcessor[
        UpdateRolePermissionsAction, UpdateRolePermissionsActionResult
    ]
    search_scopes: ActionProcessor[SearchScopesAction, SearchScopesActionResult]
    get_scope_types: ActionProcessor[GetScopeTypesAction, GetScopeTypesActionResult]
    get_entity_types: ActionProcessor[GetEntityTypesAction, GetEntityTypesActionResult]
    search_entities: ActionProcessor[SearchEntitiesAction, SearchEntitiesActionResult]
    search_scoped_permissions: ActionProcessor[
        SearchScopedPermissionsAction, SearchScopedPermissionsActionResult
    ]
    search_object_permissions: ActionProcessor[
        SearchObjectPermissionsAction, SearchObjectPermissionsActionResult
    ]
    search_permission_groups: ActionProcessor[
        SearchPermissionGroupsAction, SearchPermissionGroupsActionResult
    ]

    def __init__(
        self, service: PermissionControllerService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_role = ActionProcessor(service.create_role, action_monitors)
        self.update_role = ActionProcessor(service.update_role, action_monitors)
        self.delete_role = ActionProcessor(service.delete_role, action_monitors)
        self.purge_role = ActionProcessor(service.purge_role, action_monitors)
        self.assign_role = ActionProcessor(service.assign_role, action_monitors)
        self.revoke_role = ActionProcessor(service.revoke_role, action_monitors)
        self.get_role_detail = ActionProcessor(service.get_role_detail, action_monitors)
        self.search_roles = ActionProcessor(service.search_roles, action_monitors)
        self.search_users_assigned_to_role = ActionProcessor(
            service.search_users_assigned_to_role, action_monitors
        )
        self.update_role_permissions = ActionProcessor(
            service.update_role_permissions, action_monitors
        )
        self.search_scopes = ActionProcessor(service.search_scopes, action_monitors)
        self.get_scope_types = ActionProcessor(service.get_scope_types, action_monitors)
        self.get_entity_types = ActionProcessor(service.get_entity_types, action_monitors)
        self.search_entities = ActionProcessor(service.search_entities, action_monitors)
        self.search_scoped_permissions = ActionProcessor(
            service.search_scoped_permissions, action_monitors
        )
        self.search_object_permissions = ActionProcessor(
            service.search_object_permissions, action_monitors
        )
        self.search_permission_groups = ActionProcessor(
            service.search_permission_groups, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRoleAction.spec(),
            UpdateRoleAction.spec(),
            DeleteRoleAction.spec(),
            PurgeRoleAction.spec(),
            AssignRoleAction.spec(),
            RevokeRoleAction.spec(),
            GetRoleDetailAction.spec(),
            SearchRolesAction.spec(),
            SearchUsersAssignedToRoleAction.spec(),
            UpdateRolePermissionsAction.spec(),
            SearchScopesAction.spec(),
            GetScopeTypesAction.spec(),
            GetEntityTypesAction.spec(),
            SearchEntitiesAction.spec(),
            SearchScopedPermissionsAction.spec(),
            SearchObjectPermissionsAction.spec(),
            SearchPermissionGroupsAction.spec(),
        ]
