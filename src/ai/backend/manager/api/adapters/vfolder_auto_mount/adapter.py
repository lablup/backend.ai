"""VFolder auto-mount adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    CreateVFolderAutoMountInput,
    DeleteVFolderAutoMountInput,
    ScopedSearchVFolderAutoMountsInput,
    UpdateVFolderAutoMountInput,
    VFolderAutoMountFilter,
    VFolderAutoMountOrder,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    CreateVFolderAutoMountPayload,
    DeleteVFolderAutoMountPayload,
    SearchVFolderAutoMountsPayload,
    UpdateVFolderAutoMountPayload,
    VFolderAutoMountNode,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import VFolderAutoMountOrderField
from ai.backend.common.types import MountPermission
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.vfolder.types import VFolderMountPermission
from ai.backend.manager.data.vfolder_auto_mount.types import (
    VFolderAutoMountData,
    VFolderAutoMountSpec,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.scopes import ScopeTarget
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.models.specs.soft_delete import SoftDeleteUpdater
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.scopes import (
    ProjectVFolderAutoMountTarget,
    UserVFolderAutoMountTarget,
)
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)
from ai.backend.manager.models.vfolder_auto_mount.searchers import VFolderAutoMountSearcher
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountUpdater
from ai.backend.manager.services.vfolder_auto_mount.actions.bulk_get import (
    BulkGetVFolderAutoMountsAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.create import (
    CreateVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.delete import (
    DeleteVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.search import (
    SearchVFolderAutoMountsAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.update import (
    UpdateVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.processors import VFolderAutoMountProcessors
from ai.backend.manager.types import OptionalState

__all__ = ("VFolderAutoMountAdapter",)

_VFOLDER_AUTO_MOUNT_PAGINATION_SPEC = PaginationSpec(
    forward_order=VFolderAutoMountSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=VFolderAutoMountRow.id,
)


class VFolderAutoMountAdapter(BaseAdapter):
    """Adapter for adding, updating, deleting and reading the vfolder auto-mounts of projects
    and users."""

    _vfolder_auto_mount: VFolderAutoMountProcessors

    def __init__(self, vfolder_auto_mount: VFolderAutoMountProcessors) -> None:
        self._vfolder_auto_mount = vfolder_auto_mount

    async def bulk_get_ids(
        self, ids: Sequence[VFolderAutoMountID]
    ) -> list[VFolderAutoMountNode | Exception | None]:
        """Batch load auto-mounts by id for DataLoader use."""
        if not ids:
            return []
        result = await self._vfolder_auto_mount.bulk_get_ids.run(
            BulkGetVFolderAutoMountsAction(ids=list(ids))
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def scoped_search(
        self, input: ScopedSearchVFolderAutoMountsInput
    ) -> SearchVFolderAutoMountsPayload:
        """Search the auto-mounts of the named projects and users, combined with OR."""
        scopes: list[ScopeTarget] = [
            ProjectVFolderAutoMountTarget(project_id=ProjectID(entry.value))
            for entry in input.scope.project or []
        ]
        scopes.extend(
            UserVFolderAutoMountTarget(user_id=UserID(entry.value))
            for entry in input.scope.user or []
        )
        searcher = self._build_searcher(
            VFolderAutoMountSearcher,
            conditions=self._search_conditions(input.filter),
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_VFOLDER_AUTO_MOUNT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._vfolder_auto_mount.search.run(
            SearchVFolderAutoMountsAction(
                searcher=ScopedSearcher(scopes=scopes, used_by=(), searcher=searcher)
            )
        )
        return self._to_payload(result)

    async def create(self, input: CreateVFolderAutoMountInput) -> CreateVFolderAutoMountPayload:
        """Auto-mount a vfolder of a project, or one a user owns, into every session created
        in that project or by that user."""
        creator = VFolderAutoMountCreator(
            scope=input.scope.scope_type.to_owner(input.scope.scope_id),
            spec=VFolderAutoMountSpec(
                vfolder_id=VFolderUUID(input.vfolder_id),
                mount_destination=input.mount_destination,
                subpath=input.subpath,
                mount_permission=VFolderMountPermission(input.mount_permission),
            ),
        )
        result = await self._vfolder_auto_mount.create.run(
            CreateVFolderAutoMountAction(creator=creator)
        )
        return CreateVFolderAutoMountPayload(vfolder_auto_mount=self._data_to_node(result.data))

    async def update(self, input: UpdateVFolderAutoMountInput) -> UpdateVFolderAutoMountPayload:
        """Change an auto-mount's destination, subpath or permission."""
        updater = VFolderAutoMountUpdater(
            vfolder_auto_mount_id=VFolderAutoMountID(input.id),
            mount_destination=OptionalState.from_unset(input.mount_destination),
            subpath=OptionalState.from_unset(input.subpath),
            mount_permission=OptionalState.from_unset(input.mount_permission).map(
                VFolderMountPermission
            ),
        )
        result = await self._vfolder_auto_mount.update.run(
            UpdateVFolderAutoMountAction(updater=updater)
        )
        return UpdateVFolderAutoMountPayload(vfolder_auto_mount=self._data_to_node(result.data))

    async def delete(self, input: DeleteVFolderAutoMountInput) -> DeleteVFolderAutoMountPayload:
        """Mark an auto-mount deleted; sessions created afterwards no longer mount it."""
        result = await self._vfolder_auto_mount.delete.run(
            DeleteVFolderAutoMountAction(
                updater=SoftDeleteUpdater(
                    target_row=VFolderAutoMountRow,
                    target_column=VFolderAutoMountRow.id,
                    target_id=VFolderAutoMountID(input.id),
                    converter=VFolderAutoMountSearchableFields.own,
                )
            )
        )
        return DeleteVFolderAutoMountPayload(vfolder_auto_mount=self._data_to_node(result.data))

    def _search_conditions(self, filter: VFolderAutoMountFilter | None) -> list[QueryCondition]:
        """The filter's conditions; auto-mounts marked deleted are left out unless the
        top-level filter names ``deleted_at``."""
        if filter is None:
            return [VFolderAutoMountSearchableFields.own.deleted_at.filter.is_null()]
        conditions = self._convert_filter(filter)
        if filter.deleted_at is None:
            conditions.append(VFolderAutoMountSearchableFields.own.deleted_at.filter.is_null())
        return conditions

    def _convert_filter(self, filter: VFolderAutoMountFilter) -> list[QueryCondition]:
        fields = VFolderAutoMountSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.entity_id, fields.id.filter),
            *self.apply_enum_filter(filter.scope_type, fields.scope_type.filter),
            *self.apply_uuid_filter(filter.scope_id, fields.scope_id.filter),
            *self.apply_uuid_filter(filter.vfolder_id, fields.vfolder_id.filter),
            *self.apply_string_filter(filter.mount_destination, fields.mount_destination.filter),
            *self.apply_enum_filter(filter.mount_permission, fields.mount_permission.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
            *self.apply_nullable_datetime_filter(filter.deleted_at, fields.deleted_at.filter),
        ]
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    or_sub_conditions.append(combine_conditions_and(sub_conditions))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))
        if filter.NOT:
            for sub_filter in filter.NOT:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _convert_orders(self, order: list[VFolderAutoMountOrder]) -> list[QueryOrder]:
        return [self._convert_order(o) for o in order]

    def _convert_order(self, order: VFolderAutoMountOrder) -> QueryOrder:
        """The query order one requested order field names."""
        fields = VFolderAutoMountSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case VFolderAutoMountOrderField.MOUNT_DESTINATION:
                return fields.mount_destination.order.apply(ascending)
            case VFolderAutoMountOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case VFolderAutoMountOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)
            case VFolderAutoMountOrderField.DELETED_AT:
                return fields.deleted_at.order.apply(ascending)

    def _to_payload(
        self, result: BatchOpsResult[VFolderAutoMountData]
    ) -> SearchVFolderAutoMountsPayload:
        return SearchVFolderAutoMountsPayload(
            items=[self._data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @staticmethod
    def _data_to_node(data: VFolderAutoMountData) -> VFolderAutoMountNode:
        """Convert data layer type to Pydantic DTO."""
        return VFolderAutoMountNode(
            id=data.id,
            entity_id=data.entity_id(),
            scope_type=VFolderAutoMountScopeType.of_owner(data.scope),
            scope_id=data.scope,
            vfolder_id=data.vfolder_id,
            mount_destination=data.mount_destination,
            subpath=data.subpath,
            mount_permission=MountPermission(data.mount_permission),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
        )
