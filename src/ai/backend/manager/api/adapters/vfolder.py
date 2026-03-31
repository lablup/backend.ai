"""VFolder adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo
from ai.backend.common.dto.manager.v2.vfolder.request import (
    SearchVFoldersInput,
    VFolderFilter,
    VFolderOrder,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
    VFolderNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderAccessControlInfo,
    VFolderMetadataInfo,
    VFolderOwnershipInfo,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderUsageInfo as VFolderUsageInfoDTO,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import BinarySize, VFolderUsageMode
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderOperationStatus,
)
from ai.backend.manager.models.vfolder.conditions import VFolderConditions
from ai.backend.manager.models.vfolder.orders import (
    DEFAULT_BACKWARD_ORDER as VFOLDER_DEFAULT_BACKWARD_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    DEFAULT_FORWARD_ORDER as VFOLDER_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    TIEBREAKER_ORDER as VFOLDER_TIEBREAKER_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    resolve_order as resolve_vfolder_order,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.vfolder.types import (
    ProjectVFolderSearchScope,
    UserVFolderSearchScope,
)
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    AdminSearchVFoldersAction,
)
from ai.backend.manager.services.vfolder.actions.search_in_project import (
    SearchVFoldersInProjectAction,
)
from ai.backend.manager.services.vfolder.actions.search_user_vfolders import (
    SearchUserVFoldersAction,
)

from .base import BaseAdapter

_VFOLDER_PAGINATION_SPEC = PaginationSpec(
    forward_order=VFOLDER_DEFAULT_FORWARD_ORDER,
    backward_order=VFOLDER_DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=VFolderConditions.by_cursor_forward,
    backward_condition_factory=VFolderConditions.by_cursor_backward,
    tiebreaker_order=VFOLDER_TIEBREAKER_ORDER,
)


def _to_binary_size_info(value: int) -> BinarySizeInfo:
    """Convert bytes integer to BinarySizeInfo DTO."""
    return BinarySizeInfo(value=value, display=f"{BinarySize(value):s}")


class VFolderAdapter(BaseAdapter):
    """Adapter for VFolder domain operations."""

    @staticmethod
    def _vfolder_data_to_node(data: VFolderData) -> VFolderNode:
        """Convert VFolderData to VFolderNode DTO."""
        return VFolderNode(
            id=data.id,
            status=data.status.to_field(),
            host=data.host,
            metadata=VFolderMetadataInfo(
                name=data.name,
                usage_mode=data.usage_mode,
                quota_scope_id=str(data.quota_scope_id) if data.quota_scope_id else None,
                created_at=data.created_at,
                last_used=data.last_used,
                cloneable=data.cloneable,
            ),
            access_control=VFolderAccessControlInfo(
                permission=data.permission.to_field() if data.permission else None,
                ownership_type=data.ownership_type.to_field(),
            ),
            ownership=VFolderOwnershipInfo(
                user_id=data.user,
                project_id=data.group,
                creator_email=data.creator,
            ),
            usage=VFolderUsageInfoDTO(
                num_files=data.num_files,
                used_bytes=_to_binary_size_info(data.cur_size),
                max_size=_to_binary_size_info(data.max_size) if data.max_size is not None else None,
                max_files=data.max_files,
            ),
            unmanaged_path=data.unmanaged_path,
        )

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    async def admin_search(
        self,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Admin search for VFolders with system scope."""
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = (
            await self._processors.vfolder_admin.admin_search_vfolders.wait_for_complete(
                AdminSearchVFoldersAction(querier=querier)
            )
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def my_search(
        self,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders accessible to the current user.

        Calls current_user() internally -- the caller does not need to pass scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = UserVFolderSearchScope(user_id=me.user_id)
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.vfolder.search_user_vfolders.wait_for_complete(
            SearchUserVFoldersAction(scope=scope, querier=querier)
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def project_search(
        self,
        project_id: UUID,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders within a project scope.

        Used for the project admin page.
        """
        scope = ProjectVFolderSearchScope(project_id=project_id)
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.vfolder.search_vfolders_in_project.wait_for_complete(
            SearchVFoldersInProjectAction(scope=scope, querier=querier)
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # -------------------------------------------------------------------------
    # Filter / Order conversion
    # -------------------------------------------------------------------------

    def _convert_vfolder_filter(self, f: VFolderFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.name is not None:
            c = self.convert_string_filter(
                f.name,
                contains_factory=VFolderConditions.by_name_contains,
                equals_factory=VFolderConditions.by_name_equals,
                starts_with_factory=VFolderConditions.by_name_starts_with,
                ends_with_factory=VFolderConditions.by_name_ends_with,
            )
            if c is not None:
                conditions.append(c)
        if f.host is not None:
            c = self.convert_string_filter(
                f.host,
                contains_factory=VFolderConditions.by_host_contains,
                equals_factory=VFolderConditions.by_host_equals,
                starts_with_factory=VFolderConditions.by_host_starts_with,
                ends_with_factory=VFolderConditions.by_host_ends_with,
            )
            if c is not None:
                conditions.append(c)
        if f.status is not None:
            if f.status.in_ is not None:
                status_values = [VFolderOperationStatus(s) for s in f.status.in_]
                conditions.append(VFolderConditions.by_status_in(status_values))
            if f.status.not_in is not None:
                status_values = [VFolderOperationStatus(s) for s in f.status.not_in]
                conditions.append(VFolderConditions.by_status_not_in(status_values))
        if f.usage_mode is not None:
            if f.usage_mode.in_ is not None:
                mode_values = [VFolderUsageMode(m) for m in f.usage_mode.in_]
                conditions.append(VFolderConditions.by_usage_mode_in(mode_values))
            if f.usage_mode.not_in is not None:
                mode_values = [VFolderUsageMode(m) for m in f.usage_mode.not_in]
                conditions.append(VFolderConditions.by_usage_mode_not_in(mode_values))
        if f.created_at is not None:
            c = f.created_at.build_query_condition(
                before_factory=VFolderConditions.by_created_at_before,
                after_factory=VFolderConditions.by_created_at_after,
                equals_factory=VFolderConditions.by_created_at_equals,
            )
            if c is not None:
                conditions.append(c)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_vfolder_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_vfolder_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_vfolder_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_vfolder_orders(orders: list[VFolderOrder]) -> list[QueryOrder]:
        return [resolve_vfolder_order(o.field, o.direction) for o in orders]
