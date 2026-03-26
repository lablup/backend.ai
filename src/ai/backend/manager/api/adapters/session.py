"""Session adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.deployment.types import (
    EnvironmentVariableEntryInfoDTO,
    EnvironmentVariablesInfoDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
)
from ai.backend.common.dto.manager.v2.kernel.request import (
    AdminSearchKernelsInput,
    KernelFilter,
    KernelOrder,
)
from ai.backend.common.dto.manager.v2.kernel.response import (
    AdminSearchKernelsPayload,
    KernelClusterInfoGQLDTO,
    KernelLifecycleInfoGQLDTO,
    KernelNetworkInfoGQLDTO,
    KernelNode,
    KernelResourceInfoGQLDTO,
    KernelSessionInfoGQLDTO,
    KernelUserInfoGQLDTO,
    ResourceAllocationGQLDTO,
)
from ai.backend.common.dto.manager.v2.kernel.types import KernelStatusFilter
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceOptsEntryInfoDTO,
    ResourceOptsInfoDTO,
)
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    SessionFilter,
    SessionOrder,
)
from ai.backend.common.dto.manager.v2.session.response import (
    AdminSearchSessionsPayload,
    SessionLifecycleInfoGQLDTO,
    SessionMetadataInfoGQLDTO,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfoGQLDTO,
    SessionRuntimeInfoGQLDTO,
)
from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus, KernelStatusInMatchSpec
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.models.kernel.conditions import KernelConditions
from ai.backend.manager.models.kernel.orders import (
    DEFAULT_BACKWARD_ORDER as KERNEL_DEFAULT_BACKWARD_ORDER,
)
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
    DEFAULT_BACKWARD_ORDER as SESSION_DEFAULT_BACKWARD_ORDER,
)
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
    NoPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction

from .base import BaseAdapter


def _fold_kernel_status(status: KernelStatus) -> str:
    """Map internal kernel statuses to GQL-exposed statuses."""
    match status:
        case KernelStatus.PREPARING | KernelStatus.PULLING:
            return "PREPARING"
        case (
            KernelStatus.CANCELLED
            | KernelStatus.BUILDING
            | KernelStatus.RESTARTING
            | KernelStatus.RESIZING
            | KernelStatus.SUSPENDED
            | KernelStatus.ERROR
        ):
            return "CANCELLED"
        case _:
            return status.value


def _fold_session_status(status: SessionStatus) -> str:
    """Map internal session statuses to GQL-exposed statuses."""
    match status:
        case SessionStatus.PULLING:
            return "PREPARING"
        case SessionStatus.RESTARTING | SessionStatus.RUNNING_DEGRADED | SessionStatus.ERROR:
            return "CANCELLED"
        case _:
            return status.value


_SESSION_PAGINATION_SPEC = PaginationSpec(
    forward_order=SESSION_DEFAULT_FORWARD_ORDER,
    backward_order=SESSION_DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=SessionConditions.by_cursor_forward,
    backward_condition_factory=SessionConditions.by_cursor_backward,
    tiebreaker_order=SESSION_TIEBREAKER_ORDER,
)

_KERNEL_PAGINATION_SPEC = PaginationSpec(
    forward_order=KERNEL_DEFAULT_FORWARD_ORDER,
    backward_order=KERNEL_DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=KernelConditions.by_cursor_forward,
    backward_condition_factory=KernelConditions.by_cursor_backward,
    tiebreaker_order=KERNEL_TIEBREAKER_ORDER,
)


class SessionAdapter(BaseAdapter):
    """Adapter for session and kernel domain operations."""

    @staticmethod
    def _require_user_id() -> UUID:
        """Return the current user's UUID from request context.

        Raises RuntimeError if called outside a request context.
        """
        user = current_user()
        if user is None:
            raise RuntimeError("SessionAdapter requires an authenticated user in context")
        return user.user_id

    # -------------------------------------------------------------------------
    # Batch load (DataLoader)
    # -------------------------------------------------------------------------

    async def batch_load_by_ids(self, session_ids: Sequence[SessionId]) -> list[SessionNode | None]:
        """Batch load sessions by ID for DataLoader use.

        Returns SessionNode DTOs in the same order as the input session_ids list.
        """
        if not session_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[SessionConditions.by_ids(session_ids)],
        )
        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier, user_id=self._require_user_id())
        )
        session_map: dict[SessionId, SessionNode] = {
            SessionId(data.id): self._session_data_to_node(data) for data in action_result.data
        }
        return [session_map.get(session_id) for session_id in session_ids]

    async def batch_load_kernels_by_ids(
        self, kernel_ids: Sequence[KernelId]
    ) -> list[KernelNode | None]:
        """Batch load kernels by ID for DataLoader use.

        Returns KernelNode DTOs in the same order as the input kernel_ids list.
        """
        if not kernel_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[KernelConditions.by_ids(kernel_ids)],
        )
        action_result = await self._processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=querier, user_id=self._require_user_id())
        )
        kernel_map: dict[KernelId, KernelNode] = {
            info.id: self._kernel_info_to_node(info) for info in action_result.data
        }
        return [kernel_map.get(kernel_id) for kernel_id in kernel_ids]

    # -------------------------------------------------------------------------
    # Session search
    # -------------------------------------------------------------------------

    async def admin_search(
        self,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_session_filter(input.filter) if input.filter else []
        orders = self._convert_session_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier, user_id=self._require_user_id())
        )

        return AdminSearchSessionsPayload(
            items=[self._session_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_sessions_by_agent(
        self,
        agent_id: AgentId,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions scoped to a specific agent."""
        conditions = self._convert_session_filter(input.filter) if input.filter else []
        orders = self._convert_session_orders(input.order) if input.order else []
        scope_condition = SessionConditions.by_agent_id(agent_id)
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=[scope_condition],
        )

        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier, user_id=self._require_user_id())
        )

        return AdminSearchSessionsPayload(
            items=[self._session_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_session_filter(self, f: SessionFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
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
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_session_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_session_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_session_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_session_orders(orders: list[SessionOrder]) -> list[QueryOrder]:
        return [resolve_session_order(o.field, o.direction) for o in orders]

    # -------------------------------------------------------------------------
    # Kernel search
    # -------------------------------------------------------------------------

    async def admin_search_kernels(
        self,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_kernel_filter(input.filter) if input.filter else []
        orders = self._convert_kernel_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_KERNEL_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=querier, user_id=self._require_user_id())
        )

        return AdminSearchKernelsPayload(
            items=[self._kernel_info_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_kernels_by_agent(
        self,
        agent_id: AgentId,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels scoped to a specific agent."""
        conditions = self._convert_kernel_filter(input.filter) if input.filter else []
        orders = self._convert_kernel_orders(input.order) if input.order else []
        scope_condition = KernelConditions.by_agent_id(agent_id)
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_KERNEL_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=[scope_condition],
        )

        action_result = await self._processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=querier, user_id=self._require_user_id())
        )

        return AdminSearchKernelsPayload(
            items=[self._kernel_info_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_kernels_by_session(
        self,
        session_id: SessionId,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels scoped to a specific session."""
        conditions = self._convert_kernel_filter(input.filter) if input.filter else []
        orders = self._convert_kernel_orders(input.order) if input.order else []
        scope_condition = KernelConditions.by_session_ids([session_id])
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_KERNEL_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=[scope_condition],
        )

        action_result = await self._processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=querier, user_id=self._require_user_id())
        )

        return AdminSearchKernelsPayload(
            items=[self._kernel_info_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_kernel_filter(self, f: KernelFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
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
        if f.status is not None:
            c = self._convert_kernel_status_filter(f.status)
            if c is not None:
                conditions.append(c)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_kernel_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_kernel_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_kernel_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_kernel_status_filter(f: KernelStatusFilter) -> QueryCondition | None:
        if f.in_:
            return KernelConditions.by_status_filter_in(
                KernelStatusInMatchSpec(
                    values=[KernelStatus(s) for s in f.in_],
                    negated=False,
                )
            )
        if f.not_in:
            return KernelConditions.by_status_filter_in(
                KernelStatusInMatchSpec(
                    values=[KernelStatus(s) for s in f.not_in],
                    negated=True,
                )
            )
        return None

    @staticmethod
    def _convert_kernel_orders(orders: list[KernelOrder]) -> list[QueryOrder]:
        return [resolve_kernel_order(o.field, o.direction) for o in orders]

    # -------------------------------------------------------------------------
    # Data → DTO conversion
    # -------------------------------------------------------------------------

    @staticmethod
    def _session_data_to_node(data: SessionData) -> SessionNode:
        requested = ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(str(v)))
                for k, v in (data.requested_slots or {}).items()
            ]
        )
        occupied = ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(str(v)))
                for k, v in (data.occupying_slots or {}).items()
            ]
        )
        environ = (
            EnvironmentVariablesInfoDTO(
                entries=[
                    EnvironmentVariableEntryInfoDTO(name=k, value=str(v))
                    for k, v in data.environ.items()
                ]
            )
            if data.environ
            else None
        )
        return SessionNode(
            id=data.id,
            domain_name=data.domain_name,
            user_id=data.user_uuid,
            project_id=data.group_id,
            metadata=SessionMetadataInfoGQLDTO(
                creation_id=data.creation_id or "",
                name=data.name or "",
                session_type=data.session_type.value,
                access_key=str(data.access_key) if data.access_key else "",
                cluster_mode=data.cluster_mode.name,
                cluster_size=data.cluster_size,
                priority=data.priority,
                is_preemptible=data.is_preemptible,
                tag=data.tag,
            ),
            resource=SessionResourceInfoGQLDTO(
                allocation=ResourceAllocationGQLDTO(requested=requested, used=occupied),
                resource_group_name=data.scaling_group_name,
                target_resource_group_names=data.target_sgroup_names,
            ),
            lifecycle=SessionLifecycleInfoGQLDTO(
                status=_fold_session_status(data.status),
                result=data.result.value,
                created_at=data.created_at,
                terminated_at=data.terminated_at,
                starts_at=data.starts_at,
                batch_timeout=data.batch_timeout,
            ),
            runtime=SessionRuntimeInfoGQLDTO(
                environ=environ,
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
        requested = ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(v))
                for k, v in info.resource.requested_slots.to_json().items()
            ]
        )
        occupied = ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(v))
                for k, v in info.resource.occupied_slots.to_json().items()
            ]
        )
        shares = ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(str(v)))
                for k, v in (info.resource.occupied_shares or {}).items()
            ]
        )
        resource_opts = (
            ResourceOptsInfoDTO(
                entries=[
                    ResourceOptsEntryInfoDTO(name=k, value=str(v))
                    for k, v in info.resource.resource_opts.items()
                ]
            )
            if info.resource.resource_opts
            else None
        )
        return KernelNode(
            id=info.id,
            startup_command=info.runtime.startup_command,
            session_info=KernelSessionInfoGQLDTO(
                session_id=UUID(info.session.session_id),
                creation_id=info.session.creation_id,
                name=info.session.name,
                session_type=info.session.session_type.value,
            ),
            user_info=KernelUserInfoGQLDTO(
                user_id=info.user_permission.user_uuid,
                access_key=info.user_permission.access_key,
                domain_name=info.user_permission.domain_name,
                group_id=info.user_permission.group_id,
            ),
            network=KernelNetworkInfoGQLDTO(
                service_ports=None,
                preopen_ports=info.network.preopen_ports,
            ),
            cluster=KernelClusterInfoGQLDTO(
                cluster_role=info.cluster.cluster_role,
                cluster_idx=info.cluster.cluster_idx,
                local_rank=info.cluster.local_rank,
                cluster_hostname=info.cluster.cluster_hostname,
            ),
            resource=KernelResourceInfoGQLDTO(
                agent_id=info.resource.agent,
                resource_group_name=info.resource.scaling_group,
                container_id=info.resource.container_id,
                allocation=ResourceAllocationGQLDTO(requested=requested, used=occupied),
                shares=shares,
                resource_opts=resource_opts,
            ),
            lifecycle=KernelLifecycleInfoGQLDTO(
                status=_fold_kernel_status(info.lifecycle.status),
                result=info.lifecycle.result.value,
                created_at=info.lifecycle.created_at,
                terminated_at=info.lifecycle.terminated_at,
                starts_at=info.lifecycle.starts_at,
            ),
        )
