"""Session adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput, KernelOrder
from ai.backend.common.dto.manager.v2.kernel.response import (
    AdminSearchKernelsPayload,
    KernelClusterInfo,
    KernelLifecycleInfo,
    KernelNode,
    KernelResourceInfo,
    KernelSessionInfo,
    KernelUserInfo,
)
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    SessionOrder,
)
from ai.backend.common.dto.manager.v2.session.response import (
    AdminSearchSessionsPayload,
    SessionLifecycleInfo,
    SessionMetadataInfo,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfo,
    SessionRuntimeInfo,
)
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.kernel.conditions import KernelConditions
from ai.backend.manager.models.kernel.orders import (
    DEFAULT_FORWARD_ORDER as KERNEL_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.kernel.orders import (
    TIEBREAKER_ORDER as KERNEL_TIEBREAKER_ORDER,
)
from ai.backend.manager.models.kernel.orders import (
    resolve_order as resolve_kernel_order,
)
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.session.orders import (
    DEFAULT_FORWARD_ORDER as SESSION_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.session.orders import (
    TIEBREAKER_ORDER as SESSION_TIEBREAKER_ORDER,
)
from ai.backend.manager.models.session.orders import (
    resolve_order as resolve_session_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class SessionAdapter(BaseAdapter):
    """Adapter for session and kernel domain operations."""

    # -------------------------------------------------------------------------
    # Session search
    # -------------------------------------------------------------------------

    async def admin_search(
        self,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions (admin, no scope) with filters, orders, and pagination."""
        querier = self._build_session_querier(input)

        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier)
        )

        return AdminSearchSessionsPayload(
            items=[self._session_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_session_querier(self, input: AdminSearchSessionsInput) -> BatchQuerier:
        conditions = self._convert_session_filter(input) if input.filter else []
        orders = (
            self._convert_session_orders(input.order)
            if input.order
            else [SESSION_DEFAULT_FORWARD_ORDER]
        )
        orders.append(SESSION_TIEBREAKER_ORDER)
        pagination = self._build_session_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_session_filter(self, input: AdminSearchSessionsInput) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if input.filter is None:
            return conditions
        f = input.filter
        if f.id is not None:
            c = self.convert_uuid_filter(
                f.id,
                equals_factory=SessionConditions.by_id_filter_equals,
                in_factory=SessionConditions.by_id_filter_in,
            )
            if c is not None:
                conditions.append(c)
        if f.name is not None:
            c = self.convert_string_filter(
                f.name,
                contains_factory=SessionConditions.by_name_contains,
                equals_factory=SessionConditions.by_name_equals,
                starts_with_factory=SessionConditions.by_name_starts_with,
                ends_with_factory=SessionConditions.by_name_ends_with,
            )
            if c is not None:
                conditions.append(c)
        if f.domain_name is not None:
            c = self.convert_string_filter(
                f.domain_name,
                contains_factory=SessionConditions.by_domain_name_contains,
                equals_factory=SessionConditions.by_domain_name_equals,
                starts_with_factory=SessionConditions.by_domain_name_starts_with,
                ends_with_factory=SessionConditions.by_domain_name_ends_with,
            )
            if c is not None:
                conditions.append(c)
        if f.project_id is not None:
            c = self.convert_uuid_filter(
                f.project_id,
                equals_factory=SessionConditions.by_group_id_filter_equals,
                in_factory=SessionConditions.by_group_id_filter_in,
            )
            if c is not None:
                conditions.append(c)
        if f.user_uuid is not None:
            c = self.convert_uuid_filter(
                f.user_uuid,
                equals_factory=SessionConditions.by_user_uuid_filter_equals,
                in_factory=SessionConditions.by_user_uuid_filter_in,
            )
            if c is not None:
                conditions.append(c)
        return conditions

    @staticmethod
    def _convert_session_orders(orders: list[SessionOrder]) -> list[QueryOrder]:
        return [resolve_session_order(o.field, o.direction) for o in orders]

    @staticmethod
    def _build_session_pagination(input: AdminSearchSessionsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    # -------------------------------------------------------------------------
    # Kernel search
    # -------------------------------------------------------------------------

    async def admin_search_kernels(
        self,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels (admin, no scope) with filters, orders, and pagination."""
        querier = self._build_kernel_querier(input)

        action_result = await self._processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=querier)
        )

        return AdminSearchKernelsPayload(
            items=[self._kernel_info_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_kernel_querier(self, input: AdminSearchKernelsInput) -> BatchQuerier:
        conditions = self._convert_kernel_filter(input) if input.filter else []
        orders = (
            self._convert_kernel_orders(input.order)
            if input.order
            else [KERNEL_DEFAULT_FORWARD_ORDER]
        )
        orders.append(KERNEL_TIEBREAKER_ORDER)
        pagination = self._build_kernel_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_kernel_filter(self, input: AdminSearchKernelsInput) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if input.filter is None:
            return conditions
        f = input.filter
        if f.id is not None:
            c = self.convert_uuid_filter(
                f.id,
                equals_factory=KernelConditions.by_id_filter_equals,
                in_factory=KernelConditions.by_id_filter_in,
            )
            if c is not None:
                conditions.append(c)
        if f.session_id is not None:
            c = self.convert_uuid_filter(
                f.session_id,
                equals_factory=KernelConditions.by_session_id_filter_equals,
                in_factory=KernelConditions.by_session_id_filter_in,
            )
            if c is not None:
                conditions.append(c)
        return conditions

    @staticmethod
    def _convert_kernel_orders(orders: list[KernelOrder]) -> list[QueryOrder]:
        return [resolve_kernel_order(o.field, o.direction) for o in orders]

    @staticmethod
    def _build_kernel_pagination(input: AdminSearchKernelsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    # -------------------------------------------------------------------------
    # Data → DTO conversion
    # -------------------------------------------------------------------------

    @staticmethod
    def _session_data_to_node(data: SessionData) -> SessionNode:
        return SessionNode(
            id=data.id,
            metadata=SessionMetadataInfo(
                creation_id=data.creation_id,
                name=data.name,
                session_type=data.session_type.value,
                access_key=str(data.access_key) if data.access_key else None,
                cluster_mode=str(data.cluster_mode),
                cluster_size=data.cluster_size,
                priority=data.priority,
                is_preemptible=data.is_preemptible,
                tag=data.tag,
            ),
            resource=SessionResourceInfo(
                occupying_slots=data.occupying_slots,
                requested_slots=data.requested_slots,
                scaling_group_name=data.scaling_group_name,
                target_sgroup_names=data.target_sgroup_names,
                agent_ids=data.agent_ids,
                images=data.images,
            ),
            lifecycle=SessionLifecycleInfo(
                status=data.status.value,
                result=data.result.value,
                created_at=data.created_at,
                terminated_at=data.terminated_at,
                starts_at=data.starts_at,
                batch_timeout=data.batch_timeout,
                status_info=data.status_info,
            ),
            runtime=SessionRuntimeInfo(
                environ=data.environ,
                bootstrap_script=data.bootstrap_script,
                startup_command=data.startup_command,
                callback_url=str(data.callback_url) if data.callback_url else None,
            ),
            network=SessionNetworkInfo(
                use_host_network=data.use_host_network,
                network_type=data.network_type.value if data.network_type else None,
                network_id=data.network_id,
            ),
        )

    @staticmethod
    def _kernel_info_to_node(info: KernelInfo) -> KernelNode:
        return KernelNode(
            id=info.id,
            startup_command=info.runtime.startup_command,
            session=KernelSessionInfo(
                session_id=UUID(info.session.session_id),
                creation_id=info.session.creation_id,
                name=info.session.name,
                session_type=info.session.session_type.value,
            ),
            user=KernelUserInfo(
                user_uuid=info.user_permission.user_uuid,
                access_key=info.user_permission.access_key,
                domain_name=info.user_permission.domain_name,
                group_id=info.user_permission.group_id,
            ),
            cluster=KernelClusterInfo(
                cluster_mode=info.cluster.cluster_mode,
                cluster_size=info.cluster.cluster_size,
                cluster_role=info.cluster.cluster_role,
                cluster_idx=info.cluster.cluster_idx,
                local_rank=info.cluster.local_rank,
                cluster_hostname=info.cluster.cluster_hostname,
            ),
            resource=KernelResourceInfo(
                scaling_group=info.resource.scaling_group,
                agent=info.resource.agent,
                agent_addr=info.resource.agent_addr,
                container_id=info.resource.container_id,
                occupied_slots=dict(info.resource.occupied_slots.to_json()),
                requested_slots=dict(info.resource.requested_slots.to_json()),
                occupied_shares=info.resource.occupied_shares,
                resource_opts=info.resource.resource_opts,
            ),
            lifecycle=KernelLifecycleInfo(
                status=info.lifecycle.status.value,
                result=info.lifecycle.result.value,
                created_at=info.lifecycle.created_at,
                terminated_at=info.lifecycle.terminated_at,
                starts_at=info.lifecycle.starts_at,
                status_info=info.lifecycle.status_info,
            ),
        )
