from ai.backend.common.data.entity.permission import PERMISSION_FIELD_TYPE
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    CreatedFieldOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import (
    ScopeActionProcessor as V2ScopeActionProcessor,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData

from .actions import (
    AddRolePermissionAction,
    BulkRemoveRolePermissionsAction,
    CreateGlobalRoleAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    GetRoleDetailActionResult,
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
    SearchRolesAction,
    SearchRolesActionResult,
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
    UpdateRoleAction,
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
from .actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from .actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
)
from .service import PermissionControllerService


class PermissionControllerProcessors:
    """Processor package for RBAC permission controller operations."""

    create_role: V2ScopeActionProcessor[CreateRoleAction, CreatedEntityOpsResult[RoleData]]
    create_global_role: GlobalActionProcessor[
        CreateGlobalRoleAction, CreatedEntityOpsResult[RoleData]
    ]
    update_role: SingleEntityActionProcessor[UpdateRoleAction, EntityOpsResult[RoleData]]
    delete_role: SingleEntityActionProcessor[DeleteRoleAction, EntityOpsResult[RoleData]]
    purge_role: SingleEntityActionProcessor[PurgeRoleAction, EntityOpsResult[RoleData]]
    get_role_detail: ActionProcessor[GetRoleDetailAction, GetRoleDetailActionResult]
    search_roles: ActionProcessor[SearchRolesAction, SearchRolesActionResult]
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

    def __init__(
        self,
        role_group: ProcessorGroup[RoleData],
        service: PermissionControllerService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create_role = role_group.entity_create_ops(CreateRoleAction)
        self.create_global_role = role_group.global_create_ops(CreateGlobalRoleAction)
        self.update_role = role_group.single_update_ops(UpdateRoleAction)
        self.delete_role = role_group.single_delete_ops(DeleteRoleAction)
        self.purge_role = role_group.entity_purge_ops(PurgeRoleAction)
        self.get_role_detail = ActionProcessor(service.get_role_detail, action_monitors)
        self.search_roles = ActionProcessor(service.search_roles, action_monitors)
        scope_rbac_validators = [validators.rbac.scope]
        self.search_roles_in_scope = ScopeActionProcessor(
            service.search_roles_in_scope, action_monitors, validators=scope_rbac_validators
        )
        self.search_users_assigned_to_role = ActionProcessor(
            service.search_users_assigned_to_role, action_monitors
        )
        permissions: LookupFieldGroup[PermissionData] = role_group.field_group(
            FieldGroupMeta(PERMISSION_FIELD_TYPE),
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
