import logging
from collections.abc import Sequence
from typing import cast

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import (
    UserRoleRevocationData,
)
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    CreateRoleInput,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import (
    AssignRoleAction,
    AssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_add_role_permissions import (
    BulkAddRolePermissionsAction,
    BulkAddRolePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleAction,
    BulkAssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_remove_role_permissions import (
    BulkRemoveRolePermissionsAction,
    BulkRemoveRolePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_revoke_role import (
    BulkRevokeRoleAction,
    BulkRevokeRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import (
    CreateRoleAction,
    CreateRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import (
    DeleteRoleAction,
    DeleteRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
    GetEntityTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    GetPermissionMatrixAction,
    GetPermissionMatrixActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
    GetRoleDetailActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
    GetScopeTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    CreatePermissionActionResult,
    DeletePermissionAction,
    DeletePermissionActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import (
    PurgeRoleAction,
    PurgeRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.resolve_effective_permissions import (
    ResolveEffectivePermissionsAction,
    ResolveEffectivePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import (
    RevokeRoleAction,
    RevokeRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_element_associations import (
    SearchElementAssociationsAction,
    SearchElementAssociationsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
    SearchEntitiesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_invitations import (
    AcceptRoleInvitationAction as AcceptRoleInvitationServiceAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_invitations import (
    AdminSearchRoleInvitationsAction,
    AdminSearchRoleInvitationsActionResult,
    CreateRoleInvitationActionResult,
    RoleInvitationActionResult,
    SearchMyRoleInvitationsAction,
    SearchMyRoleInvitationsActionResult,
    SearchMySentRoleInvitationsAction,
    SearchMySentRoleInvitationsActionResult,
    SearchRoleInvitationsByRoleAction,
    SearchRoleInvitationsByRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_invitations import (
    CancelRoleInvitationAction as CancelRoleInvitationServiceAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_invitations import (
    CreateRoleInvitationAction as CreateRoleInvitationServiceAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_invitations import (
    RejectRoleInvitationAction as RejectRoleInvitationServiceAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles_in_scope import (
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import (
    UpdateRoleAction,
    UpdateRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_role_permissions import (
    UpdateRolePermissionsAction,
    UpdateRolePermissionsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Grant operations are declared in the RBAC action registry as placeholders for a future
# entity-delegation feature, but no executable action can request them yet
# (``ActionOperationType`` has no GRANT member). Exclude them from the permission matrix so
# it only exposes (scope, entity, operation) combinations that are actually enforced.
_GRANT_OPERATIONS: frozenset[OperationType] = frozenset({
    OperationType.GRANT_ALL,
    OperationType.GRANT_READ,
    OperationType.GRANT_UPDATE,
    OperationType.GRANT_SOFT_DELETE,
    OperationType.GRANT_HARD_DELETE,
})


class PermissionControllerService:
    _repository: PermissionControllerRepository
    _group_repository: GroupRepository
    _rbac_action_registry: Sequence[type[BaseRBACAction]]

    def __init__(
        self,
        repository: PermissionControllerRepository,
        group_repository: GroupRepository,
        rbac_action_registry: Sequence[type[BaseRBACAction]],
    ) -> None:
        self._repository = repository
        self._group_repository = group_repository
        self._rbac_action_registry = rbac_action_registry

    async def create_role(self, action: CreateRoleAction) -> CreateRoleActionResult:
        """
        Creates a new role in the repository.
        """
        input_data = CreateRoleInput(
            creator=action.creator,
            object_permissions=action.object_permissions,
            scope_refs=action.scope_refs,
        )
        result = await self._repository.create_role(input_data)
        return CreateRoleActionResult(
            data=result,
        )

    async def create_permission(
        self, action: CreatePermissionAction
    ) -> CreatePermissionActionResult:
        """
        Creates a new permission in the repository.
        """
        result = await self._repository.create_permission(action.creator)
        return CreatePermissionActionResult(data=result)

    async def delete_permission(
        self, action: DeletePermissionAction
    ) -> DeletePermissionActionResult:
        """
        Deletes a permission from the repository.
        """
        result = await self._repository.delete_permission(action.purger)
        return DeletePermissionActionResult(data=result)

    async def update_permission(
        self, action: UpdatePermissionAction
    ) -> UpdatePermissionActionResult:
        """
        Updates an existing permission in the repository.
        """
        result = await self._repository.update_permission(action.updater)
        return UpdatePermissionActionResult(data=result)

    async def update_role(self, action: UpdateRoleAction) -> UpdateRoleActionResult:
        """
        Updates an existing role in the repository.
        """
        result = await self._repository.update_role(action.updater)
        return UpdateRoleActionResult(data=result)

    async def delete_role(self, action: DeleteRoleAction) -> DeleteRoleActionResult:
        """
        Deletes a role from the repository. It marks the role as deleted (soft delete).
        Raises ObjectNotFound if the role does not exist.
        """
        result = await self._repository.delete_role(action.updater)
        return DeleteRoleActionResult(data=result)

    async def purge_role(self, action: PurgeRoleAction) -> PurgeRoleActionResult:
        """
        Purges a role from the repository. It permanently removes the role (hard delete).
        Raises ObjectNotFound if the role does not exist.
        """
        result = await self._repository.purge_role(action.purger)
        return PurgeRoleActionResult(data=result)

    async def assign_role(self, action: AssignRoleAction) -> AssignRoleActionResult:
        """Assigns a role to a user.

        When project_id is provided, also binds the user to the project.
        """
        if action.input.project_id is not None:
            await self._group_repository.bind_user_to_project(
                action.input.user_id, action.input.project_id
            )
        data = await self._repository.assign_role(action.input)
        return AssignRoleActionResult(data=data)

    async def revoke_role(self, action: RevokeRoleAction) -> RevokeRoleActionResult:
        """Revokes a role from a user.

        If the role was project-scoped and no remaining roles exist in that
        project, the user is also removed from the project.
        """
        result = await self._repository.revoke_role(action.input)
        for prc in result.project_remaining_roles:
            if prc.remaining_count == 0:
                await self._group_repository.unbind_user_from_project(
                    action.input.user_id, prc.project_id
                )
        return RevokeRoleActionResult(
            data=UserRoleRevocationData(
                user_role_id=result.user_role_id,
                user_id=action.input.user_id,
                role_id=action.input.role_id,
            )
        )

    async def bulk_assign_role(self, action: BulkAssignRoleAction) -> BulkAssignRoleActionResult:
        """Assigns a role to multiple users with partial failure support.

        When project_id is provided, also binds each user to the project.
        """
        if action.project_id is not None:
            for spec in action.bulk_creator.specs:
                user_role_spec = cast(UserRoleCreatorSpec, spec)
                await self._group_repository.bind_user_to_project(
                    user_role_spec.user_id, action.project_id
                )
        data = await self._repository.bulk_assign_role(action.bulk_creator)
        return BulkAssignRoleActionResult(data=data)

    async def bulk_revoke_role(self, action: BulkRevokeRoleAction) -> BulkRevokeRoleActionResult:
        """Revokes a role from multiple users with partial failure support."""
        data = await self._repository.bulk_revoke_role(action.input)
        return BulkRevokeRoleActionResult(data=data)

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: SearchRolesAction) -> SearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return SearchRolesActionResult(result=result)

    async def search_roles_in_scope(
        self, action: SearchRolesInScopeAction
    ) -> SearchRolesInScopeActionResult:
        """Search roles registered in a given scope."""
        result = await self._repository.search_roles_in_scope(action.querier, action.scope)
        return SearchRolesInScopeActionResult(
            result=result,
            _scope_type=action.scope.element_type.to_scope_type(),
            _scope_id=action.scope.scope_id,
        )

    async def search_permissions(
        self, action: SearchPermissionsAction
    ) -> SearchPermissionsActionResult:
        """Search scoped permissions with pagination and filtering."""
        result = await self._repository.search_permissions(action.querier)
        return SearchPermissionsActionResult(result=result)

    async def search_users_assigned_to_role(
        self, action: SearchUsersAssignedToRoleAction
    ) -> SearchUsersAssignedToRoleActionResult:
        """Search users assigned to a specific role with pagination and filtering."""
        result = await self._repository.search_users_assigned_to_role(
            querier=action.querier,
        )
        return SearchUsersAssignedToRoleActionResult(result=result)

    async def update_role_permissions(
        self, action: UpdateRolePermissionsAction
    ) -> UpdateRolePermissionsActionResult:
        """Update role permissions using batch update."""
        result = await self._repository.update_role_permissions(
            input_data=action.input_data,
        )
        return UpdateRolePermissionsActionResult(role=result)

    async def bulk_add_role_permissions(
        self, action: BulkAddRolePermissionsAction
    ) -> BulkAddRolePermissionsActionResult:
        """Bulk-insert permission rows defined by the action's creator."""
        result = await self._repository.bulk_add_role_permissions(action.creator)
        return BulkAddRolePermissionsActionResult(data=result)

    async def bulk_remove_role_permissions(
        self, action: BulkRemoveRolePermissionsAction
    ) -> BulkRemoveRolePermissionsActionResult:
        """Bulk-delete permission rows for the given purgers."""
        result = await self._repository.bulk_remove_role_permissions(action.purgers)
        return BulkRemoveRolePermissionsActionResult(data=result)

    async def replace_role_permissions(
        self, action: ReplaceRolePermissionsAction
    ) -> ReplaceRolePermissionsActionResult:
        """Replace the role's entire scoped-permission set."""
        result = await self._repository.replace_role_permissions(
            role_id=action.role_id,
            creator=action.creator,
        )
        return ReplaceRolePermissionsActionResult(data=result)

    async def search_scopes(self, action: SearchScopesAction) -> SearchScopesActionResult:
        """Search scopes based on element type."""
        result = await self._repository.search_scopes(action.element_type, action.querier)
        return SearchScopesActionResult(result=result)

    async def get_scope_types(self, _action: GetScopeTypesAction) -> GetScopeTypesActionResult:
        """Get all available scope types."""
        return GetScopeTypesActionResult(element_types=list(RBACElementType))

    async def get_entity_types(self, _action: GetEntityTypesAction) -> GetEntityTypesActionResult:
        """Get all available entity types."""
        return GetEntityTypesActionResult(element_types=list(RBACElementType))

    async def search_entities(self, action: SearchEntitiesAction) -> SearchEntitiesActionResult:
        """Search entities within a scope."""
        result = await self._repository.search_entities(action.querier)
        return SearchEntitiesActionResult(result=result)

    async def search_element_associations(
        self, action: SearchElementAssociationsAction
    ) -> SearchElementAssociationsActionResult:
        """Search element associations (full association rows) within a scope."""
        result = await self._repository.search_element_associations(action.querier)
        return SearchElementAssociationsActionResult(result=result)

    def get_entity_valid_operations(
        self,
    ) -> dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]:
        """
        Get valid operations for all registered RBAC element types.

        Aggregates required permissions from all registered action classes,
        grouping them by element type. Each entry maps action name to its
        required permission.
        """
        result: dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]] = {}
        for action_cls in self._rbac_action_registry:
            perm = action_cls.required_permission()
            actions = result.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm
        return result

    async def get_permission_matrix(
        self, _action: GetPermissionMatrixAction
    ) -> GetPermissionMatrixActionResult:
        """
        Build the RBAC permission matrix: scope -> entity -> action_name -> permission.

        Reads ``permission_scope()`` from each registered RBAC action to produce
        the (scope, entity, operation) mapping. Grant operations are skipped because
        they are not yet enforceable at runtime (see ``_GRANT_OPERATIONS``).
        """
        result: dict[
            RBACElementType, dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]
        ] = {}
        for action_cls in self._rbac_action_registry:
            perm = action_cls.required_permission()
            if perm.operation in _GRANT_OPERATIONS:
                continue
            scope = action_cls.permission_scope()
            entity_map = result.setdefault(scope, {})
            actions = entity_map.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm
        return GetPermissionMatrixActionResult(matrix=result)

    async def resolve_effective_permissions(
        self, action: ResolveEffectivePermissionsAction
    ) -> ResolveEffectivePermissionsActionResult:
        """Resolve the set of permitted operations across a collection of per-target keys.

        Traverses the scope chain and evaluates all role/permission assignments
        to return all operations the user is authorized to perform on each
        target key.
        """
        permissions = await self._repository.resolve_effective_permissions(action.keys)
        return ResolveEffectivePermissionsActionResult(permissions=permissions)

    async def create_role_invitation(
        self, action: CreateRoleInvitationServiceAction
    ) -> CreateRoleInvitationActionResult:
        """Create role invitations by resolving invitee emails."""
        result = await self._repository.create_invitation_by_email(
            invitee_emails=action.invitee_emails,
            inviter_user_id=action.inviter_user_id,
            role_id=action.role_id,
        )
        return CreateRoleInvitationActionResult(created=result.created)

    async def accept_invitation(
        self, action: AcceptRoleInvitationServiceAction
    ) -> RoleInvitationActionResult:
        """Accept a PENDING invitation and assign the role atomically."""
        data = await self._repository.accept_invitation(action.invitation_id)
        return RoleInvitationActionResult(data=data)

    async def reject_invitation(
        self, action: RejectRoleInvitationServiceAction
    ) -> RoleInvitationActionResult:
        """Reject a PENDING invitation."""
        data = await self._repository.reject_invitation(action.invitation_id)
        return RoleInvitationActionResult(data=data)

    async def cancel_invitation(
        self, action: CancelRoleInvitationServiceAction
    ) -> RoleInvitationActionResult:
        """Cancel a PENDING invitation."""
        data = await self._repository.cancel_invitation(action.invitation_id)
        return RoleInvitationActionResult(data=data)

    async def search_my_role_invitations(
        self, action: SearchMyRoleInvitationsAction
    ) -> SearchMyRoleInvitationsActionResult:
        """Search invitations addressed to a specific user."""
        result = await self._repository.search_invitations_by_invitee(action.querier, action.scope)
        return SearchMyRoleInvitationsActionResult(
            result=SearchResult(
                items=result.items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
        )

    async def search_my_sent_role_invitations(
        self, action: SearchMySentRoleInvitationsAction
    ) -> SearchMySentRoleInvitationsActionResult:
        """Search invitations sent by a specific user."""
        result = await self._repository.search_invitations_by_inviter(action.querier, action.scope)
        return SearchMySentRoleInvitationsActionResult(
            result=SearchResult(
                items=result.items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
        )

    async def search_role_invitations_by_role(
        self, action: SearchRoleInvitationsByRoleAction
    ) -> SearchRoleInvitationsByRoleActionResult:
        """Search invitations for a specific role (admin/project-admin view)."""
        result = await self._repository.search_invitations_by_role(action.querier, action.scope)
        return SearchRoleInvitationsByRoleActionResult(
            result=SearchResult(
                items=result.items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
        )

    async def admin_search_role_invitations(
        self, action: AdminSearchRoleInvitationsAction
    ) -> AdminSearchRoleInvitationsActionResult:
        """Search all invitations across the system (superadmin only)."""
        result = await self._repository.admin_search_invitations(action.querier)
        return AdminSearchRoleInvitationsActionResult(
            result=SearchResult(
                items=result.items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
        )
