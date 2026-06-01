from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

from .actions import (
    AssignRoleAction,
    AssignRoleActionResult,
    BulkAddRolePermissionsAction,
    BulkAddRolePermissionsActionResult,
    BulkAssignRoleAction,
    BulkAssignRoleActionResult,
    BulkRemoveRolePermissionsAction,
    BulkRemoveRolePermissionsActionResult,
    BulkRevokeRoleAction,
    BulkRevokeRoleActionResult,
    CreateRoleAction,
    CreateRoleActionResult,
    DeleteRoleAction,
    DeleteRoleActionResult,
    EnsureSystemRoleAction,
    EnsureSystemRoleActionResult,
    GetRoleDetailAction,
    GetRoleDetailActionResult,
    PurgeRoleAction,
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
    RevokeRoleAction,
    RevokeRoleActionResult,
    SearchRolesAction,
    SearchRolesActionResult,
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
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
from .actions.get_permission_matrix import (
    GetPermissionMatrixAction,
    GetPermissionMatrixActionResult,
)
from .actions.get_scope_types import (
    GetScopeTypesAction,
    GetScopeTypesActionResult,
)
from .actions.permission import (
    CreatePermissionAction,
    CreatePermissionActionResult,
    DeletePermissionAction,
    DeletePermissionActionResult,
)
from .actions.search_element_associations import (
    SearchElementAssociationsAction,
    SearchElementAssociationsActionResult,
)
from .actions.search_entities import (
    SearchEntitiesAction,
    SearchEntitiesActionResult,
)
from .actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from .actions.search_role_invitations import (
    AcceptRoleInvitationAction as AcceptInvitationAction,
)
from .actions.search_role_invitations import (
    AdminSearchRoleInvitationsAction,
    AdminSearchRoleInvitationsActionResult,
    CreateRoleInvitationAction,
    CreateRoleInvitationActionResult,
    RoleInvitationActionResult,
    SearchMyRoleInvitationsAction,
    SearchMyRoleInvitationsActionResult,
    SearchMySentRoleInvitationsAction,
    SearchMySentRoleInvitationsActionResult,
    SearchRoleInvitationsByRoleAction,
    SearchRoleInvitationsByRoleActionResult,
)
from .actions.search_role_invitations import (
    CancelRoleInvitationAction as CancelInvitationAction,
)
from .actions.search_role_invitations import (
    RejectRoleInvitationAction as RejectInvitationAction,
)
from .actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from .actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
)
from .service import PermissionControllerService


