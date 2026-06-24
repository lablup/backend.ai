"""Role preset domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers. Translates v2 DTOs
into Processor actions and converts the action results back into v2 DTOs.
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import (
    OperationType,
    RBACElementType,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO, RBACElementTypeDTO
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetFailureInfo,
    BulkAddRolePermissionPresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
    BulkRolePermissionPresetFailureInfo,
    RolePermissionPresetNode,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetOrderField,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRestoreRolePresetsInput,
    CreateRolePresetInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetBody,
    UpdateRolePresetInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkDeleteRolePresetsPayload,
    BulkPurgeRolePresetsPayload,
    BulkRestoreRolePresetsPayload,
    BulkRolePresetFailureInfo,
    CreateRolePresetPayload,
    RolePresetNode,
    SearchRolePresetsPayload,
    UpdateRolePresetPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.query_types import QueryCondition, QueryOrder
from ai.backend.manager.models.rbac_models.role_permission_preset.conditions import (
    RolePermissionPresetConditions,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.orders import (
    RolePermissionPresetOrders,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.conditions import RolePresetConditions
from ai.backend.manager.models.rbac_models.role_preset.orders import RolePresetOrders
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import (
    BulkCreator,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetCreatorSpec,
    RolePermissionPresetDependentCreatorSpec,
    RolePresetCreatorSpec,
)
from ai.backend.manager.repositories.role_preset.updaters import (
    RolePresetDeletedFlagUpdaterSpec,
    RolePresetUpdaterSpec,
)
from ai.backend.manager.services.role_preset.actions.bulk_add_permissions import (
    BulkAddRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_purge import (
    BulkPurgeRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_remove_permissions import (
    BulkRemoveRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.create import CreateRolePresetAction
from ai.backend.manager.services.role_preset.actions.delete import BulkDeleteRolePresetsAction
from ai.backend.manager.services.role_preset.actions.get import GetRolePresetAction
from ai.backend.manager.services.role_preset.actions.restore import BulkRestoreRolePresetsAction
from ai.backend.manager.services.role_preset.actions.search import SearchRolePresetsAction
from ai.backend.manager.services.role_preset.actions.search_permission_presets import (
    SearchRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.update import UpdateRolePresetAction
from ai.backend.manager.types import OptionalState


def _role_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RolePresetOrders.created_at(ascending=False),
        backward_order=RolePresetOrders.created_at(ascending=True),
        forward_condition_factory=RolePresetConditions.by_cursor_forward,
        backward_condition_factory=RolePresetConditions.by_cursor_backward,
        tiebreaker_order=RolePresetRow.id.asc(),
    )


def _role_permission_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RolePermissionPresetOrders.id(ascending=False),
        backward_order=RolePermissionPresetOrders.id(ascending=True),
        forward_condition_factory=RolePermissionPresetConditions.by_cursor_forward,
        backward_condition_factory=RolePermissionPresetConditions.by_cursor_backward,
        tiebreaker_order=RolePermissionPresetRow.id.asc(),
    )


class RolePresetAdapter(BaseAdapter):
    """Adapter for role preset domain operations."""

    async def create(self, input: CreateRolePresetInput) -> CreateRolePresetPayload:
        """Create a new role preset."""
        creator_spec = RolePresetCreatorSpec(
            name=input.name,
            scope_type=RBACElementType(input.scope_type.value).to_scope_type(),
            auto_assign=input.auto_assign,
        )
        permission_creator_specs = [
            RolePermissionPresetDependentCreatorSpec(
                entity_type=RBACElementType(entry.entity_type.value).to_entity_type(),
                operation=OperationType(entry.operation.value),
            )
            for entry in input.permissions
        ]
        result = await self._processors.role_preset.create.wait_for_complete(
            CreateRolePresetAction(
                creator_spec=creator_spec,
                permission_creator_specs=permission_creator_specs,
            )
        )
        return CreateRolePresetPayload(role_preset=self._data_to_node(result.preset))

    async def get(self, role_preset_id: RolePresetID) -> RolePresetNode:
        """Get a single role preset by ID."""
        result = await self._processors.role_preset.get.wait_for_complete(
            GetRolePresetAction(preset_id=role_preset_id)
        )
        return self._data_to_node(result.preset)

    async def search(self, input: SearchRolePresetsInput) -> SearchRolePresetsPayload:
        """Search role presets with filtering and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        # Soft-deleted rows are excluded unless the caller explicitly sets the
        # top-level ``deleted`` filter.
        base_conditions: list[QueryCondition] = []
        if input.filter is None or input.filter.deleted is None:
            base_conditions.append(RolePresetConditions.by_deleted(False))
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        result = await self._processors.role_preset.search.wait_for_complete(
            SearchRolePresetsAction(querier=querier)
        )
        return SearchRolePresetsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(self, input: UpdateRolePresetInput) -> UpdateRolePresetPayload:
        """Update an existing role preset's metadata."""
        spec = RolePresetUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            auto_assign=(
                OptionalState.update(input.auto_assign)
                if input.auto_assign is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[RolePresetRow] = Updater(spec=spec, pk_value=input.role_preset_id)
        result = await self._processors.role_preset.update.wait_for_complete(
            UpdateRolePresetAction(updater=updater)
        )
        return UpdateRolePresetPayload(role_preset=self._data_to_node(result.preset))

    async def update_from_body(
        self, role_preset_id: RolePresetID, body: UpdateRolePresetBody
    ) -> UpdateRolePresetPayload:
        """Update a role preset whose ID is carried separately from the body.

        Used by the REST handler, where the preset ID comes from the URL path
        while the body only carries the mutable metadata.
        """
        return await self.update(
            UpdateRolePresetInput(
                role_preset_id=role_preset_id,
                name=body.name,
                auto_assign=body.auto_assign,
            )
        )

    async def bulk_delete(self, input: BulkDeleteRolePresetsInput) -> BulkDeleteRolePresetsPayload:
        """Bulk-soft-delete role presets."""
        updaters: list[Updater[RolePresetRow]] = [
            Updater(spec=RolePresetDeletedFlagUpdaterSpec(deleted=True), pk_value=preset_id)
            for preset_id in input.role_preset_ids
        ]
        result = await self._processors.role_preset.bulk_delete.wait_for_complete(
            BulkDeleteRolePresetsAction(updaters=updaters)
        )
        return BulkDeleteRolePresetsPayload(
            items=[self._data_to_node(d) for d in result.successes],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=input.role_preset_ids[f.index],
                    message=str(f.exception),
                )
                for f in result.failures
            ],
        )

    async def bulk_restore(
        self, input: BulkRestoreRolePresetsInput
    ) -> BulkRestoreRolePresetsPayload:
        """Bulk-restore soft-deleted role presets."""
        updaters: list[Updater[RolePresetRow]] = [
            Updater(spec=RolePresetDeletedFlagUpdaterSpec(deleted=False), pk_value=preset_id)
            for preset_id in input.role_preset_ids
        ]
        result = await self._processors.role_preset.bulk_restore.wait_for_complete(
            BulkRestoreRolePresetsAction(updaters=updaters)
        )
        return BulkRestoreRolePresetsPayload(
            items=[self._data_to_node(d) for d in result.successes],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=input.role_preset_ids[f.index],
                    message=str(f.exception),
                )
                for f in result.failures
            ],
        )

    async def bulk_purge(self, input: BulkPurgeRolePresetsInput) -> BulkPurgeRolePresetsPayload:
        """Bulk-hard-delete role presets."""
        result = await self._processors.role_preset.bulk_purge.wait_for_complete(
            BulkPurgeRolePresetsAction(ids=input.role_preset_ids)
        )
        purge_result = result.result
        return BulkPurgeRolePresetsPayload(
            items=[self._data_to_node(d) for d in purge_result.successes],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=input.role_preset_ids[f.index],
                    message=str(f.exception),
                )
                for f in purge_result.failures
            ],
        )

    async def search_permission_presets(
        self,
        role_preset_id: RolePresetID,
        input: SearchRolePermissionPresetsInput,
    ) -> SearchRolePermissionPresetsPayload:
        """Search the permission entries belonging to a single role preset.

        Backs the ``permission_presets`` field resolver on ``RolePresetGQL``. The
        parent preset id is always enforced as a base condition, so caller-supplied
        filters can only narrow within that preset, never widen across presets.
        """
        conditions = self._convert_permission_filter(input.filter) if input.filter else []
        orders = self._convert_permission_orders(input.order) if input.order else []
        base_conditions: list[QueryCondition] = [
            RolePermissionPresetConditions.by_role_preset_id_equals(role_preset_id)
        ]
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_permission_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        result = await self._processors.role_preset.search_permission_presets.wait_for_complete(
            SearchRolePermissionPresetsAction(querier=querier)
        )
        return SearchRolePermissionPresetsPayload(
            items=[self._permission_data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def bulk_add_permissions(
        self,
        role_preset_id: RolePresetID,
        input: BulkAddRolePermissionPresetsInput,
    ) -> BulkAddRolePermissionPresetsPayload:
        """Bulk-add permission entries to an existing role preset."""
        bulk_creator: BulkCreator[RolePermissionPresetRow] = BulkCreator(
            specs=[
                RolePermissionPresetCreatorSpec(
                    role_preset_id=role_preset_id,
                    entity_type=RBACElementType(entry.entity_type.value).to_entity_type(),
                    operation=OperationType(entry.operation.value),
                )
                for entry in input.permissions
            ]
        )
        result = await self._processors.role_preset.bulk_add_permissions.wait_for_complete(
            BulkAddRolePermissionPresetsAction(bulk_creator=bulk_creator)
        )
        return BulkAddRolePermissionPresetsPayload(
            items=[self._permission_data_to_node(d) for d in result.successes],
            failed=[
                BulkAddRolePermissionPresetFailureInfo(
                    entity_type=input.permissions[f.index].entity_type,
                    operation=input.permissions[f.index].operation,
                    message=str(f.exception),
                )
                for f in result.failures
            ],
        )

    async def bulk_remove_permissions(
        self, input: BulkRemoveRolePermissionPresetsInput
    ) -> BulkRemoveRolePermissionPresetsPayload:
        """Bulk-remove permission entries from a role preset."""
        result = await self._processors.role_preset.bulk_remove_permissions.wait_for_complete(
            BulkRemoveRolePermissionPresetsAction(ids=input.permission_preset_ids)
        )
        return BulkRemoveRolePermissionPresetsPayload(
            items=[self._permission_data_to_node(d) for d in result.successes],
            failed=[
                BulkRolePermissionPresetFailureInfo(
                    permission_preset_id=input.permission_preset_ids[f.index],
                    message=str(f.exception),
                )
                for f in result.failures
            ],
        )

    def _convert_filter(self, filter_: RolePresetFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.name is not None:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=RolePresetConditions.by_name_contains,
                equals_factory=RolePresetConditions.by_name_equals,
                starts_with_factory=RolePresetConditions.by_name_starts_with,
                ends_with_factory=RolePresetConditions.by_name_ends_with,
                in_factory=RolePresetConditions.by_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.scope_type is not None:
            conditions.append(
                RolePresetConditions.by_scope_type(
                    RBACElementType(filter_.scope_type.value).to_scope_type()
                )
            )
        if filter_.auto_assign is not None:
            conditions.append(RolePresetConditions.by_auto_assign(filter_.auto_assign))
        if filter_.deleted is not None:
            conditions.append(RolePresetConditions.by_deleted(filter_.deleted))
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter_.NOT:
                not_conds.extend(self._convert_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    def _convert_orders(self, orders: list[RolePresetOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case RolePresetOrderField.NAME:
                    result.append(RolePresetOrders.name(ascending))
                case RolePresetOrderField.SCOPE_TYPE:
                    result.append(RolePresetOrders.scope_type(ascending))
                case RolePresetOrderField.CREATED_AT:
                    result.append(RolePresetOrders.created_at(ascending))
                case RolePresetOrderField.UPDATED_AT:
                    result.append(RolePresetOrders.updated_at(ascending))
        return result

    def _convert_permission_filter(
        self, filter_: RolePermissionPresetFilter
    ) -> list[QueryCondition]:
        # ``role_preset_id`` is intentionally ignored here: the parent preset scope
        # is enforced as a base condition by the caller, so it cannot be widened.
        conditions: list[QueryCondition] = []
        if filter_.entity_type is not None:
            f = filter_.entity_type
            if f.equals is not None:
                conditions.append(
                    RolePermissionPresetConditions.by_entity_type_equals(
                        RBACElementType(f.equals.value).to_entity_type()
                    )
                )
            if f.not_equals is not None:
                conditions.append(
                    RolePermissionPresetConditions.by_entity_type_not_equals(
                        RBACElementType(f.not_equals.value).to_entity_type()
                    )
                )
            if f.in_:
                conditions.append(
                    RolePermissionPresetConditions.by_entity_type_in([
                        RBACElementType(v.value).to_entity_type() for v in f.in_
                    ])
                )
            if f.not_in:
                conditions.append(
                    RolePermissionPresetConditions.by_entity_type_not_in([
                        RBACElementType(v.value).to_entity_type() for v in f.not_in
                    ])
                )
        if filter_.operation is not None:
            f_op = filter_.operation
            if f_op.equals is not None:
                conditions.append(
                    RolePermissionPresetConditions.by_operation_equals(
                        OperationType(f_op.equals.value)
                    )
                )
            if f_op.not_equals is not None:
                conditions.append(
                    RolePermissionPresetConditions.by_operation_not_equals(
                        OperationType(f_op.not_equals.value)
                    )
                )
            if f_op.in_:
                conditions.append(
                    RolePermissionPresetConditions.by_operation_in([
                        OperationType(v.value) for v in f_op.in_
                    ])
                )
            if f_op.not_in:
                conditions.append(
                    RolePermissionPresetConditions.by_operation_not_in([
                        OperationType(v.value) for v in f_op.not_in
                    ])
                )
        if filter_.created_at is not None:
            cond = filter_.created_at.build_query_condition(
                before_factory=RolePermissionPresetConditions.by_created_at_before,
                after_factory=RolePermissionPresetConditions.by_created_at_after,
                equals_factory=RolePermissionPresetConditions.by_created_at_equals,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_permission_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_permission_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter_.NOT:
                not_conds.extend(self._convert_permission_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    def _convert_permission_orders(
        self, orders: list[RolePermissionPresetOrder]
    ) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case RolePermissionPresetOrderField.ENTITY_TYPE:
                    result.append(RolePermissionPresetOrders.entity_type(ascending))
                case RolePermissionPresetOrderField.OPERATION:
                    result.append(RolePermissionPresetOrders.operation(ascending))
                case RolePermissionPresetOrderField.CREATED_AT:
                    result.append(RolePermissionPresetOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RolePresetData) -> RolePresetNode:
        return RolePresetNode(
            id=data.id,
            name=data.name,
            scope_type=RBACElementTypeDTO(data.scope_type.value),
            auto_assign=data.auto_assign,
            deleted=data.deleted,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _permission_data_to_node(data: RolePermissionPresetData) -> RolePermissionPresetNode:
        return RolePermissionPresetNode(
            id=data.id,
            role_preset_id=data.role_preset_id,
            entity_type=RBACElementTypeDTO(data.entity_type.value),
            operation=OperationTypeDTO(data.operation.value),
            created_at=data.created_at,
        )
