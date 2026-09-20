from ai.backend.common.data.entity.permission import PermissionFieldType
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    CreatedFieldOpsResult,
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.user.types import UserData

from .actions import (
    AddRolePermissionAction,
    BulkRemoveRolePermissionsAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    GetRoleDetailActionResult,
    GlobalSearchRolesAction,
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
    UpdateRoleAction,
)
from .actions.bulk_get_permissions import BulkGetPermissionsAction
from .actions.bulk_get_roles import BulkGetRolesAction
from .actions.delete_permission import DeletePermissionAction
from .actions.get_entity_types import (
    PublicGetEntityTypesAction,
    PublicGetEntityTypesActionResult,
)
from .actions.get_held_permissions import (
    ScopedGetHeldPermissionsAction,
    ScopedGetHeldPermissionsActionResult,
)
from .actions.get_permission_matrix import (
    PublicGetPermissionMatrixAction,
    PublicGetPermissionMatrixActionResult,
)
from .actions.get_scope_types import (
    PublicGetScopeTypesAction,
    PublicGetScopeTypesActionResult,
)
from .actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from .actions.purge_role import PurgeRoleAction
from .actions.search_my_role_assignments import (
    ScopedSearchRoleAssignmentsAction,
    ScopedSearchRoleAssignmentsActionResult,
)
from .actions.search_permissions import GlobalSearchPermissionsAction
from .actions.search_role_permissions import SearchRolePermissionsAction
from .actions.search_users_assigned_to_role import (
    GlobalSearchRoleAssignmentsAction,
    GlobalSearchRoleAssignmentsActionResult,
)
from .actions.update_permission import UpdatePermissionAction
from .service import PermissionControllerService


class PermissionControllerProcessors:
    """Processor package for RBAC permission controller operations."""

    create_role: ScopeActionProcessor[CreateRoleAction, CreatedEntityOpsResult[RoleData]]
    update_role: SingleEntityActionProcessor[UpdateRoleAction, EntityOpsResult[RoleData]]
    delete_role: SingleEntityActionProcessor[DeleteRoleAction, EntityOpsResult[RoleData]]
    purge_role: SingleEntityActionProcessor[PurgeRoleAction, EntityOpsResult[RoleData]]
    get_role_detail: SingleEntityActionProcessor[GetRoleDetailAction, GetRoleDetailActionResult]
    bulk_get_roles: PartialBulkActionProcessor[BulkGetRolesAction, RoleData]
    global_search_roles: GlobalActionProcessor[GlobalSearchRolesAction, BatchOpsResult[RoleData]]
    search_roles_in_scope: ScopeActionProcessor[
        SearchRolesInScopeAction, SearchRolesInScopeActionResult
    ]
    scoped_search_role_assignments: ScopeActionProcessor[
        ScopedSearchRoleAssignmentsAction, ScopedSearchRoleAssignmentsActionResult
    ]
    global_search_role_assignments: GlobalActionProcessor[
        GlobalSearchRoleAssignmentsAction, GlobalSearchRoleAssignmentsActionResult
    ]
    add_role_permission: SingleEntityActionProcessor[
        AddRolePermissionAction, CreatedFieldOpsResult[PermissionData]
    ]
    bulk_remove_role_permissions: PartialBulkFieldActionProcessor[
        BulkRemoveRolePermissionsAction, PermissionData
    ]
    replace_role_permissions: SingleEntityActionProcessor[
        ReplaceRolePermissionsAction, ReplaceRolePermissionsActionResult
    ]
    public_get_scope_types: PublicActionProcessor[
        PublicGetScopeTypesAction, PublicGetScopeTypesActionResult
    ]
    public_get_entity_types: PublicActionProcessor[
        PublicGetEntityTypesAction, PublicGetEntityTypesActionResult
    ]
    public_get_permission_matrix: PublicActionProcessor[
        PublicGetPermissionMatrixAction, PublicGetPermissionMatrixActionResult
    ]
    scoped_get_held_permissions: ScopeActionProcessor[
        ScopedGetHeldPermissionsAction, ScopedGetHeldPermissionsActionResult
    ]
    bulk_get_permissions: PartialBulkFieldActionProcessor[BulkGetPermissionsAction, PermissionData]
    search_role_permissions: BulkActionProcessor[
        SearchRolePermissionsAction, ScopedFieldsOpsResult[PermissionData]
    ]
    global_search_permissions: GlobalActionProcessor[
        GlobalSearchPermissionsAction, BatchOpsResult[PermissionData]
    ]
    update_permission: SingleFieldActionProcessor[
        UpdatePermissionAction, EntityOpsResult[PermissionData]
    ]
    delete_permission: SingleFieldActionProcessor[
        DeletePermissionAction, EntityOpsResult[PermissionData]
    ]

    def __init__(
        self,
        role_group: ProcessorGroup[RoleData],
        user_group: ProcessorGroup[UserData],
        service: PermissionControllerService,
    ) -> None:
        self.create_role = role_group.entity_create_ops(CreateRoleAction)
        self.update_role = role_group.single_update_ops(UpdateRoleAction)
        self.delete_role = role_group.single_delete_ops(DeleteRoleAction)
        self.purge_role = role_group.entity_purge_ops(PurgeRoleAction)
        self.get_role_detail = role_group.single_entity(
            GetRoleDetailAction, service.get_role_detail
        )
        self.bulk_get_roles = role_group.partial_bulk_get_ops(BulkGetRolesAction)
        self.global_search_roles = role_group.global_searcher_ops(GlobalSearchRolesAction)
        self.search_roles_in_scope = role_group.scope(
            SearchRolesInScopeAction, service.search_roles_in_scope
        )
        self.scoped_search_role_assignments = user_group.scope(
            ScopedSearchRoleAssignmentsAction, service.scoped_search_role_assignments
        )
        self.global_search_role_assignments = role_group.global_scope(
            GlobalSearchRoleAssignmentsAction, service.search_users_assigned_to_role
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
        self.replace_role_permissions = role_group.single_entity(
            ReplaceRolePermissionsAction, service.replace_role_permissions
        )
        self.public_get_scope_types = role_group.public(
            PublicGetScopeTypesAction, service.get_scope_types
        )
        self.public_get_entity_types = role_group.public(
            PublicGetEntityTypesAction, service.get_entity_types
        )
        self.public_get_permission_matrix = role_group.public(
            PublicGetPermissionMatrixAction, service.get_permission_matrix
        )
        self.scoped_get_held_permissions = role_group.scope(
            ScopedGetHeldPermissionsAction, service.get_held_permissions
        )
        self.bulk_get_permissions = permissions.partial_bulk_get_ops(BulkGetPermissionsAction)
        self.search_role_permissions = permissions.atomic_bulk_scoped_search_ops(
            SearchRolePermissionsAction
        )
        self.global_search_permissions = permissions.global_searcher_ops(
            GlobalSearchPermissionsAction
        )
        self.update_permission = permissions.update_ops(UpdatePermissionAction)
        self.delete_permission = permissions.purge_ops(DeletePermissionAction)
