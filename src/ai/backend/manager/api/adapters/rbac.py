"""RBAC domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
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
    CreateRoleInput,
    CreateRolePayload,
    DeleteRolePayload,
    PurgeRolePayload,
    RoleNode,
    UpdateRoleInput,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OperationType as OperationTypeDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    PermissionSummary,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleSource as RoleSourceV2,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleStatus as RoleStatusV2,
)
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.data.permission.status import RoleStatus as InternalRoleStatus
from ai.backend.manager.data.permission.types import RoleSource as InternalRoleSource
from ai.backend.manager.models.rbac_models.conditions import RoleConditions
from ai.backend.manager.models.rbac_models.orders import RoleOrders
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    Purger,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.delete_role import DeleteRoleAction
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.search_roles import SearchRolesAction
from ai.backend.manager.services.permission_contoller.actions.update_role import UpdateRoleAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


class RBACAdapter(BaseAdapter):
    """Adapter for RBAC domain operations.

    Exposes: create, admin_search, get, update, delete, purge.
    assign/revoke/bulk operations require specialized inputs not
    yet bridged through this adapter.
    """

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

    # ------------------------------------------------------------------ helpers

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
            source=RoleSourceV2(data.source.value),
            status=RoleStatusV2(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            permissions=[],
        )

    @staticmethod
    def _role_detail_to_node(data: RoleDetailData) -> RoleNode:
        return RoleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceV2(data.source.value),
            status=RoleStatusV2(data.status.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            permissions=[
                PermissionSummary(
                    entity_type=p.object_id.entity_type,
                    operation=OperationTypeDTO(p.operation.value),
                )
                for p in data.object_permissions
            ],
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
