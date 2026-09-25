"""Role preset domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers. Translates v2 DTOs
into Processor actions and converts the action results back into v2 DTOs.
"""

from __future__ import annotations

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, PermissionBitFilter
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
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
from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField, RolePresetUsage
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.searchable_fields import (
    RolePermissionPresetSearchableFields,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetCreator
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.rbac_models.role_preset.searchers import (
    RolePermissionPresetSearcher,
    RolePresetSearcher,
)
from ai.backend.manager.models.rbac_models.role_preset.updaters import RolePresetUpdater
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher
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
from ai.backend.manager.services.role_preset.processors import RolePresetProcessors
from ai.backend.manager.types import OptionalState


def _role_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RolePresetSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=RolePresetRow.id,
    )


def _role_permission_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RolePermissionPresetSearchableFields.own.id.order.apply(ascending=False),
        cursor_column=RolePermissionPresetRow.id,
    )


class RolePresetAdapter(BaseAdapter):
    """Adapter for role preset domain operations."""

    _role_preset: RolePresetProcessors

    def __init__(self, role_preset: RolePresetProcessors) -> None:
        self._role_preset = role_preset

    async def create(self, input: CreateRolePresetInput) -> CreateRolePresetPayload:
        """Create a new role preset."""
        creator = RolePresetCreator(
            name=input.name,
            scope_type=input.scope_type,
            auto_assign=input.auto_assign,
        )
        permission_creators = [
            RolePermissionPresetCreator(
                entity_type=entry.entity_type,
                permission=entry.permission.to_permission(),
            )
            for entry in input.permissions
        ]
        result = await self._role_preset.create.run(
            CreateRolePresetAction(
                creator=creator,
                permission_creators=permission_creators,
            )
        )
        return CreateRolePresetPayload(role_preset=self._data_to_node(result.data))

    async def get(self, role_preset_id: RolePresetID) -> RolePresetNode:
        """Get a single role preset by ID."""
        result = await self._role_preset.get.run(GetRolePresetAction(preset_id=role_preset_id))
        return self._data_to_node(result.data)

    def _usage(self, usage: RolePresetUsage | None) -> list[UsedBy]:
        """The uses the request named, each of which the caller must be able to read."""
        if usage is None or usage.used_by is None:
            return []
        linked = RolePresetSearchableFields.linked.usage
        return [linked.roles.used_by(RoleID(entity_id)) for entity_id in usage.used_by.role or ()]

    async def search(self, input: SearchRolePresetsInput) -> SearchRolePresetsPayload:
        """Search role presets with filtering and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        # Soft-deleted rows are excluded unless the caller explicitly sets the
        # top-level ``deleted`` filter.
        base_conditions: list[QueryCondition] = []
        if input.filter is None or input.filter.deleted is None:
            base_conditions.append(RolePresetSearchableFields.own.deleted.filter.equals(False))
        searcher = self._build_searcher(
            RolePresetSearcher,
            conditions=[*base_conditions, *conditions],
            orders=orders,
            pagination_spec=_role_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._role_preset.search.run(
            SearchRolePresetsAction(
                searcher=GlobalSearcher(used_by=self._usage(input.usage), searcher=searcher)
            )
        )
        return SearchRolePresetsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(self, input: UpdateRolePresetInput) -> UpdateRolePresetPayload:
        """Update an existing role preset's metadata."""
        updater = RolePresetUpdater(
            preset_id=input.role_preset_id,
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            auto_assign=(
                OptionalState.update(input.auto_assign)
                if input.auto_assign is not None
                else OptionalState.nop()
            ),
        )
        result = await self._role_preset.update.run(UpdateRolePresetAction(updater=updater))
        return UpdateRolePresetPayload(role_preset=self._data_to_node(result.data))

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
        result = await self._role_preset.bulk_delete.run(
            BulkDeleteRolePresetsAction(ids=input.role_preset_ids)
        )
        return BulkDeleteRolePresetsPayload(
            items=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=RolePresetID(item.entity_id), message=str(item.error)
                )
                for item in result.items
                if item.error is not None
            ],
        )

    async def bulk_restore(
        self, input: BulkRestoreRolePresetsInput
    ) -> BulkRestoreRolePresetsPayload:
        """Bulk-restore soft-deleted role presets."""
        result = await self._role_preset.bulk_restore.run(
            BulkRestoreRolePresetsAction(ids=input.role_preset_ids)
        )
        return BulkRestoreRolePresetsPayload(
            items=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=RolePresetID(item.entity_id), message=str(item.error)
                )
                for item in result.items
                if item.error is not None
            ],
        )

    async def bulk_purge(self, input: BulkPurgeRolePresetsInput) -> BulkPurgeRolePresetsPayload:
        """Bulk-hard-delete role presets."""
        result = await self._role_preset.bulk_purge.run(
            BulkPurgeRolePresetsAction(ids=input.role_preset_ids)
        )
        return BulkPurgeRolePresetsPayload(
            items=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                BulkRolePresetFailureInfo(
                    role_preset_id=RolePresetID(item.entity_id), message=str(item.error)
                )
                for item in result.items
                if item.error is not None
            ],
        )

    async def search_permission_presets(
        self,
        role_preset_id: RolePresetID,
        input: SearchRolePermissionPresetsInput,
    ) -> SearchRolePermissionPresetsPayload:
        """Search the permission entries belonging to a single role preset.

        Backs the ``permission_presets`` field resolver on ``RolePresetGQL``. The action
        names the preset, so a caller-supplied filter can only narrow within it.
        """
        conditions = self._convert_permission_filter(input.filter) if input.filter else []
        orders = self._convert_permission_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            RolePermissionPresetSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_permission_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._role_preset.search_permission_presets.run(
            SearchRolePermissionPresetsAction(preset_ids=[role_preset_id], searcher=searcher)
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
        creators = [
            RolePermissionPresetCreator(
                entity_type=entry.entity_type,
                permission=entry.permission.to_permission(),
            )
            for entry in input.permissions
        ]
        result = await self._role_preset.bulk_add_permissions.run(
            BulkAddRolePermissionPresetsAction(preset_id=role_preset_id, creators=creators)
        )
        # The write is atomic: every entry landed, or the run raised and nothing did.
        return BulkAddRolePermissionPresetsPayload(
            items=[self._permission_data_to_node(d) for d in result.items],
            failed=[],
        )

    async def bulk_remove_permissions(
        self, input: BulkRemoveRolePermissionPresetsInput
    ) -> BulkRemoveRolePermissionPresetsPayload:
        """Bulk-remove permission entries from a role preset."""
        result = await self._role_preset.bulk_remove_permissions.run(
            BulkRemoveRolePermissionPresetsAction(ids=input.permission_preset_ids)
        )
        return BulkRemoveRolePermissionPresetsPayload(
            items=[self._permission_data_to_node(d) for d in result.successes.values()],
            failed=[
                BulkRolePermissionPresetFailureInfo(
                    permission_preset_id=RolePermissionPresetID(permission_id),
                    message=str(exception),
                )
                for permission_id, exception in result.errors.items()
            ],
        )

    def _convert_filter(self, filter_: RolePresetFilter) -> list[QueryCondition]:
        fields = RolePresetSearchableFields.own
        conditions = [
            *self.apply_string_filter(filter_.name, fields.name.filter),
            *self.apply_string_filter(filter_.scope_type, fields.scope_type.filter),
            *self.apply_bool_filter(filter_.auto_assign, fields.auto_assign.filter),
            *self.apply_bool_filter(filter_.deleted, fields.deleted.filter),
            *self.apply_to_many_filter(
                filter_.permissions,
                RolePresetSearchableFields.nested.permissions.correlation,
                self._convert_permission_filter,
            ),
        ]
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
        fields = RolePresetSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case RolePresetOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case RolePresetOrderField.SCOPE_TYPE:
                    result.append(fields.scope_type.order.apply(ascending))
                case RolePresetOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case RolePresetOrderField.UPDATED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
        return result

    def _convert_permission_filter(
        self, filter_: RolePermissionPresetFilter
    ) -> list[QueryCondition]:
        # ``role_preset_id`` is intentionally ignored here: the parent preset scope
        # is enforced as a base condition by the caller, so it cannot be widened.
        fields = RolePermissionPresetSearchableFields.own
        conditions = [
            *self.apply_string_filter(filter_.entity_type, fields.entity_type.filter),
            *self._convert_permission_bit_filter(filter_.permission),
            *self.apply_datetime_filter(filter_.created_at, fields.created_at.filter),
        ]
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

    def _convert_permission_bit_filter(
        self, bit_filter: PermissionBitFilter | None
    ) -> list[QueryCondition]:
        """Each operation the caller set, on the entry's one permission bit."""
        if bit_filter is None:
            return []
        conditions = RolePermissionPresetSearchableFields.own.permission.filter
        applied: list[QueryCondition] = []
        if bit_filter.equals is not None:
            applied.append(conditions.equals(bit_filter.equals.to_permission()))
        if bit_filter.not_equals is not None:
            applied.append(conditions.not_equals(bit_filter.not_equals.to_permission()))
        if bit_filter.in_:
            applied.append(conditions.in_([v.to_permission() for v in bit_filter.in_]))
        if bit_filter.not_in:
            applied.append(conditions.not_in([v.to_permission() for v in bit_filter.not_in]))
        return applied

    def _convert_permission_orders(
        self, orders: list[RolePermissionPresetOrder]
    ) -> list[QueryOrder]:
        fields = RolePermissionPresetSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case RolePermissionPresetOrderField.ENTITY_TYPE:
                    result.append(fields.entity_type.order.apply(ascending))
                case RolePermissionPresetOrderField.PERMISSION:
                    result.append(fields.permission.order.apply(ascending))
                case RolePermissionPresetOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RolePresetData) -> RolePresetNode:
        return RolePresetNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            scope_type=data.scope_type,
            auto_assign=data.auto_assign,
            deleted=data.deleted,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _permission_data_to_node(data: RolePermissionPresetData) -> RolePermissionPresetNode:
        return RolePermissionPresetNode(
            id=data.id,
            field_id=data.id,
            role_preset_id=data.role_preset_id,
            entity_type=data.entity_type,
            permission=PermissionBitDTO.of(data.permission),
            created_at=data.created_at,
        )
