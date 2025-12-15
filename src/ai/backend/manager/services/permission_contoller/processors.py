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
    RevokeRoleAction,
    RevokeRoleActionResult,
    SearchRolesAction,
    SearchRolesActionResult,
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
    UpdateRoleAction,
    UpdateRoleActionResult,
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

    def __init__(
        self, service: PermissionControllerService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_role = ActionProcessor(service.create_role, action_monitors)
        self.update_role = ActionProcessor(service.update_role, action_monitors)
        self.delete_role = ActionProcessor(service.delete_role, action_monitors)
        self.assign_role = ActionProcessor(service.assign_role, action_monitors)
        self.revoke_role = ActionProcessor(service.revoke_role, action_monitors)
        self.get_role_detail = ActionProcessor(service.get_role_detail, action_monitors)
        self.search_roles = ActionProcessor(service.search_roles, action_monitors)
        self.search_users_assigned_to_role = ActionProcessor(
            service.search_users_assigned_to_role, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRoleAction.spec(),
            UpdateRoleAction.spec(),
            DeleteRoleAction.spec(),
            AssignRoleAction.spec(),
            RevokeRoleAction.spec(),
            GetRoleDetailAction.spec(),
            SearchRolesAction.spec(),
            SearchUsersAssignedToRoleAction.spec(),
        ]
