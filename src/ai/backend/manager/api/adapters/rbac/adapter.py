"""RBAC domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    RuntimeEntityID,
)
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.rbac import (
    OrderDirection,
    RoleDTO,
    RoleFilter,
    RoleOrder,
    RoleOrderField,
    RoleSource,
    RoleStatus,
    SearchRolesRequest,
    SearchRolesResponse,
)
from ai.backend.common.dto.manager.rbac.response import PaginationInfo
from ai.backend.common.dto.manager.v2.rbac import (
    BulkAddRolePermissionFailureInfo,
    BulkAddRolePermissionsPayload,
    BulkAssignRoleResultPayload,
    BulkRemoveRolePermissionFailureInfo,
    BulkRemoveRolePermissionsPayload,
    BulkRevokeRoleFailureInfo,
    BulkRevokeRoleResultPayload,
    CreateRoleInput,
    CreateRolePayload,
    DeleteRolePayload,
    EntityActionInfo,
    EntityOperationCombinationInfo,
    OperationInfo,
    PermissionNode,
    PurgeRolePayload,
    ReplaceRolePermissionsPayload,
    RoleAssignmentNode,
    RoleNode,
    ScopeEntityCombinationInfo,
    ScopeEntityOperationCombinationInfo,
    UpdateRoleInput,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac import (
    DeletePermissionPayload as DeletePermissionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchPermissionsGQLInput,
    SearchRoleAssignmentsInput,
    SearchRolesInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput as AssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAddRolePermissionsInput as BulkAddRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAssignRoleInput as BulkAssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRemoveRolePermissionsInput as BulkRemoveRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRevokeRoleInput as BulkRevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreatePermissionInput as CreatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    MappedScopeNestedFilter as MappedScopeNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionFilter as PermissionFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionNestedFilter as PermissionNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionOrderBy as PermissionOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    ReplaceRolePermissionsInput as ReplaceRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RevokeRoleInput as RevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentFilter as RoleAssignmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentOrderBy as RoleAssignmentOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleFilter as RoleFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleNestedFilter as RoleNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleOrderBy as RoleOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UpdatePermissionInput as UpdatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UserNestedFilter as UserNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OrderDirection as OrderDirectionV2,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    PermissionBitDTO,
    PermissionBitFilter,
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    BulkRoleAssignmentResultData,
    BulkRolePermissionReplaceResultData,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    RoleData,
    RoleDetailData,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import RoleStatus as InternalRoleStatus
from ai.backend.manager.data.permission.types import GrantableOperation
from ai.backend.manager.data.permission.types import RoleSource as InternalRoleSource
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.permission import (
    PermissionAlreadyGranted,
    ReplaceRolePermissionRoleIdMismatch,
)
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.rbac.exceptions import InvalidScope
from ai.backend.manager.models.rbac_models.conditions import (
    AssignedUserConditions,
)
from ai.backend.manager.models.rbac_models.orders import (
    AssignedUserOrders,
)
from ai.backend.manager.models.rbac_models.permission.conditions import (
    ScopedPermissionConditions,
)
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.orders import ScopedPermissionOrders
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role.conditions import RoleConditions
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.orders import RoleOrders
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleOperationScope
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater, RoleUpdater
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.add_role_permission import (
    AddRolePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_remove_role_permissions import (
    BulkRemoveRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.delete_role import DeleteRoleAction
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    GetPermissionMatrixAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles_in_scope import (
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import UpdateRoleAction
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.bulk_revoke import (
    BulkRevokeRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.revoke import RevokeRoleAction
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.types import OptionalState, TriState

# ------------------------------------------------------------------ pagination specs


@lru_cache(maxsize=1)
def _permission_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScopedPermissionOrders.created_at(ascending=False),
        backward_order=ScopedPermissionOrders.created_at(ascending=True),
        forward_condition_factory=ScopedPermissionConditions.by_cursor_forward,
        backward_condition_factory=ScopedPermissionConditions.by_cursor_backward,
        tiebreaker_order=PermissionRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _role_gql_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RoleOrders.created_at(ascending=False),
        backward_order=RoleOrders.created_at(ascending=True),
        forward_condition_factory=RoleConditions.by_cursor_forward,
        backward_condition_factory=RoleConditions.by_cursor_backward,
        tiebreaker_order=RoleRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _assignment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AssignedUserOrders.granted_at(ascending=False),
        backward_order=AssignedUserOrders.granted_at(ascending=True),
        forward_condition_factory=AssignedUserConditions.by_cursor_forward,
        backward_condition_factory=AssignedUserConditions.by_cursor_backward,
        tiebreaker_order=UserRoleRow.id.asc(),
    )


class RBACAdapter(BaseAdapter):
    """Adapter for RBAC domain operations.

    Exposes: create, admin_search, get, update, delete, purge.
    assign/revoke/bulk operations require specialized inputs not
    yet bridged through this adapter.
    """

    _rbac: RbacProcessors
    _permission_controller: PermissionControllerProcessors

    def __init__(
        self,
        rbac: RbacProcessors,
        permission_controller: PermissionControllerProcessors,
    ) -> None:
        self._rbac = rbac
        self._permission_controller = permission_controller

    def _validate_scope_id(self, scope_type: EntityType, scope_id: str) -> None:
        """Raise InvalidScope if scope_id is not a valid UUID for scope types that require one."""
        match scope_type:
            case UserEntityType() | ProjectEntityType() | DomainEntityType():
                self._scope_uuid(scope_type, scope_id)
            case _:
                pass

    def _scope_uuid(self, scope_type: EntityType, scope_id: str) -> UUID:
        try:
            return UUID(scope_id)
        except ValueError:
            raise InvalidScope(
                f"scope_id must be a valid UUID for scope_type '{scope_type}', got '{scope_id}'"
            ) from None

    def _scope_identifier(self, scope_type: EntityType, scope_id: str) -> EntityIdentifier:
        value = self._scope_uuid(scope_type, scope_id)
        match scope_type:
            case DomainEntityType():
                return DomainID(value)
            case ProjectEntityType():
                return ProjectID(value)
            case UserEntityType():
                return UserID(value)
            case _:
                return RuntimeEntityID(scope_type, value)

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_roles_by_ids(self, role_ids: Sequence[RoleID]) -> list[RoleNode | None]:
        """Batch load roles by ID for DataLoader use.

        Returns RoleNode DTOs in the same order as the input role_ids list.
        """
        if not role_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[RoleConditions.by_ids(role_ids)],
        )
        action_result: SearchRolesActionResult = (
            await self._permission_controller.search_roles.wait_for_complete(
                SearchRolesAction(querier=querier)
            )
        )
        role_map: dict[UUID, RoleNode] = {
            data.id: self._role_data_to_node(data) for data in action_result.result.items
        }
        return [role_map.get(role_id) for role_id in role_ids]

    async def batch_load_permissions_by_ids(
        self, permission_ids: Sequence[PermissionID]
    ) -> list[PermissionNode | None]:
        """Batch load permissions by ID for DataLoader use.

        Returns PermissionNode DTOs in the same order as the input permission_ids list.
        """
        if not permission_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ScopedPermissionConditions.by_ids(permission_ids)],
        )
        action_result: SearchPermissionsActionResult = (
            await self._permission_controller.search_permissions.wait_for_complete(
                SearchPermissionsAction(querier=querier)
            )
        )
        permission_map: dict[UUID, PermissionNode] = {
            data.id: self._permission_data_to_node(data) for data in action_result.result.items
        }
        return [permission_map.get(pid) for pid in permission_ids]

    async def batch_load_role_assignments_by_ids(
        self, assignment_ids: Sequence[UUID]
    ) -> list[RoleAssignmentNode | None]:
        """Batch load role assignments by ID for DataLoader use.

        Returns RoleAssignmentNode DTOs in the same order as the input assignment_ids list.
        """
        if not assignment_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AssignedUserConditions.by_ids(assignment_ids)],
        )
        action_result: SearchUsersAssignedToRoleActionResult = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        assignment_map: dict[UUID, RoleAssignmentNode] = {
            data.id: self._assignment_data_to_node(data) for data in action_result.result.items
        }
        return [assignment_map.get(aid) for aid in assignment_ids]

    async def batch_load_permissions_by_role_ids(
        self, role_ids: Sequence[RoleID]
    ) -> list[list[PermissionNode]]:
        """Batch load permissions grouped by role_id for DataLoader use.

        Returns a list of permission lists, one per role_id (empty list if no permissions).
        """
        if not role_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ScopedPermissionConditions.by_role_ids(role_ids)],
        )
        action_result: SearchPermissionsActionResult = (
            await self._permission_controller.search_permissions.wait_for_complete(
                SearchPermissionsAction(querier=querier)
            )
        )
        result_map: dict[UUID, list[PermissionNode]] = defaultdict(list)
        for item in action_result.result.items:
            result_map[item.role_id].append(self._permission_data_to_node(item))
        return [result_map.get(role_id, []) for role_id in role_ids]

    async def batch_load_role_assignments_by_user_ids(
        self, user_ids: Sequence[UserID]
    ) -> list[list[RoleAssignmentNode]]:
        """Batch load role assignments grouped by user_id for DataLoader use.

        Returns a list of assignment lists, one per user_id (empty list if no assignments).
        """
        if not user_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AssignedUserConditions.by_user_ids(user_ids)],
        )
        action_result: SearchUsersAssignedToRoleActionResult = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        result_map: dict[UUID, list[RoleAssignmentNode]] = defaultdict(list)
        for item in action_result.result.items:
            result_map[item.user_id].append(self._assignment_data_to_node(item))
        return [result_map.get(user_id, []) for user_id in user_ids]

    async def batch_load_assignments_by_role_ids(
        self, role_ids: Sequence[RoleID]
    ) -> list[list[RoleAssignmentNode]]:
        """Batch load role assignments grouped by role_id for DataLoader use.

        Returns a list of assignment lists, one per role_id (empty list if no assignments).
        """
        if not role_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AssignedUserConditions.by_role_ids(role_ids)],
        )
        action_result: SearchUsersAssignedToRoleActionResult = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        result_map: dict[UUID, list[RoleAssignmentNode]] = defaultdict(list)
        for item in action_result.result.items:
            result_map[item.role_id].append(self._assignment_data_to_node(item))
        return [result_map.get(role_id, []) for role_id in role_ids]

    async def batch_load_role_assignments_by_role_and_user_ids(
        self, pairs: Sequence[tuple[uuid.UUID, uuid.UUID]]
    ) -> list[RoleAssignmentNode | None]:
        """Batch load role assignments by (role_id, user_id) compound key for DataLoader use.

        Returns RoleAssignmentNode DTOs in the same order as the input pairs list.
        """
        if not pairs:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AssignedUserConditions.by_role_and_user_ids(pairs)],
        )
        action_result: SearchUsersAssignedToRoleActionResult = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        result_map: dict[tuple[uuid.UUID, uuid.UUID], RoleAssignmentNode] = {
            (item.role_id, item.user_id): self._assignment_data_to_node(item)
            for item in action_result.result.items
        }
        return [result_map.get(pair) for pair in pairs]

    # ------------------------------------------------------------------ permission catalog

    async def _permission_matrix(
        self,
    ) -> Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]]:
        action_result = await self._permission_controller.get_permission_matrix.wait_for_complete(
            GetPermissionMatrixAction()
        )
        return action_result.matrix

    async def get_permission_matrix(self) -> list[ScopeEntityOperationCombinationInfo]:
        """Return the complete RBAC scope-entity-operation permission matrix."""
        matrix = await self._permission_matrix()
        return [
            ScopeEntityOperationCombinationInfo(
                scope_type=scope,
                entities=self._entity_actions(entity_map),
            )
            for scope, entity_map in sorted(matrix.items())
        ]

    async def get_entity_operation_combinations(self) -> list[EntityOperationCombinationInfo]:
        """Return every entity a role may permit and the operations it may permit on it."""
        matrix = await self._permission_matrix()
        return [
            EntityOperationCombinationInfo(
                entity_type=entity.entity_type,
                operations=entity.actions,
            )
            for entity in self._entity_actions(self._any_entity_map(matrix))
        ]

    async def get_scope_entity_combinations(self) -> list[ScopeEntityCombinationInfo]:
        """Return, per scope a role sits in, the entities a permission there may name."""
        matrix = await self._permission_matrix()
        return [
            ScopeEntityCombinationInfo(
                scope_type=scope,
                valid_entity_types=sorted(entity_map),
            )
            for scope, entity_map in sorted(matrix.items())
        ]

    @staticmethod
    def _any_entity_map(
        matrix: Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]],
    ) -> Mapping[EntityType, Sequence[GrantableOperation]]:
        """The entities of any one scope. A permission row names no scope, so every
        scope carries the same ones."""
        for entity_map in matrix.values():
            return entity_map
        return {}

    @staticmethod
    def _entity_actions(
        entity_map: Mapping[EntityType, Sequence[GrantableOperation]],
    ) -> list[EntityActionInfo]:
        return sorted(
            [
                EntityActionInfo(
                    entity_type=entity,
                    actions=[
                        OperationInfo(
                            operation=op.name,
                            description=op.description,
                            required_permission=PermissionBitDTO.of(op.permission),
                        )
                        for op in operations
                    ],
                )
                for entity, operations in entity_map.items()
            ],
            key=lambda e: e.entity_type,
        )

    # ------------------------------------------------------------------ create

    async def create(self, input: CreateRoleInput) -> CreateRolePayload:
        """Create a new role in the one scope the input names."""
        scope_input = input.scope_input()
        result = await self._permission_controller.create_role.run(
            CreateRoleAction(
                creator=RoleCreator(
                    name=input.name,
                    scope=self._scope_identifier(scope_input.scope_type, scope_input.scope_id),
                    description=input.description,
                    auto_assign=input.auto_assign,
                )
            )
        )
        return CreateRolePayload(role=self._role_data_to_node(result.data))

    # ------------------------------------------------------------------ search

    async def admin_search(self, input: SearchRolesRequest) -> SearchRolesResponse:
        """Search roles with no scope restriction (admin only)."""
        querier = self._build_search_querier(input)
        action_result = await self._permission_controller.search_roles.wait_for_complete(
            SearchRolesAction(querier=querier)
        )
        result = action_result.result
        return SearchRolesResponse(
            roles=[self._role_data_to_dto(r) for r in result.items],
            pagination=PaginationInfo(
                total=result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    # ------------------------------------------------------------------ GQL search

    async def admin_search_permissions_gql(
        self,
        input: AdminSearchPermissionsGQLInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[PermissionNode]:
        """Search scoped permissions with cursor/offset pagination."""
        conditions = self._convert_permission_filter(input.filter) if input.filter else []
        orders = self._convert_permission_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_permission_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        action_result: SearchPermissionsActionResult = (
            await self._permission_controller.search_permissions.wait_for_complete(
                SearchPermissionsAction(querier=querier)
            )
        )
        raw = action_result.result
        return SearchResult(
            items=[self._permission_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def admin_search_roles_gql(
        self,
        input: SearchRolesInput,
    ) -> SearchResult[RoleNode]:
        """Search roles with cursor/offset pagination."""
        conditions = self._convert_role_filter_gql(input.filter) if input.filter else []
        orders = self._convert_role_orders_gql(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_gql_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result: SearchRolesActionResult = (
            await self._permission_controller.search_roles.wait_for_complete(
                SearchRolesAction(querier=querier)
            )
        )
        raw = action_result.result
        return SearchResult(
            items=[self._role_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def search_roles_in_scope(
        self,
        scope: ScopedRoleOperationScope,
        input: SearchRolesInput,
    ) -> SearchResult[RoleNode]:
        """Search roles registered in a given scope."""
        conditions = self._convert_role_filter_gql(input.filter) if input.filter else []
        orders = self._convert_role_orders_gql(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_gql_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result: SearchRolesInScopeActionResult = (
            await self._permission_controller.search_roles_in_scope.run(
                SearchRolesInScopeAction(scope=scope, querier=querier)
            )
        )
        raw = action_result.result
        return SearchResult(
            items=[self._role_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def my_search_role_assignments(
        self,
        input: SearchRoleAssignmentsInput,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search role assignments for the current authenticated user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self._search_role_assignments(
            input,
            base_conditions=[AssignedUserConditions.by_user_id(me.user_id)],
        )

    async def admin_search_role_assignments(
        self,
        input: SearchRoleAssignmentsInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search role assignments with cursor/offset pagination (admin)."""
        return await self._search_role_assignments(input, base_conditions=base_conditions)

    async def _search_role_assignments(
        self,
        input: SearchRoleAssignmentsInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[RoleAssignmentNode]:
        """Internal implementation for searching role assignments."""
        conditions = self._convert_assignment_filter(input.filter) if input.filter else []
        orders = self._convert_assignment_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_assignment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        action_result: SearchUsersAssignedToRoleActionResult = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        raw = action_result.result
        return SearchResult(
            items=[self._assignment_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def get(self, role_id: UUID) -> RoleNode:
        """Get a role by ID."""
        action_result = await self._permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=role_id)
        )
        return self._role_detail_to_node(action_result.role)

    # ------------------------------------------------------------------ update

    async def update(self, role_id: UUID, input: UpdateRoleInput) -> UpdateRolePayload:
        """Update an existing role."""
        updater = self._build_updater(role_id, input)
        result = await self._permission_controller.update_role.run(
            UpdateRoleAction(updater=updater)
        )
        return UpdateRolePayload(role=self._role_data_to_node(result.data))

    # ------------------------------------------------------------------ delete

    async def delete(self, role_id: UUID) -> DeleteRolePayload:
        """Soft-delete a role (marks status as DELETED)."""
        result = await self._permission_controller.delete_role.run(
            DeleteRoleAction(updater=RoleSoftDeleteUpdater(role_id=RoleID(role_id)))
        )
        return DeleteRolePayload(id=result.data.id)

    # ------------------------------------------------------------------ purge

    async def purge(self, role_id: UUID) -> PurgeRolePayload:
        """Hard-delete a role from the database."""
        result = await self._permission_controller.purge_role.run(
            PurgeRoleAction(role_id=RoleID(role_id))
        )
        return PurgeRolePayload(id=result.data.id)

    # ------------------------------------------------------------------ delete_permission

    async def delete_permission(self, permission_id: UUID) -> DeletePermissionPayloadDTO:
        """Hard-delete a scoped permission."""
        await self._permission_controller.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=RolePermissionPurger(PermissionID(permission_id)))
        )
        return DeletePermissionPayloadDTO(id=permission_id)

    # ------------------------------------------------------------------ create_permission / update_permission

    async def create_permission(self, input: CreatePermissionInputDTO) -> PermissionNode:
        """Create a permission on the role; it holds in the scope the role sits in."""
        creator = RolePermissionCreator(
            entity_type=input.entity_type,
            permission=single_bit(input.permission_bit()),
        )
        action_result = await self._permission_controller.create_permission.wait_for_complete(
            CreatePermissionAction(role_id=RoleID(input.role_id), creator=creator)
        )
        return self._permission_data_to_node(action_result.data)

    async def update_permission(self, input: UpdatePermissionInputDTO) -> PermissionNode:
        """Update an existing permission."""
        updater = RolePermissionUpdater(
            permission_id=PermissionID(input.id),
            entity_type=(
                OptionalState.update(input.entity_type)
                if input.entity_type is not None
                else OptionalState.nop()
            ),
            permission=(
                OptionalState.update(single_bit(input.permission_bit()))
                if input.permission is not None
                else OptionalState.nop()
            ),
        )
        action_result = await self._permission_controller.update_permission.wait_for_complete(
            UpdatePermissionAction(updater=updater)
        )
        return self._permission_data_to_node(action_result.data)

    # ------------------------------------------------------------------ assign_role / revoke_role

    async def assign_role(self, input: AssignRoleInputDTO) -> RoleAssignmentNode:
        """Assign a role to a user."""
        action_result = await self._rbac.assign_role.wait_for_complete(
            AssignRoleAction(
                input=UserRoleAssignmentInput(
                    user_id=input.user_id,
                    role_id=input.role_id,
                    project_id=input.project_id,
                )
            )
        )
        data: UserRoleAssignmentData = action_result.data
        return RoleAssignmentNode(
            id=data.id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=data.granted_by,
            granted_at=datetime.now(tz=UTC),
        )

    async def revoke_role(self, input: RevokeRoleInputDTO) -> RoleAssignmentNode:
        """Revoke a role from a user."""
        action_result = await self._rbac.revoke_role.wait_for_complete(
            RevokeRoleAction(
                input=UserRoleRevocationInput(user_id=input.user_id, role_id=input.role_id)
            )
        )
        data: UserRoleRevocationData = action_result.data
        return RoleAssignmentNode(
            id=data.user_role_id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )

    # ------------------------------------------------------------------ bulk_assign_role / bulk_revoke_role

    async def bulk_assign_role(self, input: BulkAssignRoleInputDTO) -> BulkAssignRoleResultPayload:
        """Bulk-assign a role to multiple users."""
        action_result = await self._rbac.bulk_assign_role.wait_for_complete(
            BulkAssignRoleAction(
                role_id=RoleID(input.role_id),
                user_ids=[UserID(uid) for uid in input.user_ids],
                project_id=input.project_id,
            )
        )
        result: BulkRoleAssignmentResultData = action_result.data
        now = datetime.now(tz=UTC)
        return BulkAssignRoleResultPayload(
            assigned=[
                RoleAssignmentNode(
                    id=s.id,
                    user_id=s.user_id,
                    role_id=s.role_id,
                    granted_by=s.granted_by,
                    granted_at=now,
                )
                for s in result.successes
            ],
            failed=[],
        )

    async def bulk_add_role_permissions(
        self,
        input: BulkAddRolePermissionsInputDTO,
    ) -> BulkAddRolePermissionsPayload:
        """Insert scoped permission rows across one or more roles, one entry at a time,
        each answered for by its role; an entry the database refuses is reported
        beside the ones that landed."""
        items: list[PermissionNode] = []
        failed: list[BulkAddRolePermissionFailureInfo] = []
        for entry in input.permissions:
            try:
                result = await self._permission_controller.add_role_permission.run(
                    AddRolePermissionAction(
                        role_id=RoleID(entry.role_id),
                        creator=self._role_permission_creator(entry),
                    )
                )
            except (PermissionAlreadyGranted, RepositoryIntegrityError) as e:
                failed.append(
                    BulkAddRolePermissionFailureInfo(
                        role_id=entry.role_id,
                        entity_type=entry.entity_type,
                        permission=entry.permission,
                        message=str(e),
                    )
                )
                continue
            items.append(self._permission_data_to_node(result.data))
        return BulkAddRolePermissionsPayload(items=items, failed=failed)

    async def bulk_remove_role_permissions(
        self,
        input: BulkRemoveRolePermissionsInputDTO,
    ) -> BulkRemoveRolePermissionsPayload:
        """Delete permission rows by primary key, each answered for by its role. An id
        matching no row is left out of the answer rather than reported."""
        if not input.permission_ids:
            return BulkRemoveRolePermissionsPayload(items=[], failed=[])
        try:
            result = await self._permission_controller.bulk_remove_role_permissions.run(
                BulkRemoveRolePermissionsAction(
                    permission_ids=[PermissionID(pid) for pid in input.permission_ids]
                )
            )
        except NotFoundError:
            return BulkRemoveRolePermissionsPayload(items=[], failed=[])
        return BulkRemoveRolePermissionsPayload(
            items=[self._permission_data_to_node(item) for item in result.successes.values()],
            failed=[
                BulkRemoveRolePermissionFailureInfo(
                    permission_id=permission_id,
                    message=str(exception),
                )
                for permission_id, exception in result.errors.items()
                if not isinstance(exception, NotFoundError)
            ],
        )

    async def replace_role_permissions(
        self,
        input: ReplaceRolePermissionsInputDTO,
    ) -> ReplaceRolePermissionsPayload:
        """Replace one role's entire scoped-permission set."""
        for entry in input.permissions:
            if entry.role_id != input.role_id:
                raise ReplaceRolePermissionRoleIdMismatch(
                    f"entry role_id {entry.role_id} does not match request role_id {input.role_id}",
                )
        action_result = (
            await self._permission_controller.replace_role_permissions.wait_for_complete(
                ReplaceRolePermissionsAction(
                    role_id=RoleID(input.role_id),
                    entries=self._permission_entries(input.permissions),
                )
            )
        )
        result: BulkRolePermissionReplaceResultData = action_result.data
        return ReplaceRolePermissionsPayload(
            items=[self._permission_data_to_node(item) for item in result.successes],
            failed=[],
        )

    def _permission_entries(
        self, entries: Sequence[CreatePermissionInputDTO]
    ) -> list[PermissionEntry]:
        """One entry per entity type; an input names a single operation, and an entity
        type named more than once holds every operation named on it."""
        held: dict[EntityType, Permission] = {}
        for entry in entries:
            entity_type = entry.entity_type
            held[entity_type] = held.get(entity_type, Permission.NONE) | entry.permission_bit()
        return [
            PermissionEntry(entity_type=entity_type, permission=permission)
            for entity_type, permission in held.items()
        ]

    def _role_permission_creator(self, entry: CreatePermissionInputDTO) -> RolePermissionCreator:
        return RolePermissionCreator(
            entity_type=entry.entity_type,
            permission=entry.permission_bit(),
        )

    async def bulk_revoke_role(self, input: BulkRevokeRoleInputDTO) -> BulkRevokeRoleResultPayload:
        """Bulk-revoke a role from multiple users."""
        action_result = await self._rbac.bulk_revoke_role.wait_for_complete(
            BulkRevokeRoleAction(
                input=BulkUserRoleRevocationInput(role_id=input.role_id, user_ids=input.user_ids)
            )
        )
        result: BulkRoleRevocationResultData = action_result.data
        now = datetime.now(tz=UTC)
        return BulkRevokeRoleResultPayload(
            revoked=[
                RoleAssignmentNode(
                    id=s.user_role_id,
                    user_id=s.user_id,
                    role_id=s.role_id,
                    granted_by=None,
                    granted_at=now,
                )
                for s in result.successes
            ],
            failed=[
                BulkRevokeRoleFailureInfo(user_id=f.user_id, message=f.message)
                for f in result.failures
            ],
        )

    # ------------------------------------------------------------------ helpers (REST layer)

    def _build_search_querier(self, input: SearchRolesRequest) -> BatchQuerier:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders: list[QueryOrder] = []
        if input.order is not None:
            for order in input.order:
                orders.append(self._convert_order(order))
        pagination = OffsetPagination(limit=input.limit, offset=input.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter_req: RoleFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.name is not None:
            condition = self.convert_string_filter(
                filter_req.name,
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
                starts_with_factory=RoleConditions.by_name_starts_with,
                ends_with_factory=RoleConditions.by_name_ends_with,
                in_factory=RoleConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.sources is not None and len(filter_req.sources) > 0:
            conditions.append(RoleConditions.by_sources(filter_req.sources))

        if filter_req.statuses is not None and len(filter_req.statuses) > 0:
            conditions.append(RoleConditions.by_statuses(filter_req.statuses))

        return conditions

    @staticmethod
    def _convert_order(order: RoleOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        if order.field == RoleOrderField.NAME:
            return RoleOrders.name(ascending=ascending)
        if order.field == RoleOrderField.CREATED_AT:
            return RoleOrders.created_at(ascending=ascending)
        if order.field == RoleOrderField.UPDATED_AT:
            return RoleOrders.updated_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    # ------------------------------------------------------------------ helpers (GQL layer)

    def _convert_permission_bit_filter(
        self,
        f: PermissionBitFilter,
        *,
        equals_factory: Callable[[Permission], QueryCondition],
        not_equals_factory: Callable[[Permission], QueryCondition],
        in_factory: Callable[[Collection[Permission]], QueryCondition],
        not_in_factory: Callable[[Collection[Permission]], QueryCondition],
    ) -> list[QueryCondition]:
        """Translate a ``PermissionBitFilter`` into conditions on the permission bit."""
        conditions: list[QueryCondition] = []
        if f.equals is not None:
            conditions.append(equals_factory(f.equals.to_permission()))
        if f.not_equals is not None:
            conditions.append(not_equals_factory(f.not_equals.to_permission()))
        if f.in_:
            conditions.append(in_factory([v.to_permission() for v in f.in_]))
        if f.not_in:
            conditions.append(not_in_factory([v.to_permission() for v in f.not_in]))
        return conditions

    def _convert_permission_filter(self, f: PermissionFilterDTO) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.role_id is not None:
            condition = self.convert_uuid_filter(
                f.role_id,
                equals_factory=ScopedPermissionConditions.by_role_id_equals,
                in_factory=ScopedPermissionConditions.by_role_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.entity_type is not None:
            condition = self.convert_string_filter(
                f.entity_type,
                contains_factory=ScopedPermissionConditions.by_entity_type_match.contains,
                equals_factory=ScopedPermissionConditions.by_entity_type_match.equals,
                starts_with_factory=ScopedPermissionConditions.by_entity_type_match.starts_with,
                ends_with_factory=ScopedPermissionConditions.by_entity_type_match.ends_with,
                in_factory=ScopedPermissionConditions.by_entity_type_match.in_,
            )
            if condition is not None:
                conditions.append(condition)
        if f.created_at is not None:
            cond = f.created_at.build_query_condition(
                before_factory=ScopedPermissionConditions.by_created_at_before,
                after_factory=ScopedPermissionConditions.by_created_at_after,
                equals_factory=ScopedPermissionConditions.by_created_at_equals,
            )
            if cond is not None:
                conditions.append(cond)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_permission_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_permission_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_permission_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_permission_orders(orders: list[PermissionOrderByDTO]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "id":
                result.append(ScopedPermissionOrders.id(ascending))
            elif o.field == "entity_type":
                result.append(ScopedPermissionOrders.entity_type(ascending))
            elif o.field == "created_at":
                result.append(ScopedPermissionOrders.created_at(ascending))
        return result

    def _convert_role_filter_gql(self, f: RoleFilterDTO) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.name is not None:
            condition = self.convert_string_filter(
                f.name,
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
                starts_with_factory=RoleConditions.by_name_starts_with,
                ends_with_factory=RoleConditions.by_name_ends_with,
                in_factory=RoleConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.source is not None:
            src = f.source
            if src.equals is not None:
                conditions.append(RoleConditions.by_source_equals(InternalRoleSource(src.equals)))
            if src.in_ is not None and src.in_:
                conditions.append(
                    RoleConditions.by_sources([InternalRoleSource(s) for s in src.in_])
                )
            if src.not_equals is not None:
                conditions.append(
                    RoleConditions.by_source_not_equals(InternalRoleSource(src.not_equals))
                )
            if src.not_in is not None and src.not_in:
                conditions.append(
                    RoleConditions.by_source_not_in([InternalRoleSource(s) for s in src.not_in])
                )
        if f.status is not None:
            st = f.status
            if st.equals is not None:
                conditions.append(RoleConditions.by_status_equals(InternalRoleStatus(st.equals)))
            if st.in_ is not None and st.in_:
                conditions.append(
                    RoleConditions.by_statuses([InternalRoleStatus(s) for s in st.in_])
                )
            if st.not_equals is not None:
                conditions.append(
                    RoleConditions.by_status_not_equals(InternalRoleStatus(st.not_equals))
                )
            if st.not_in is not None and st.not_in:
                conditions.append(
                    RoleConditions.by_status_not_in([InternalRoleStatus(s) for s in st.not_in])
                )
        if f.assigned_user is not None:
            conditions.extend(self._convert_user_nested_filter(f.assigned_user))
        if f.mapped_scope is not None:
            conditions.extend(self._convert_mapped_scope_nested_filter(f.mapped_scope))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_role_filter_gql(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_role_filter_gql(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_role_filter_gql(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_user_nested_filter(self, f: UserNestedFilterDTO) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if f.user_id is not None:
            condition = self.convert_uuid_filter(
                f.user_id,
                equals_factory=AssignedUserConditions.by_user_id_equals,
                in_factory=AssignedUserConditions.by_user_id_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        conditions: list[QueryCondition] = []
        if raw_conditions:
            conditions.append(RoleConditions.by_assigned_user_id(raw_conditions))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_user_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_user_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_user_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_mapped_scope_nested_filter(
        self, f: MappedScopeNestedFilterDTO
    ) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if f.scope_type is not None:
            condition = self.convert_string_filter(
                f.scope_type,
                contains_factory=RoleConditions.by_scope_type_match.contains,
                equals_factory=RoleConditions.by_scope_type_match.equals,
                starts_with_factory=RoleConditions.by_scope_type_match.starts_with,
                ends_with_factory=RoleConditions.by_scope_type_match.ends_with,
                in_factory=RoleConditions.by_scope_type_match.in_,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if f.scope_id is not None:
            condition = self.convert_uuid_filter(
                f.scope_id,
                equals_factory=RoleConditions.by_scope_id_equals,
                in_factory=RoleConditions.by_scope_id_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        conditions: list[QueryCondition] = []
        if raw_conditions:
            conditions.append(RoleConditions.by_mapped_scope(raw_conditions))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_mapped_scope_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_mapped_scope_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_mapped_scope_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_role_orders_gql(orders: list[RoleOrderByDTO]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "name":
                result.append(RoleOrders.name(ascending))
            elif o.field == "created_at":
                result.append(RoleOrders.created_at(ascending))
            elif o.field == "updated_at":
                result.append(RoleOrders.updated_at(ascending))
        return result

    def _convert_role_nested_filter(self, f: RoleNestedFilterDTO) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if f.name is not None:
            condition = self.convert_string_filter(
                f.name,
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
                starts_with_factory=RoleConditions.by_name_starts_with,
                ends_with_factory=RoleConditions.by_name_ends_with,
                in_factory=RoleConditions.by_name_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if f.source is not None:
            src = f.source
            if src.equals is not None:
                raw_conditions.append(
                    RoleConditions.by_source_equals(InternalRoleSource(src.equals))
                )
            if src.in_ is not None and src.in_:
                raw_conditions.append(
                    RoleConditions.by_sources([InternalRoleSource(s) for s in src.in_])
                )
            if src.not_equals is not None:
                raw_conditions.append(
                    RoleConditions.by_source_not_equals(InternalRoleSource(src.not_equals))
                )
            if src.not_in is not None and src.not_in:
                raw_conditions.append(
                    RoleConditions.by_source_not_in([InternalRoleSource(s) for s in src.not_in])
                )
        if f.status is not None:
            st = f.status
            if st.equals is not None:
                raw_conditions.append(
                    RoleConditions.by_status_equals(InternalRoleStatus(st.equals))
                )
            if st.in_ is not None and st.in_:
                raw_conditions.append(
                    RoleConditions.by_statuses([InternalRoleStatus(s) for s in st.in_])
                )
            if st.not_equals is not None:
                raw_conditions.append(
                    RoleConditions.by_status_not_equals(InternalRoleStatus(st.not_equals))
                )
            if st.not_in is not None and st.not_in:
                raw_conditions.append(
                    RoleConditions.by_status_not_in([InternalRoleStatus(s) for s in st.not_in])
                )
        conditions: list[QueryCondition] = []
        if raw_conditions:
            conditions.append(AssignedUserConditions.exists_role_combined(raw_conditions))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_role_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_role_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_role_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_permission_nested_filter(
        self, f: PermissionNestedFilterDTO
    ) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if f.entity_type is not None:
            condition = self.convert_string_filter(
                f.entity_type,
                contains_factory=ScopedPermissionConditions.by_entity_type_match.contains,
                equals_factory=ScopedPermissionConditions.by_entity_type_match.equals,
                starts_with_factory=ScopedPermissionConditions.by_entity_type_match.starts_with,
                ends_with_factory=ScopedPermissionConditions.by_entity_type_match.ends_with,
                in_factory=ScopedPermissionConditions.by_entity_type_match.in_,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if f.permission is not None:
            raw_conditions.extend(
                self._convert_permission_bit_filter(
                    f.permission,
                    equals_factory=ScopedPermissionConditions.by_permission_equals,
                    not_equals_factory=ScopedPermissionConditions.by_permission_not_equals,
                    in_factory=ScopedPermissionConditions.by_permission_in,
                    not_in_factory=ScopedPermissionConditions.by_permission_not_in,
                )
            )
        conditions: list[QueryCondition] = []
        if raw_conditions:
            conditions.append(AssignedUserConditions.exists_permission_combined(raw_conditions))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_permission_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_permission_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_permission_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_assignment_filter(self, f: RoleAssignmentFilterDTO) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.role_id is not None:
            condition = self.convert_uuid_filter(
                f.role_id,
                equals_factory=AssignedUserConditions.by_role_id_equals,
                in_factory=AssignedUserConditions.by_role_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.role is not None:
            conditions.extend(self._convert_role_nested_filter(f.role))
        if f.permission is not None:
            conditions.extend(self._convert_permission_nested_filter(f.permission))
        if f.username is not None:
            condition = self.convert_string_filter(
                f.username,
                contains_factory=AssignedUserConditions.by_username_contains,
                equals_factory=AssignedUserConditions.by_username_equals,
                starts_with_factory=AssignedUserConditions.by_username_starts_with,
                ends_with_factory=AssignedUserConditions.by_username_ends_with,
                in_factory=AssignedUserConditions.by_username_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.email is not None:
            condition = self.convert_string_filter(
                f.email,
                contains_factory=AssignedUserConditions.by_email_contains,
                equals_factory=AssignedUserConditions.by_email_equals,
                starts_with_factory=AssignedUserConditions.by_email_starts_with,
                ends_with_factory=AssignedUserConditions.by_email_ends_with,
                in_factory=AssignedUserConditions.by_email_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_assignment_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_assignment_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_assignment_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_assignment_orders(orders: list[RoleAssignmentOrderByDTO]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "username":
                result.append(AssignedUserOrders.username(ascending))
            elif o.field == "email":
                result.append(AssignedUserOrders.email(ascending))
            elif o.field == "granted_at":
                result.append(AssignedUserOrders.granted_at(ascending))
        return result

    def _build_updater(self, role_id: UUID, input: UpdateRoleInput) -> RoleUpdater:
        name: OptionalState[str] = OptionalState.nop()
        description: TriState[str] = TriState.nop()
        auto_assign: OptionalState[bool] = OptionalState.nop()

        if input.name is not None:
            name = OptionalState.update(input.name)
        if input.description is not SENTINEL:
            if input.description is None:
                description = TriState.nullify()
            else:
                description = TriState.update(str(input.description))
        if input.auto_assign is not None:
            auto_assign = OptionalState.update(input.auto_assign)

        return RoleUpdater(
            role_id=RoleID(role_id), name=name, description=description, auto_assign=auto_assign
        )

    @staticmethod
    def _role_data_to_node(data: RoleData) -> RoleNode:
        return RoleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            auto_assign=data.auto_assign,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
        )

    @staticmethod
    def _role_detail_to_node(data: RoleDetailData) -> RoleNode:
        return RoleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            auto_assign=data.auto_assign,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
        )

    @staticmethod
    def _permission_data_to_node(data: PermissionData) -> PermissionNode:
        return PermissionNode(
            id=data.id,
            role_id=data.role_id,
            entity_type=EntityType(data.entity_type),
            permission=PermissionBitDTO.of(data.permission),
            created_at=data.created_at,
        )

    @staticmethod
    def _assignment_data_to_node(data: AssignedUserData) -> RoleAssignmentNode:
        return RoleAssignmentNode(
            id=data.id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=data.granted_by,
            granted_at=data.granted_at,
        )

    @staticmethod
    def _role_data_to_dto(data: RoleData) -> RoleDTO:
        return RoleDTO(
            id=data.id,
            name=data.name,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
            source=RoleSource(data.source.value),
            status=RoleStatus(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            description=data.description,
        )
