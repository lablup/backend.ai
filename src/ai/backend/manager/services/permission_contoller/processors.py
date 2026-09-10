from ai.backend.common.data.entity.permission import PermissionFieldType
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    CreatedFieldOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData

from .actions import (
    AddRolePermissionAction,
    BulkRemoveRolePermissionsAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    GetRoleDetailActionResult,
    GlobalSearchRolesAction,
    GlobalSearchRolesActionResult,
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
    UpdateRoleAction,
)
from .actions.bulk_get_roles import BulkGetRolesAction
from .actions.get_entity_types import (
    GlobalGetEntityTypesAction,
    GlobalGetEntityTypesActionResult,
)
from .actions.get_permission_matrix import (
    PublicGetPermissionMatrixAction,
    PublicGetPermissionMatrixActionResult,
)
from .actions.get_scope_types import (
    GlobalGetScopeTypesAction,
    GlobalGetScopeTypesActionResult,
)
from .actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from .actions.permission import (
    CreatePermissionAction,
    CreatePermissionActionResult,
    DeletePermissionAction,
    DeletePermissionActionResult,
)
from .actions.purge_role import PurgeRoleAction
from .actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from .actions.search_scopes import (
    GlobalSearchScopesAction,
    GlobalSearchScopesActionResult,
)
from .actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
)
from .service import PermissionControllerService


class PermissionControllerProcessors:
    """Processor package for RBAC permission controller operations."""

    create_role: ScopeActionProcessor[CreateRoleAction, CreatedEntityOpsResult[RoleData]]
    update_role: SingleEntityActionProcessor[UpdateRoleAction, EntityOpsResult[RoleData]]
    delete_role: SingleEntityActionProcessor[DeleteRoleAction, EntityOpsResult[RoleData]]
    purge_role: SingleEntityActionProcessor[PurgeRoleAction, EntityOpsResult[RoleData]]
    get_role_detail: SingleEntityActionProcessor[GetRoleDetailAction, GetRoleDetailActionResult]
    bulk_get_roles: PartialBulkActionProcessor[BulkGetRolesAction, RoleData]
    global_search_roles: GlobalActionProcessor[
        GlobalSearchRolesAction, GlobalSearchRolesActionResult
    ]
    search_roles_in_scope: ScopeActionProcessor[
        SearchRolesInScopeAction, SearchRolesInScopeActionResult
    ]
    search_users_assigned_to_role: ActionProcessor[
        SearchUsersAssignedToRoleAction, SearchUsersAssignedToRoleActionResult
    ]
    add_role_permission: SingleEntityActionProcessor[
        AddRolePermissionAction, CreatedFieldOpsResult[PermissionData]
    ]
    bulk_remove_role_permissions: PartialBulkFieldActionProcessor[
        BulkRemoveRolePermissionsAction, PermissionData
    ]
    replace_role_permissions: ActionProcessor[
        ReplaceRolePermissionsAction, ReplaceRolePermissionsActionResult
    ]
    global_search_scopes: GlobalActionProcessor[
        GlobalSearchScopesAction, GlobalSearchScopesActionResult
    ]
    global_get_scope_types: GlobalActionProcessor[
        GlobalGetScopeTypesAction, GlobalGetScopeTypesActionResult
    ]
    global_get_entity_types: GlobalActionProcessor[
        GlobalGetEntityTypesAction, GlobalGetEntityTypesActionResult
    ]
    public_get_permission_matrix: PublicActionProcessor[
        PublicGetPermissionMatrixAction, PublicGetPermissionMatrixActionResult
    ]
    search_permissions: ActionProcessor[SearchPermissionsAction, SearchPermissionsActionResult]
    create_permission: ActionProcessor[CreatePermissionAction, CreatePermissionActionResult]
    update_permission: ActionProcessor[UpdatePermissionAction, UpdatePermissionActionResult]
    delete_permission: ActionProcessor[DeletePermissionAction, DeletePermissionActionResult]

    def __init__(
        self,
        role_group: ProcessorGroup[RoleData],
        service: PermissionControllerService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create_role = role_group.entity_create_ops(CreateRoleAction)
        self.update_role = role_group.single_update_ops(UpdateRoleAction)
        self.delete_role = role_group.single_delete_ops(DeleteRoleAction)
        self.purge_role = role_group.entity_purge_ops(PurgeRoleAction)
        self.get_role_detail = role_group.single_entity(
            GetRoleDetailAction, service.get_role_detail
        )
        self.bulk_get_roles = role_group.partial_bulk_get_ops(BulkGetRolesAction)
        self.global_search_roles = role_group.global_scope(
            GlobalSearchRolesAction, service.search_roles
        )
        self.search_roles_in_scope = role_group.scope(
            SearchRolesInScopeAction, service.search_roles_in_scope
        )
        self.search_users_assigned_to_role = ActionProcessor(
            service.search_users_assigned_to_role, action_monitors
        )
        permissions: LookupFieldGroup[PermissionData] = role_group.field_group(
            FieldGroupMeta(PermissionFieldType()),
            PermissionData,
            LookupRolePermissionOwnerAction,
            LookupBulkRolePermissionOwnerAction,
        )
        self.add_role_permission = permissions.create_ops(AddRolePermissionAction)
        self.bulk_remove_role_permissions = permissions.partial_bulk_purge_ops(
            BulkRemoveRolePermissionsAction
        )
        self.replace_role_permissions = ActionProcessor(
            service.replace_role_permissions, action_monitors
        )
        self.global_search_scopes = role_group.global_scope(
            GlobalSearchScopesAction, service.search_scopes
        )
        self.global_get_scope_types = role_group.global_scope(
            GlobalGetScopeTypesAction, service.get_scope_types
        )
        self.global_get_entity_types = role_group.global_scope(
            GlobalGetEntityTypesAction, service.get_entity_types
        )
        self.public_get_permission_matrix = role_group.public(
            PublicGetPermissionMatrixAction, service.get_permission_matrix
        )
        self.search_permissions = ActionProcessor(service.search_permissions, action_monitors)
        self.create_permission = ActionProcessor(service.create_permission, action_monitors)
        self.update_permission = ActionProcessor(service.update_permission, action_monitors)
        self.delete_permission = ActionProcessor(service.delete_permission, action_monitors)
