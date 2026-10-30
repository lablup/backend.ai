"""Role preset domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers. Translates v2 DTOs
into Processor actions and converts the action results back into v2 DTOs.
"""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.dto.manager.v2.common import (
    OrderDirection,
    PartialBulkFailure,
    PartialBulkPayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, PermissionBitFilter
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    PartialBulkRemoveRolePresetPermissionsInput,
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    AtomicBulkAddRolePresetPermissionsPayload,
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
    PartialBulkDeleteRolePresetsInput,
    PartialBulkPurgeRolePresetsInput,
    PartialBulkRestoreRolePresetsInput,
    PartialBulkUpdateRolePresetsInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetBody,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkDeleteRolePresetsPayload,
    BulkPurgeRolePresetsPayload,
    BulkRestoreRolePresetsPayload,
    BulkRolePresetFailureInfo,
    CreateRolePresetPayload,
    DeleteRolePresetPayload,
    PurgeRolePresetPayload,
    RestoreRolePresetPayload,
    RolePresetNode,
    SearchRolePresetsPayload,
    UpdateRolePresetPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField, RolePresetUsage
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
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
from ai.backend.manager.models.rbac_models.role_preset.updaters import (
    RolePresetUpdater,
)
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater, SoftDeleteUpdater
from ai.backend.manager.services.role_preset.actions.atomic_bulk_add_permissions import (
    AtomicBulkAddRolePresetPermissionsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_get import BulkGetRolePresetsAction
from ai.backend.manager.services.role_preset.actions.bulk_get_permissions import (
    BulkGetRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.create import CreateRolePresetAction
from ai.backend.manager.services.role_preset.actions.delete import DeleteRolePresetAction
from ai.backend.manager.services.role_preset.actions.get import GetRolePresetAction
from ai.backend.manager.services.role_preset.actions.partial_bulk_delete import (
    PartialBulkDeleteRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_purge import (
    PartialBulkPurgeRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_remove_permissions import (
    PartialBulkRemoveRolePresetPermissionsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_restore import (
    PartialBulkRestoreRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_update import (
    PartialBulkUpdateRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.purge import PurgeRolePresetAction
from ai.backend.manager.services.role_preset.actions.restore import RestoreRolePresetAction
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

    async def batch_load_by_ids(
        self, ids: Sequence[RolePresetID]
    ) -> list[RolePresetNode | Exception | None]:
        """Batch load role presets by id for DataLoader use.

        One answer per id in the given order: the node, ``None`` for an id matching no
        row, and the denial for one the caller may not read.
        """
        if not ids:
            return []
        result = await self._role_preset.bulk_get.run(BulkGetRolePresetsAction(ids=ids))
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def batch_load_permissions_by_ids(
        self, ids: Sequence[RolePermissionPresetID]
    ) -> list[RolePermissionPresetNode | Exception | None]:
        """Batch load preset permission entries for DataLoader use, checked per preset."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._role_preset.bulk_get_permissions,
            BulkGetRolePermissionPresetsAction(ids=ids),
            ids,
            self._permission_data_to_node,
        )

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
        # top-level ``deleted_at`` or ``deleted`` filter.
        base_conditions: list[QueryCondition] = []
        if input.filter is None or (
            input.filter.deleted_at is None and input.filter.deleted is None
        ):
            base_conditions.append(RolePresetSearchableFields.own.deleted_at.filter.is_null())
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

    async def update(
        self, role_preset_id: RolePresetID, input: UpdateRolePresetBody
    ) -> UpdateRolePresetPayload:
        """Update an existing role preset's metadata."""
        result = await self._role_preset.update.run(
            UpdateRolePresetAction(updater=self._to_updater(role_preset_id, input))
        )
        return UpdateRolePresetPayload(role_preset=self._data_to_node(result.data))

    async def delete(self, role_preset_id: RolePresetID) -> DeleteRolePresetPayload:
        """Soft-delete a role preset."""
        result = await self._role_preset.delete.run(
            DeleteRolePresetAction(
                updater=SoftDeleteUpdater(
                    target_row=RolePresetRow,
                    target_column=RolePresetRow.id,
                    target_id=role_preset_id,
                    converter=RolePresetSearchableFields.own,
                )
            )
        )
        return DeleteRolePresetPayload(role_preset=self._data_to_node(result.data))

    async def restore(self, role_preset_id: RolePresetID) -> RestoreRolePresetPayload:
        """Restore a soft-deleted role preset."""
        result = await self._role_preset.restore.run(
            RestoreRolePresetAction(
                updater=RestoreUpdater(
                    target_row=RolePresetRow,
                    target_column=RolePresetRow.id,
                    target_id=role_preset_id,
                    converter=RolePresetSearchableFields.own,
                )
            )
        )
        return RestoreRolePresetPayload(role_preset=self._data_to_node(result.data))

    async def purge(self, role_preset_id: RolePresetID) -> PurgeRolePresetPayload:
        """Purge a role preset together with its permission entries."""
        result = await self._role_preset.purge.run(PurgeRolePresetAction(preset_id=role_preset_id))
        node = self._data_to_node(result.data)
        return PurgeRolePresetPayload(role_preset=node, entity_id=node.entity_id)

    async def partial_bulk_update(
        self, input: PartialBulkUpdateRolePresetsInput
    ) -> PartialBulkPayload[RolePresetNode]:
        """Update several role presets, answering for each one."""
        result = await self._role_preset.partial_bulk_update.run(
            PartialBulkUpdateRolePresetsAction(
                updaters=[
                    self._to_updater(RolePresetID(item.id), item.input) for item in input.items
                ]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_delete(
        self, input: PartialBulkDeleteRolePresetsInput
    ) -> PartialBulkPayload[RolePresetNode]:
        """Soft-delete several role presets, answering for each one."""
        result = await self._role_preset.partial_bulk_delete.run(
            PartialBulkDeleteRolePresetsAction(
                ids=[RolePresetID(preset_id) for preset_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_restore(
        self, input: PartialBulkRestoreRolePresetsInput
    ) -> PartialBulkPayload[RolePresetNode]:
        """Restore several soft-deleted role presets, answering for each one."""
        result = await self._role_preset.partial_bulk_restore.run(
            PartialBulkRestoreRolePresetsAction(
                ids=[RolePresetID(preset_id) for preset_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeRolePresetsInput
    ) -> PartialBulkPayload[RolePresetNode]:
        """Purge several role presets, answering for each one."""
        result = await self._role_preset.partial_bulk_purge.run(
            PartialBulkPurgeRolePresetsAction(
                ids=[RolePresetID(preset_id) for preset_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def bulk_delete(self, input: BulkDeleteRolePresetsInput) -> BulkDeleteRolePresetsPayload:
        """Same as :meth:`partial_bulk_delete`, in the payload shape of the old bulk API."""
        result = await self._role_preset.partial_bulk_delete.run(
            PartialBulkDeleteRolePresetsAction(ids=input.role_preset_ids)
        )
        payload = self._to_partial_bulk_payload(result)
        return BulkDeleteRolePresetsPayload(
            items=payload.successes, failed=self._to_bulk_failures(payload)
        )

    async def bulk_restore(
        self, input: BulkRestoreRolePresetsInput
    ) -> BulkRestoreRolePresetsPayload:
        """Same as :meth:`partial_bulk_restore`, in the payload shape of the old bulk API."""
        result = await self._role_preset.partial_bulk_restore.run(
            PartialBulkRestoreRolePresetsAction(ids=input.role_preset_ids)
        )
        payload = self._to_partial_bulk_payload(result)
        return BulkRestoreRolePresetsPayload(
            items=payload.successes, failed=self._to_bulk_failures(payload)
        )

    async def bulk_purge(self, input: BulkPurgeRolePresetsInput) -> BulkPurgeRolePresetsPayload:
        """Same as :meth:`partial_bulk_purge`, in the payload shape of the old bulk API."""
        result = await self._role_preset.partial_bulk_purge.run(
            PartialBulkPurgeRolePresetsAction(ids=input.role_preset_ids)
        )
        payload = self._to_partial_bulk_payload(result)
        return BulkPurgeRolePresetsPayload(
            items=payload.successes, failed=self._to_bulk_failures(payload)
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

    async def atomic_bulk_add_permissions(
        self,
        role_preset_id: RolePresetID,
        input: BulkAddRolePermissionPresetsInput,
    ) -> AtomicBulkAddRolePresetPermissionsPayload:
        """Add permission entries to an existing role preset, all or none."""
        creators = [
            RolePermissionPresetCreator(
                entity_type=entry.entity_type,
                permission=entry.permission.to_permission(),
            )
            for entry in input.permissions
        ]
        result = await self._role_preset.atomic_bulk_add_permissions.run(
            AtomicBulkAddRolePresetPermissionsAction(preset_id=role_preset_id, creators=creators)
        )
        return AtomicBulkAddRolePresetPermissionsPayload(
            items=[self._permission_data_to_node(d) for d in result.items]
        )

    async def bulk_add_permissions(
        self,
        role_preset_id: RolePresetID,
        input: BulkAddRolePermissionPresetsInput,
    ) -> BulkAddRolePermissionPresetsPayload:
        """Same as :meth:`atomic_bulk_add_permissions`, in the payload shape of the old bulk API."""
        payload = await self.atomic_bulk_add_permissions(role_preset_id, input)
        return BulkAddRolePermissionPresetsPayload(items=payload.items, failed=[])

    async def partial_bulk_remove_permissions(
        self, input: PartialBulkRemoveRolePresetPermissionsInput
    ) -> PartialBulkPayload[RolePermissionPresetNode]:
        """Remove several permission entries, answering for each one."""
        result = await self._role_preset.partial_bulk_remove_permissions.run(
            PartialBulkRemoveRolePresetPermissionsAction(
                ids=[RolePermissionPresetID(entry_id) for entry_id in input.ids]
            )
        )
        return PartialBulkPayload[RolePermissionPresetNode](
            successes=[self._permission_data_to_node(d) for d in result.successes.values()],
            failed=[
                PartialBulkFailure(id=permission_id, message=str(exception))
                for permission_id, exception in result.errors.items()
            ],
        )

    async def bulk_remove_permissions(
        self, input: BulkRemoveRolePermissionPresetsInput
    ) -> BulkRemoveRolePermissionPresetsPayload:
        """Same as :meth:`partial_bulk_remove_permissions`, in the payload shape of the old bulk API."""
        result = await self._role_preset.partial_bulk_remove_permissions.run(
            PartialBulkRemoveRolePresetPermissionsAction(ids=input.permission_preset_ids)
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

    def _to_updater(
        self, role_preset_id: RolePresetID, input: UpdateRolePresetBody
    ) -> RolePresetUpdater:
        return RolePresetUpdater(
            preset_id=role_preset_id,
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            auto_assign=(
                OptionalState.update(input.auto_assign)
                if input.auto_assign is not None
                else OptionalState.nop()
            ),
        )

    def _to_partial_bulk_payload(
        self, result: PartialBulkResult[RolePresetData]
    ) -> PartialBulkPayload[RolePresetNode]:
        return PartialBulkPayload[RolePresetNode](
            successes=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                PartialBulkFailure(id=item.entity_id, message=str(item.error))
                for item in result.items
                if item.error is not None
            ],
        )

    def _to_bulk_failures(
        self, payload: PartialBulkPayload[RolePresetNode]
    ) -> list[BulkRolePresetFailureInfo]:
        return [
            BulkRolePresetFailureInfo(
                role_preset_id=RolePresetID(failure.id), message=failure.message
            )
            for failure in payload.failed
        ]

    def _convert_filter(self, filter_: RolePresetFilter) -> list[QueryCondition]:
        fields = RolePresetSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter_.id, fields.id.filter),
            *self.apply_uuid_filter(filter_.entity_id, fields.id.filter),
            *self.apply_string_filter(filter_.name, fields.name.filter),
            *self.apply_string_filter(filter_.scope_type, fields.scope_type.filter),
            *self.apply_bool_filter(filter_.auto_assign, fields.auto_assign.filter),
            *self._deleted_conditions(filter_.deleted),
            *self.apply_nullable_datetime_filter(filter_.deleted_at, fields.deleted_at.filter),
            *self.apply_to_many_filter(
                filter_.permissions,
                RolePresetSearchableFields.nested.permissions.correlation,
                self._convert_permission_filter,
            ),
            *self.apply_to_many_filter(
                filter_.labels,
                RolePresetSearchableFields.nested.labels.correlation,
                self._convert_entity_label_filter,
            ),
        ]
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                sub_conditions = self._convert_filter(sub)
                if sub_conditions:
                    or_conds.append(combine_conditions_and(sub_conditions))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            for sub in filter_.NOT:
                sub_conditions = self._convert_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _deleted_conditions(self, deleted: bool | None) -> list[QueryCondition]:
        if deleted is None:
            return []
        conditions = RolePresetSearchableFields.own.deleted_at.filter
        return [conditions.is_not_null() if deleted else conditions.is_null()]

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
            *self.apply_uuid_filter(filter_.field_id, fields.id.filter),
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
                sub_conditions = self._convert_permission_filter(sub)
                if sub_conditions:
                    or_conds.append(combine_conditions_and(sub_conditions))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            for sub in filter_.NOT:
                sub_conditions = self._convert_permission_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
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
            deleted=data.deleted_at is not None,
            deleted_at=data.deleted_at,
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
