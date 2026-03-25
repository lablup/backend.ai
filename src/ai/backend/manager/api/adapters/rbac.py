"""RBAC domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from functools import lru_cache
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.permission.types import OperationType as InternalOperationType
from ai.backend.common.data.permission.types import RBACElementType
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
    AssociationScopesEntitiesNode,
    BulkAssignRoleFailureInfo,
    BulkAssignRoleResultPayload,
    BulkRevokeRoleFailureInfo,
    BulkRevokeRoleResultPayload,
    CreateRoleInput,
    CreateRolePayload,
    DeleteRolePayload,
    EntityNode,
    PermissionNode,
    PurgeRolePayload,
    RoleAssignmentNode,
    RoleNode,
    UpdateRoleInput,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac import (
    DeletePermissionPayload as DeletePermissionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchEntitiesGQLInput,
    AdminSearchPermissionsGQLInput,
    AdminSearchRoleAssignmentsGQLInput,
    AdminSearchRolesGQLInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput as AssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAssignRoleInput as BulkAssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRevokeRoleInput as BulkRevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreatePermissionInput as CreatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityFilter as EntityFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityOrderBy as EntityOrderByDTO,
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
from ai.backend.common.dto.manager.v2.rbac.types import (
    OperationTypeDTO,
    RBACElementTypeDTO,
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OrderDirection as OrderDirectionV2,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    BulkRoleAssignmentResultData,
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
from ai.backend.manager.data.permission.types import RoleSource as InternalRoleSource
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.conditions import (
    AssignedUserConditions,
    EntityScopeConditions,
    PermissionConditions,
    RoleConditions,
    ScopedPermissionConditions,
)
from ai.backend.manager.models.rbac_models.orders import (
    AssignedUserOrders,
    EntityScopeOrders,
    RoleOrders,
    ScopedPermissionOrders,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    NoPagination,
    OffsetPagination,
    Purger,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
    RoleCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.updaters import (
    PermissionUpdaterSpec,
    RoleUpdaterSpec,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import AssignRoleAction
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_revoke_role import (
    BulkRevokeRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.delete_role import DeleteRoleAction
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.revoke_role import RevokeRoleAction
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
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import UpdateRoleAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

# ------------------------------------------------------------------ pagination specs


@lru_cache(maxsize=1)
def _permission_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScopedPermissionOrders.id(ascending=False),
        backward_order=ScopedPermissionOrders.id(ascending=True),
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


@lru_cache(maxsize=1)
def _entity_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=EntityScopeOrders.id(ascending=False),
        backward_order=EntityScopeOrders.id(ascending=True),
        forward_condition_factory=EntityScopeConditions.by_cursor_forward,
        backward_condition_factory=EntityScopeConditions.by_cursor_backward,
        tiebreaker_order=AssociationScopesEntitiesRow.id.asc(),
    )


class RBACAdapter(BaseAdapter):
    """Adapter for RBAC domain operations.

    Exposes: create, admin_search, get, update, delete, purge.
    assign/revoke/bulk operations require specialized inputs not
    yet bridged through this adapter.
    """

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_roles_by_ids(self, role_ids: Sequence[UUID]) -> list[RoleNode | None]:
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
            await self._processors.permission_controller.search_roles.wait_for_complete(
                SearchRolesAction(querier=querier)
            )
        )
        role_map: dict[UUID, RoleNode] = {
            data.id: self._role_data_to_node(data) for data in action_result.result.items
        }
        return [role_map.get(role_id) for role_id in role_ids]

    async def batch_load_permissions_by_ids(
        self, permission_ids: Sequence[UUID]
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
            await self._processors.permission_controller.search_permissions.wait_for_complete(
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
        action_result: SearchUsersAssignedToRoleActionResult = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
        )
        assignment_map: dict[UUID, RoleAssignmentNode] = {
            data.id: self._assignment_data_to_node(data) for data in action_result.result.items
        }
        return [assignment_map.get(aid) for aid in assignment_ids]

    async def batch_load_entities_by_type_and_ids(
        self, object_ids: Sequence[ObjectId]
    ) -> list[EntityNode | None]:
        """Batch load entities by ObjectId (type + id) for DataLoader use.

        Returns EntityNode DTOs in the same order as the input object_ids list.
        """
        if not object_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[EntityScopeConditions.by_object_ids(object_ids)],
        )
        action_result: SearchEntitiesActionResult = (
            await self._processors.permission_controller.search_entities.wait_for_complete(
                SearchEntitiesAction(querier=querier)
            )
        )
        entity_map: dict[ObjectId, EntityNode] = {
            ObjectId(entity_type=e.entity_type, entity_id=e.entity_id): self._entity_data_to_node(e)
            for e in action_result.result.items
        }
        return [entity_map.get(oid) for oid in object_ids]

    async def batch_load_element_associations_by_ids(
        self, association_ids: Sequence[UUID]
    ) -> list[AssociationScopesEntitiesNode | None]:
        """Batch load element associations by ID for DataLoader use.

        Returns AssociationScopesEntitiesNode DTOs in the same order as the input ids list.
        """
        if not association_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[EntityScopeConditions.by_ids(association_ids)],
        )
        action_result: SearchElementAssociationsActionResult = await self._processors.permission_controller.search_element_associations.wait_for_complete(
            SearchElementAssociationsAction(querier=querier)
        )
        association_map: dict[UUID, AssociationScopesEntitiesNode] = {
            data.id: self._association_data_to_node(data) for data in action_result.result.items
        }
        return [association_map.get(aid) for aid in association_ids]

    async def batch_load_permissions_by_role_ids(
        self, role_ids: Sequence[UUID]
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
            await self._processors.permission_controller.search_permissions.wait_for_complete(
                SearchPermissionsAction(querier=querier)
            )
        )
        result_map: dict[UUID, list[PermissionNode]] = defaultdict(list)
        for item in action_result.result.items:
            result_map[item.role_id].append(self._permission_data_to_node(item))
        return [result_map.get(role_id, []) for role_id in role_ids]

    async def batch_load_role_assignments_by_user_ids(
        self, user_ids: Sequence[UUID]
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
        action_result: SearchUsersAssignedToRoleActionResult = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
        )
        result_map: dict[UUID, list[RoleAssignmentNode]] = defaultdict(list)
        for item in action_result.result.items:
            result_map[item.user_id].append(self._assignment_data_to_node(item))
        return [result_map.get(user_id, []) for user_id in user_ids]

    async def batch_load_assignments_by_role_ids(
        self, role_ids: Sequence[UUID]
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
        action_result: SearchUsersAssignedToRoleActionResult = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
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
        action_result: SearchUsersAssignedToRoleActionResult = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
        )
        result_map: dict[tuple[uuid.UUID, uuid.UUID], RoleAssignmentNode] = {
            (item.role_id, item.user_id): self._assignment_data_to_node(item)
            for item in action_result.result.items
        }
        return [result_map.get(pair) for pair in pairs]

    # ------------------------------------------------------------------ create

    async def create(self, input: CreateRoleInput) -> CreateRolePayload:
        """Create a new role."""
        creator = Creator(
            spec=RoleCreatorSpec(
                name=input.name,
                source=InternalRoleSource(input.source.value),
                status=InternalRoleStatus.ACTIVE,
                description=input.description,
            )
        )
        action_result = await self._processors.permission_controller.create_role.wait_for_complete(
            CreateRoleAction(creator=creator)
        )
        return CreateRolePayload(role=self._role_data_to_node(action_result.data))

    # ------------------------------------------------------------------ search

    async def admin_search(self, input: SearchRolesRequest) -> SearchRolesResponse:
        """Search roles with no scope restriction (admin only)."""
        querier = self._build_search_querier(input)
        action_result = await self._processors.permission_controller.search_roles.wait_for_complete(
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
            await self._processors.permission_controller.search_permissions.wait_for_complete(
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
        input: AdminSearchRolesGQLInput,
        base_conditions: Sequence[QueryCondition] | None = None,
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
            base_conditions=base_conditions,
        )
        action_result: SearchRolesActionResult = (
            await self._processors.permission_controller.search_roles.wait_for_complete(
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

    async def admin_search_role_assignments_gql(
        self,
        input: AdminSearchRoleAssignmentsGQLInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search role assignments with cursor/offset pagination."""
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
        action_result: SearchUsersAssignedToRoleActionResult = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
        )
        raw = action_result.result
        return SearchResult(
            items=[self._assignment_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def admin_search_entities_gql(
        self,
        input: AdminSearchEntitiesGQLInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[AssociationScopesEntitiesNode]:
        """Search entity associations with cursor/offset pagination."""
        conditions = self._convert_entity_filter(input.filter) if input.filter else []
        orders = self._convert_entity_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_entity_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        action_result: SearchElementAssociationsActionResult = await self._processors.permission_controller.search_element_associations.wait_for_complete(
            SearchElementAssociationsAction(querier=querier)
        )
        raw = action_result.result
        return SearchResult(
            items=[self._association_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    # ------------------------------------------------------------------ get

    async def get(self, role_id: UUID) -> RoleNode:
        """Get a role by ID."""
        action_result = (
            await self._processors.permission_controller.get_role_detail.wait_for_complete(
                GetRoleDetailAction(role_id=role_id)
            )
        )
        return self._role_detail_to_node(action_result.role)

    # ------------------------------------------------------------------ update

    async def update(self, role_id: UUID, input: UpdateRoleInput) -> UpdateRolePayload:
        """Update an existing role."""
        updater = self._build_updater(role_id, input)
        action_result = await self._processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(updater=updater)
        )
        return UpdateRolePayload(role=self._role_data_to_node(action_result.data))

    # ------------------------------------------------------------------ delete

    async def delete(self, role_id: UUID) -> DeleteRolePayload:
        """Soft-delete a role (marks status as DELETED)."""
        spec = RoleUpdaterSpec(status=OptionalState.update(InternalRoleStatus.DELETED))
        updater = Updater(spec=spec, pk_value=role_id)
        action_result = await self._processors.permission_controller.delete_role.wait_for_complete(
            DeleteRoleAction(updater=updater)
        )
        return DeleteRolePayload(id=action_result.data.id)

    # ------------------------------------------------------------------ purge

    async def purge(self, role_id: UUID) -> PurgeRolePayload:
        """Hard-delete a role from the database."""
        purger: Purger[RoleRow] = Purger(row_class=RoleRow, pk_value=role_id)
        action_result = await self._processors.permission_controller.purge_role.wait_for_complete(
            PurgeRoleAction(purger=purger)
        )
        return PurgeRolePayload(id=action_result.data.id)

    # ------------------------------------------------------------------ delete_permission

    async def delete_permission(self, permission_id: UUID) -> DeletePermissionPayloadDTO:
        """Hard-delete a scoped permission."""
        purger: Purger[PermissionRow] = Purger(row_class=PermissionRow, pk_value=permission_id)
        await self._processors.permission_controller.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=purger)
        )
        return DeletePermissionPayloadDTO(id=permission_id)

    # ------------------------------------------------------------------ create_permission / update_permission

    async def create_permission(self, input: CreatePermissionInputDTO) -> PermissionNode:
        """Create a new scoped permission."""
        creator: Creator[PermissionRow] = Creator(
            spec=PermissionCreatorSpec(
                role_id=input.role_id,
                scope_type=RBACElementType(input.scope_type),
                scope_id=input.scope_id,
                entity_type=RBACElementType(input.entity_type),
                operation=InternalOperationType(input.operation),
            )
        )
        action_result = (
            await self._processors.permission_controller.create_permission.wait_for_complete(
                CreatePermissionAction(creator=creator)
            )
        )
        return self._permission_data_to_node(action_result.data)

    async def update_permission(self, input: UpdatePermissionInputDTO) -> PermissionNode:
        """Update an existing scoped permission."""
        spec = PermissionUpdaterSpec(
            scope_type=(
                OptionalState.update(RBACElementType(input.scope_type))
                if input.scope_type is not None
                else OptionalState.nop()
            ),
            scope_id=(
                OptionalState.update(input.scope_id)
                if input.scope_id is not None
                else OptionalState.nop()
            ),
            entity_type=(
                OptionalState.update(RBACElementType(input.entity_type))
                if input.entity_type is not None
                else OptionalState.nop()
            ),
            operation=(
                OptionalState.update(InternalOperationType(input.operation))
                if input.operation is not None
                else OptionalState.nop()
            ),
        )
        action_result = (
            await self._processors.permission_controller.update_permission.wait_for_complete(
                UpdatePermissionAction(updater=Updater(spec=spec, pk_value=input.id))
            )
        )
        return self._permission_data_to_node(action_result.data)

    # ------------------------------------------------------------------ assign_role / revoke_role

    async def assign_role(self, input: AssignRoleInputDTO) -> RoleAssignmentNode:
        """Assign a role to a user."""
        action_result = await self._processors.permission_controller.assign_role.wait_for_complete(
            AssignRoleAction(
                input=UserRoleAssignmentInput(user_id=input.user_id, role_id=input.role_id)
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
        action_result = await self._processors.permission_controller.revoke_role.wait_for_complete(
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
        specs = [UserRoleCreatorSpec(user_id=uid, role_id=input.role_id) for uid in input.user_ids]
        action_result = (
            await self._processors.permission_controller.bulk_assign_role.wait_for_complete(
                BulkAssignRoleAction(bulk_creator=BulkCreator(specs=specs))
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
            failed=[
                BulkAssignRoleFailureInfo(user_id=f.user_id, message=f.message)
                for f in result.failures
            ],
        )

    async def bulk_revoke_role(self, input: BulkRevokeRoleInputDTO) -> BulkRevokeRoleResultPayload:
        """Bulk-revoke a role from multiple users."""
        action_result = (
            await self._processors.permission_controller.bulk_revoke_role.wait_for_complete(
                BulkRevokeRoleAction(
                    input=BulkUserRoleRevocationInput(
                        role_id=input.role_id, user_ids=input.user_ids
                    )
                )
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

    def _convert_permission_filter(self, f: PermissionFilterDTO) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.role_id is not None:
            conditions.append(ScopedPermissionConditions.by_role_id(f.role_id))
        if f.scope_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_scope_type(RBACElementType(f.scope_type))
            )
        if f.entity_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_entity_type(RBACElementType(f.entity_type))
            )
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
        if f.scope_id is not None:
            raw_conditions.append(PermissionConditions.by_scope_id(f.scope_id))
        if f.scope_type is not None:
            scope_type = RBACElementType(f.scope_type).to_scope_type()
            raw_conditions.append(PermissionConditions.by_scope_types([scope_type]))
        if f.entity_type is not None:
            entity_type = RBACElementType(f.entity_type).to_entity_type()
            raw_conditions.append(PermissionConditions.by_entity_types([entity_type]))
        if f.operation is not None:
            operation = InternalOperationType(f.operation)
            raw_conditions.append(PermissionConditions.by_operations([operation]))
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
            conditions.append(AssignedUserConditions.by_role_id(f.role_id))
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

    def _convert_entity_filter(self, f: EntityFilterDTO) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.entity_type is not None:
            conditions.append(EntityScopeConditions.by_entity_type(RBACElementType(f.entity_type)))
        if f.entity_id is not None:
            condition = self.convert_string_filter(
                f.entity_id,
                contains_factory=EntityScopeConditions.by_entity_id_contains,
                equals_factory=EntityScopeConditions.by_entity_id_equals,
                starts_with_factory=EntityScopeConditions.by_entity_id_starts_with,
                ends_with_factory=EntityScopeConditions.by_entity_id_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_entity_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_entity_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_entity_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_entity_orders(orders: list[EntityOrderByDTO]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "entity_type":
                result.append(EntityScopeOrders.entity_type(ascending))
            elif o.field == "registered_at":
                result.append(EntityScopeOrders.registered_at(ascending))
        return result

    def _build_updater(self, role_id: UUID, input: UpdateRoleInput) -> Updater[RoleRow]:
        name: OptionalState[str] = OptionalState.nop()
        status: OptionalState[InternalRoleStatus] = OptionalState.nop()
        description: TriState[str] = TriState.nop()

        if input.name is not None:
            name = OptionalState.update(input.name)
        if input.status is not None:
            status = OptionalState.update(InternalRoleStatus(input.status.value))
        if input.description is not SENTINEL:
            if input.description is None:
                description = TriState.nullify()
            else:
                description = TriState.update(str(input.description))

        spec = RoleUpdaterSpec(name=name, status=status, description=description)
        return Updater(spec=spec, pk_value=role_id)

    @staticmethod
    def _role_data_to_node(data: RoleData) -> RoleNode:
        return RoleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
        )

    @staticmethod
    def _role_detail_to_node(data: RoleDetailData) -> RoleNode:
        return RoleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
        )

    @staticmethod
    def _permission_data_to_node(data: PermissionData) -> PermissionNode:
        return PermissionNode(
            id=data.id,
            role_id=data.role_id,
            scope_type=RBACElementTypeDTO(data.scope_type.to_element().value),
            scope_id=data.scope_id,
            entity_type=RBACElementTypeDTO(data.entity_type.to_element().value),
            operation=OperationTypeDTO(data.operation.value),
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
    def _entity_data_to_node(data: EntityData) -> EntityNode:
        return EntityNode(
            entity_type=data.entity_type.value,
            entity_id=data.entity_id,
        )

    @staticmethod
    def _association_data_to_node(
        data: AssociationScopesEntitiesData,
    ) -> AssociationScopesEntitiesNode:
        return AssociationScopesEntitiesNode(
            id=data.id,
            scope_type=data.scope_id.scope_type.value,
            scope_id=data.scope_id.scope_id,
            entity_type=data.object_id.entity_type.value,
            entity_id=data.object_id.entity_id,
            relation_type=data.relation_type.value,
            registered_at=data.registered_at,
        )

    @staticmethod
    def _role_data_to_dto(data: RoleData) -> RoleDTO:
        return RoleDTO(
            id=data.id,
            name=data.name,
            source=RoleSource(data.source.value),
            status=RoleStatus(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            description=data.description,
        )
