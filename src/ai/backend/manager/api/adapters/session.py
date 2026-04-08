"""Session adapter bridging DTOs and Processors."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa

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
    EnqueueSessionInput,
    SessionFilter,
    SessionOrder,
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
    TerminateSessionsInProjectInput,
    TerminateSessionsInput,
    UpdateSessionInput,
)
from ai.backend.common.dto.manager.v2.session.response import (
    AdminSearchSessionsPayload,
    EnqueueSessionPayload,
    SessionLifecycleInfoGQLDTO,
    SessionLogsPayload,
    SessionMetadataInfoGQLDTO,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfoGQLDTO,
    SessionRuntimeInfoGQLDTO,
    StartSessionServicePayload,
    TerminateSessionsPayload,
    UpdateSessionPayload,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    KernelId,
    MountPermission,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus, KernelStatusInMatchSpec
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
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
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.session.types import ProjectSessionSearchScope
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionBatchSpec,
    SessionExecutionSpec,
    SessionResourceSpec,
    SessionSchedulingSpec,
    VFolderMountItem,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
)
from ai.backend.manager.services.session.actions.rename_session import RenameSessionAction
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_in_project import (
    SearchSessionsInProjectAction,
)
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction
from ai.backend.manager.services.session.actions.shutdown_service import ShutdownServiceAction
from ai.backend.manager.services.session.actions.start_service import StartServiceAction
from ai.backend.manager.services.session.actions.terminate_sessions import (
    TerminateSessionsAction,
)
from ai.backend.manager.services.session.actions.terminate_sessions_in_project import (
    TerminateSessionsInProjectAction,
)

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
    # Create
    # -------------------------------------------------------------------------

    async def enqueue(
        self,
        input: EnqueueSessionInput,
        user_id: UUID,
        user_role: str,
        access_key: str,
        domain_name: str,
        group_id: UUID,
    ) -> EnqueueSessionPayload:
        """Enqueue a new session for scheduling."""
        batch_spec: SessionBatchSpec | None = None
        if input.batch is not None:
            starts_at = None
            if input.batch.starts_at is not None:
                starts_at = datetime.fromisoformat(input.batch.starts_at)

            batch_timeout = (
                timedelta(seconds=input.batch.batch_timeout)
                if input.batch.batch_timeout is not None
                else None
            )

            batch_spec = SessionBatchSpec(
                startup_command=input.batch.startup_command,
                starts_at=starts_at,
                batch_timeout=batch_timeout,
            )

        mounts: list[VFolderMountItem] | None = None
        if input.mounts is not None:
            mounts = [
                VFolderMountItem(
                    vfolder_id=m.vfolder_id,
                    mount_path=m.mount_path,
                    permission=(MountPermission(m.permission) if m.permission else None),
                )
                for m in input.mounts
            ]

        execution_spec: SessionExecutionSpec | None = None
        if input.environ or input.preopen_ports or input.bootstrap_script:
            execution_spec = SessionExecutionSpec(
                environ=input.environ,
                preopen_ports=input.preopen_ports,
                bootstrap_script=input.bootstrap_script,
            )

        action = EnqueueSessionAction(
            session_name=input.session_name,
            session_type=SessionTypes(input.session_type.value),
            image_id=input.image_id,
            resource=SessionResourceSpec(
                entries=[
                    ResourceSlotEntry(
                        resource_type=e.resource_type,
                        quantity=e.quantity,
                    )
                    for e in input.resource_entries
                ],
                resource_group=input.resource_group,
                shmem=input.resource_opts.shmem.expr
                if input.resource_opts and input.resource_opts.shmem
                else None,
                cluster_mode=(
                    ClusterMode.MULTI_NODE
                    if input.cluster_mode == ClusterModeEnum.MULTI_NODE
                    else ClusterMode.SINGLE_NODE
                ),
                cluster_size=input.cluster_size,
            ),
            mounts=mounts,
            execution=execution_spec,
            scheduling=SessionSchedulingSpec(
                priority=input.priority,
                is_preemptible=input.is_preemptible,
                dependencies=input.dependencies,
                agent_list=input.agent_list,
                attach_network=input.attach_network,
            ),
            batch=batch_spec,
            tag=input.tag,
            callback_url=input.callback_url,
            user_id=user_id,
            user_role=UserRole(user_role),
            access_key=AccessKey(access_key),
            domain_name=domain_name,
            group_id=group_id,
        )

        result = await self._processors.session.enqueue_session.wait_for_complete(action)
        return EnqueueSessionPayload(
            session=self._session_data_to_node(result.session_data),
        )

    # -------------------------------------------------------------------------
    # Get single session
    # -------------------------------------------------------------------------

    async def get(self, session_id: UUID) -> SessionNode:
        """Get a single session by ID."""
        conditions = [SessionConditions.by_ids([SessionId(session_id)])]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=conditions,
        )
        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier, user_id=self._require_user_id())
        )
        if not action_result.data:
            raise SessionNotFound(f"Session not found: {session_id}")
        return self._session_data_to_node(action_result.data[0])

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

    async def my_search(self, input: AdminSearchSessionsInput) -> AdminSearchSessionsPayload:
        """Search sessions owned by the current user."""
        user = current_user()
        if user is None:
            raise RuntimeError("No authenticated user in context")

        conditions = self._convert_session_filter(input.filter) if input.filter else []
        orders = self._convert_session_orders(input.order) if input.order else []

        def _by_user_uuid() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.user_uuid == user.user_id

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
            base_conditions=[_by_user_uuid],
        )
        action_result = await self._processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier, user_id=user.user_id)
        )
        return AdminSearchSessionsPayload(
            items=[self._session_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_by_project(
        self,
        scope: ProjectSessionSearchScope,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions within a project, cursor-based pagination."""
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
        action_result = await self._processors.session.search_sessions_in_project.wait_for_complete(
            SearchSessionsInProjectAction(scope=scope, querier=querier)
        )
        return AdminSearchSessionsPayload(
            items=[self._session_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def project_search(
        self, project_id: UUID, input: AdminSearchSessionsInput
    ) -> AdminSearchSessionsPayload:
        """Search sessions within a specific project."""
        conditions = self._convert_session_filter(input.filter) if input.filter else []
        orders = self._convert_session_orders(input.order) if input.order else []

        def _by_project_id() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.group_id == project_id

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
            base_conditions=[_by_project_id],
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
                in_factory=SessionConditions.by_name_in,
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
                in_factory=SessionConditions.by_domain_name_in,
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
    # Terminate
    # -------------------------------------------------------------------------

    async def terminate(self, input: TerminateSessionsInput) -> TerminateSessionsPayload:
        """Terminate one or more sessions."""
        action = TerminateSessionsAction(
            session_ids=[SessionId(sid) for sid in input.session_ids],
            forced=input.forced,
        )
        result = await self._processors.session.terminate_sessions.wait_for_complete(action)
        return TerminateSessionsPayload(
            cancelled=result.cancelled,
            terminating=result.terminating,
            force_terminated=result.force_terminated,
            skipped=result.skipped,
        )

    async def terminate_in_project(
        self, input: TerminateSessionsInProjectInput
    ) -> TerminateSessionsPayload:
        """Terminate one or more sessions within a project scope."""
        action = TerminateSessionsInProjectAction(
            project_id=input.project_id,
            session_ids=[SessionId(sid) for sid in input.session_ids],
            forced=input.forced,
        )
        result = await self._processors.session.terminate_sessions_in_project.wait_for_complete(
            action
        )
        return TerminateSessionsPayload(
            cancelled=result.cancelled,
            terminating=result.terminating,
            force_terminated=result.force_terminated,
            skipped=result.skipped,
        )

    # -------------------------------------------------------------------------
    # Service management
    # -------------------------------------------------------------------------

    async def start_service(
        self,
        session_id: UUID,
        input: StartSessionServiceInput,
        access_key: str,
    ) -> StartSessionServicePayload:
        """Start an app service in a session."""
        action = StartServiceAction(
            session_name=str(session_id),
            access_key=AccessKey(access_key),
            service=input.service,
            login_session_token=input.login_session_token,
            port=input.port,
            arguments=json.dumps(input.arguments) if input.arguments else None,
            envs=json.dumps(input.envs) if input.envs else None,
        )
        result = await self._processors.session.start_service.wait_for_complete(action)
        return StartSessionServicePayload(token=result.token, wsproxy_addr=result.wsproxy_addr)

    async def shutdown_service(
        self,
        session_id: UUID,
        input: ShutdownSessionServiceInput,
        access_key: str,
    ) -> None:
        """Shut down a service in a session."""
        action = ShutdownServiceAction(
            session_name=str(session_id),
            owner_access_key=AccessKey(access_key),
            service_name=input.service,
        )
        await self._processors.session.shutdown_service.wait_for_complete(action)

    # -------------------------------------------------------------------------
    # Logs
    # -------------------------------------------------------------------------

    async def get_logs(
        self,
        session_id: UUID,
        access_key: str,
        kernel_id: UUID | None = None,
    ) -> SessionLogsPayload:
        """Get container logs for a session."""
        action = GetContainerLogsAction(
            session_name=str(session_id),
            owner_access_key=AccessKey(access_key),
            kernel_id=KernelId(kernel_id) if kernel_id else None,
        )
        result = await self._processors.session.get_container_logs.wait_for_complete(action)
        logs_text = result.result.get("result", {}).get("logs", "")
        return SessionLogsPayload(logs=logs_text)

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    async def update(
        self,
        session_id: UUID,
        input: UpdateSessionInput,
        access_key: str,
    ) -> UpdateSessionPayload:
        """Update session fields (currently supports rename only)."""
        if input.name is not None:
            action = RenameSessionAction(
                session_name=str(session_id),
                new_name=input.name,
                owner_access_key=AccessKey(access_key),
            )
            result = await self._processors.session.rename_session.wait_for_complete(action)
            return UpdateSessionPayload(session=self._session_data_to_node(result.session_data))
        # If no fields to update, just return the current session
        session_node = await self.get(session_id)
        return UpdateSessionPayload(session=session_node)

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