class PermissionControllerProcessors(AbstractProcessorPackage):
    """Processor package for RBAC permission controller operations."""

    create_role: ActionProcessor[CreateRoleAction, CreateRoleActionResult]
    ensure_system_role: ActionProcessor[EnsureSystemRoleAction, EnsureSystemRoleActionResult]
    update_role: ActionProcessor[UpdateRoleAction, UpdateRoleActionResult]
    delete_role: ActionProcessor[DeleteRoleAction, DeleteRoleActionResult]
    assign_role: ActionProcessor[AssignRoleAction, AssignRoleActionResult]
    revoke_role: ActionProcessor[RevokeRoleAction, RevokeRoleActionResult]
    bulk_assign_role: ActionProcessor[BulkAssignRoleAction, BulkAssignRoleActionResult]
    bulk_revoke_role: ActionProcessor[BulkRevokeRoleAction, BulkRevokeRoleActionResult]
    get_role_detail: ActionProcessor[GetRoleDetailAction, GetRoleDetailActionResult]
    search_roles: ActionProcessor[SearchRolesAction, SearchRolesActionResult]
    search_roles_in_scope: ScopeActionProcessor[
        SearchRolesInScopeAction, SearchRolesInScopeActionResult
    ]
    search_users_assigned_to_role: ActionProcessor[
        SearchUsersAssignedToRoleAction, SearchUsersAssignedToRoleActionResult
    ]
    update_role_permissions: ActionProcessor[
        UpdateRolePermissionsAction, UpdateRolePermissionsActionResult
    ]
    bulk_add_role_permissions: ActionProcessor[
        BulkAddRolePermissionsAction, BulkAddRolePermissionsActionResult
    ]
    bulk_remove_role_permissions: ActionProcessor[
        BulkRemoveRolePermissionsAction, BulkRemoveRolePermissionsActionResult
    ]
    replace_role_permissions: ActionProcessor[
        ReplaceRolePermissionsAction, ReplaceRolePermissionsActionResult
    ]
    search_scopes: ActionProcessor[SearchScopesAction, SearchScopesActionResult]
    get_scope_types: ActionProcessor[GetScopeTypesAction, GetScopeTypesActionResult]
    get_entity_types: ActionProcessor[GetEntityTypesAction, GetEntityTypesActionResult]
    get_permission_matrix: ActionProcessor[
        GetPermissionMatrixAction, GetPermissionMatrixActionResult
    ]
    search_entities: ActionProcessor[SearchEntitiesAction, SearchEntitiesActionResult]
    search_element_associations: ActionProcessor[
        SearchElementAssociationsAction, SearchElementAssociationsActionResult
    ]
    search_permissions: ActionProcessor[SearchPermissionsAction, SearchPermissionsActionResult]
    create_permission: ActionProcessor[CreatePermissionAction, CreatePermissionActionResult]
    update_permission: ActionProcessor[UpdatePermissionAction, UpdatePermissionActionResult]
    delete_permission: ActionProcessor[DeletePermissionAction, DeletePermissionActionResult]
    create_role_invitation: ScopeActionProcessor[
        CreateRoleInvitationAction, CreateRoleInvitationActionResult
    ]
    accept_role_invitation: SingleEntityActionProcessor[
        AcceptInvitationAction, RoleInvitationActionResult
    ]
    reject_role_invitation: SingleEntityActionProcessor[
        RejectInvitationAction, RoleInvitationActionResult
    ]
    cancel_role_invitation: SingleEntityActionProcessor[
        CancelInvitationAction, RoleInvitationActionResult
    ]
    search_my_role_invitations: ScopeActionProcessor[
        SearchMyRoleInvitationsAction, SearchMyRoleInvitationsActionResult
    ]
    search_my_sent_role_invitations: ScopeActionProcessor[
        SearchMySentRoleInvitationsAction, SearchMySentRoleInvitationsActionResult
    ]
    search_role_invitations_by_role: ScopeActionProcessor[
        SearchRoleInvitationsByRoleAction, SearchRoleInvitationsByRoleActionResult
    ]
    admin_search_role_invitations: ActionProcessor[
        AdminSearchRoleInvitationsAction, AdminSearchRoleInvitationsActionResult
    ]

    def __init__(
        self,
        service: PermissionControllerService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create_role = ActionProcessor(service.create_role, action_monitors)
        self.ensure_system_role = ActionProcessor(service.ensure_system_role, action_monitors)
        self.update_role = ActionProcessor(service.update_role, action_monitors)
        self.delete_role = ActionProcessor(service.delete_role, action_monitors)
        self.purge_role = ActionProcessor(service.purge_role, action_monitors)
        self.assign_role = ActionProcessor(service.assign_role, action_monitors)
        self.revoke_role = ActionProcessor(service.revoke_role, action_monitors)
        self.bulk_assign_role = ActionProcessor(service.bulk_assign_role, action_monitors)
        self.bulk_revoke_role = ActionProcessor(service.bulk_revoke_role, action_monitors)
        self.get_role_detail = ActionProcessor(service.get_role_detail, action_monitors)
        self.search_roles = ActionProcessor(service.search_roles, action_monitors)
        scope_rbac_validators = [validators.rbac.scope]
        self.search_roles_in_scope = ScopeActionProcessor(
            service.search_roles_in_scope, action_monitors, validators=scope_rbac_validators
        )
        self.search_users_assigned_to_role = ActionProcessor(
            service.search_users_assigned_to_role, action_monitors
        )
        self.update_role_permissions = ActionProcessor(
            service.update_role_permissions, action_monitors
        )
        self.bulk_add_role_permissions = ActionProcessor(
            service.bulk_add_role_permissions, action_monitors
        )
        self.bulk_remove_role_permissions = ActionProcessor(
            service.bulk_remove_role_permissions, action_monitors
        )
        self.replace_role_permissions = ActionProcessor(
            service.replace_role_permissions, action_monitors
        )
        self.search_scopes = ActionProcessor(service.search_scopes, action_monitors)
        self.get_scope_types = ActionProcessor(service.get_scope_types, action_monitors)
        self.get_entity_types = ActionProcessor(service.get_entity_types, action_monitors)
        self.get_permission_matrix = ActionProcessor(service.get_permission_matrix, action_monitors)
        self.search_entities = ActionProcessor(service.search_entities, action_monitors)
        self.search_element_associations = ActionProcessor(
            service.search_element_associations, action_monitors
        )
        self.search_permissions = ActionProcessor(service.search_permissions, action_monitors)
        self.create_permission = ActionProcessor(service.create_permission, action_monitors)
        self.update_permission = ActionProcessor(service.update_permission, action_monitors)
        self.delete_permission = ActionProcessor(service.delete_permission, action_monitors)
        invitation_scope_validators = [validators.rbac.scope]
        invitation_entity_validators = [validators.rbac.single_entity]
        self.create_role_invitation = ScopeActionProcessor(
            service.create_role_invitation, action_monitors, validators=invitation_scope_validators
        )
        self.accept_role_invitation = SingleEntityActionProcessor(
            service.accept_invitation, action_monitors, validators=invitation_entity_validators
        )
        self.reject_role_invitation = SingleEntityActionProcessor(
            service.reject_invitation, action_monitors, validators=invitation_entity_validators
        )
        self.cancel_role_invitation = SingleEntityActionProcessor(
            service.cancel_invitation, action_monitors, validators=invitation_entity_validators
        )
        self.search_my_role_invitations = ScopeActionProcessor(
            service.search_my_role_invitations,
            action_monitors,
            validators=invitation_scope_validators,
        )
        self.search_my_sent_role_invitations = ScopeActionProcessor(
            service.search_my_sent_role_invitations,
            action_monitors,
            validators=invitation_scope_validators,
        )
        self.search_role_invitations_by_role = ScopeActionProcessor(
            service.search_role_invitations_by_role,
            action_monitors,
            validators=invitation_scope_validators,
        )
        self.admin_search_role_invitations = ActionProcessor(
            service.admin_search_role_invitations, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRoleAction.spec(),
            EnsureSystemRoleAction.spec(),
            UpdateRoleAction.spec(),
            DeleteRoleAction.spec(),
            PurgeRoleAction.spec(),
            AssignRoleAction.spec(),
            RevokeRoleAction.spec(),
            BulkAssignRoleAction.spec(),
            BulkRevokeRoleAction.spec(),
            GetRoleDetailAction.spec(),
            SearchRolesAction.spec(),
            SearchRolesInScopeAction.spec(),
            SearchUsersAssignedToRoleAction.spec(),
            UpdateRolePermissionsAction.spec(),
            BulkAddRolePermissionsAction.spec(),
            BulkRemoveRolePermissionsAction.spec(),
            ReplaceRolePermissionsAction.spec(),
            SearchScopesAction.spec(),
            GetScopeTypesAction.spec(),
            GetEntityTypesAction.spec(),
            GetPermissionMatrixAction.spec(),
            SearchEntitiesAction.spec(),
            SearchElementAssociationsAction.spec(),
            SearchPermissionsAction.spec(),
            CreatePermissionAction.spec(),
            UpdatePermissionAction.spec(),
            DeletePermissionAction.spec(),
            CreateRoleInvitationAction.spec(),
            AcceptInvitationAction.spec(),
            RejectInvitationAction.spec(),
            CancelInvitationAction.spec(),
            SearchMyRoleInvitationsAction.spec(),
            SearchMySentRoleInvitationsAction.spec(),
            SearchRoleInvitationsByRoleAction.spec(),
            AdminSearchRoleInvitationsAction.spec(),
        ]
