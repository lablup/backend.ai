"""Session adapter bridging DTOs and Processors."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
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
from ai.backend.common.dto.manager.v2.scheduler.request import ComputeScheduleInput
from ai.backend.common.dto.manager.v2.scheduler.response import (
    ComputeScheduleKernelResultInfo,
    ComputeSchedulePayload,
    UnschedulableReasonHintInfo,
)
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    EnqueueSessionInput,
    ExcludeSessionIdleChecksInput,
    IncludeSessionIdleChecksInput,
    ScopedSearchSessionsInput,
    SessionFilter,
    SessionOrder,
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
    TerminateSessionsInput,
    UpdateSessionInput,
)
from ai.backend.common.dto.manager.v2.session.response import (
    AdminSearchSessionsPayload,
    EnqueueSessionPayload,
    ExcludeSessionIdleChecksFailureInfo,
    ExcludeSessionIdleChecksPayload,
    IncludeSessionIdleChecksFailureInfo,
    IncludeSessionIdleChecksPayload,
    SessionIdleCheckTargetInfo,
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
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    SessionScope,
    SessionStatusFilter,
)
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    KernelId,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.common.types import ResourceSlotEntry as DataResourceSlotEntry
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus, KernelStatusInMatchSpec
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.data.session.compute_schedule import ComputeScheduleKernelResult
from ai.backend.manager.data.session.draft import KernelResourceInput
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session.types import (
    SessionData,
    SessionStatus,
    SessionTerminationStatus,
)
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.kernel.conditions import KernelConditions
from ai.backend.manager.models.kernel.orders import (
    DEFAULT_FORWARD_ORDER as KERNEL_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.kernel.orders import (
    resolve_order as resolve_kernel_order,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel.searchers import KernelSearcher
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.session.orders import (
    DEFAULT_FORWARD_ORDER as SESSION_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.session.orders import (
    resolve_order as resolve_session_order,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.searchers import SessionSearcher
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair
from ai.backend.manager.services.idle_checker.actions.exclude_sessions import (
    ExcludeSessionIdleChecksAction,
)
from ai.backend.manager.services.idle_checker.actions.include_sessions import (
    IncludeSessionIdleChecksAction,
)
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.session.actions.batch_get_kernel_resource_allocation import (
    BatchGetKernelResourceAllocationAction,
)
from ai.backend.manager.services.session.actions.batch_get_session_resource_allocation import (
    BatchGetSessionResourceAllocationAction,
)
from ai.backend.manager.services.session.actions.bulk_get import BulkGetSessionsAction
from ai.backend.manager.services.session.actions.bulk_get_kernels import BulkGetKernelsAction
from ai.backend.manager.services.session.actions.compute_schedule import (
    ComputeScheduleAction,
)
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionBatchSpec,
    SessionExecutionSpec,
    SessionResourceSpec,
    SessionSchedulingSpec,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
)
from ai.backend.manager.services.session.actions.get_session import GetSessionAction
from ai.backend.manager.services.session.actions.global_search import GlobalSearchSessionsAction
from ai.backend.manager.services.session.actions.global_search_kernels import (
    GlobalSearchKernelsAction,
)
from ai.backend.manager.services.session.actions.rename_session import RenameSessionAction
from ai.backend.manager.services.session.actions.scoped_search import (
    DomainSessionScopeItem,
    ProjectSessionScopeItem,
    ScopedSearchSessionsAction,
    SessionScopeItem,
    UserSessionScopeItem,
)
from ai.backend.manager.services.session.actions.scoped_search_kernels import (
    ScopedSearchKernelsAction,
)
from ai.backend.manager.services.session.actions.shutdown_service import ShutdownServiceAction
from ai.backend.manager.services.session.actions.start_service import StartServiceAction
from ai.backend.manager.services.session.actions.terminate_sessions import (
    TerminateSessionsAction,
)
from ai.backend.manager.services.session.processors import SessionProcessors


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
    cursor_column=SessionRow.id,
)

_KERNEL_PAGINATION_SPEC = PaginationSpec(
    forward_order=KERNEL_DEFAULT_FORWARD_ORDER,
    cursor_column=KernelRow.id,
)


class SessionAdapter(BaseAdapter):
    """Adapter for session and kernel domain operations."""

    _session: SessionProcessors
    _idle_checker: IdleCheckerProcessors

    def __init__(self, session: SessionProcessors, idle_checker: IdleCheckerProcessors) -> None:
        self._session = session
        self._idle_checker = idle_checker

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
        """Enqueue a new session for scheduling.

        When ``input.owner_id`` is set, the session is created on behalf of the
        target user: their default access key, role, and domain are used in place
        of the caller's. Resolution and authorization of the delegated user
        are handled by the downstream session service, not by this adapter.
        """
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

        mounts: list[MountInfoEntry] | None = None
        if input.mounts is not None:
            mounts = [
                MountInfoEntry(
                    vfolder_id=VFolderUUID(m.vfolder_id),
                    mount_destination=m.mount_path,
                    mount_perm=(MountPermission(m.permission) if m.permission else None),
                    subpath=m.subpath,
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

        parsed_entries = []
        for e in input.resource_entries:
            parsed_entries.append(
                DataResourceSlotEntry(
                    resource_type=ResourceSlotName(e.resource_type), quantity=e.quantity
                )
            )
        requested_slots = DataResourceSlotEntry.inputs_to_resource_slot(parsed_entries)
        resource_entries = []
        for e in input.resource_entries:
            if requested_slots.get(e.resource_type, Decimal(0)) == 0:
                continue
            resource_entries.append(
                ResourceSlotEntry(
                    resource_type=e.resource_type,
                    quantity=e.quantity,
                )
            )
        action = EnqueueSessionAction(
            project_id=ProjectID(group_id),
            session_name=input.session_name,
            session_type=SessionTypes(input.session_type.value),
            image_id=input.image_id,
            resource=SessionResourceSpec(
                entries=resource_entries,
                resource_group=input.resource_group,
                resource_group_id=input.resource_group_id,
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
                job_priority=input.job_priority,
                is_preemptible=input.is_preemptible,
                dependencies=input.dependencies,
                agent_list=input.agent_list,
                agent_selection_policy=(
                    AgentSelectionPolicy(input.agent_selection_policy.value)
                    if input.agent_selection_policy is not None
                    else None
                ),
                attach_network=input.attach_network,
            ),
            batch=batch_spec,
            tag=input.tag,
            callback_url=input.callback_url,
            user_id=UserID(user_id),
            user_role=UserRole(user_role),
            access_key=AccessKey(access_key),
            domain_name=domain_name,
            group_id=group_id,
            owner_id=input.owner_id,
        )

        result = await self._session.enqueue_session.run(action)
        return EnqueueSessionPayload(
            session=(await self._session_data_to_nodes([result.session_data]))[0],
        )

    # -------------------------------------------------------------------------
    # Compute schedule
    # -------------------------------------------------------------------------

    async def compute_schedule(self, input: ComputeScheduleInput) -> ComputeSchedulePayload:
        """Probe whether each kernel of a would-be session fits the target
        resource group's nodes, without provisioning.

        The read is answered for the named resource group, so the action carries
        that group as its entity and the gate checks read on it.
        """
        cluster_mode = (
            ClusterMode.MULTI_NODE
            if input.cluster_mode == ClusterModeEnum.MULTI_NODE
            else ClusterMode.SINGLE_NODE
        )
        kernels = [
            KernelResourceInput(
                image_id=kernel.image_id,
                resources=tuple(
                    DataResourceSlotEntry(
                        resource_type=ResourceSlotName(entry.resource_type),
                        quantity=entry.quantity,
                    )
                    for entry in kernel.resources
                ),
            )
            for kernel in input.kernels
        ]
        action = ComputeScheduleAction(
            kernels=kernels,
            cluster_mode=cluster_mode,
            resource_group_id=input.resource_group_id,
            designated_agent_ids=input.designated_agent_ids,
            agent_selection_policy=(
                AgentSelectionPolicy(input.agent_selection_policy.value)
                if input.agent_selection_policy is not None
                else None
            ),
        )
        result = await self._session.compute_schedule.run(action)
        return ComputeSchedulePayload(
            results=[
                self._compute_schedule_kernel_result_to_info(kernel_result)
                for kernel_result in result.result.kernel_results
            ],
        )

    @staticmethod
    def _compute_schedule_kernel_result_to_info(
        result: ComputeScheduleKernelResult,
    ) -> ComputeScheduleKernelResultInfo:
        """Map the internal per-kernel fitting outcome onto its response DTO."""
        reason_hint: UnschedulableReasonHintInfo | None = None
        hint = result.reason_hint
        if hint is not None:
            required_reduction = (
                [
                    ResourceSlotEntryInfo(
                        resource_type=entry.resource_type,
                        quantity=Decimal(entry.quantity),
                    )
                    for entry in hint.required_reduction
                ]
                if hint.required_reduction is not None
                else None
            )
            reason_hint = UnschedulableReasonHintInfo(
                required_reduction=required_reduction,
            )
        return ComputeScheduleKernelResultInfo(
            requested_slots=[
                ResourceSlotEntryInfo(
                    resource_type=entry.resource_type,
                    quantity=Decimal(entry.quantity),
                )
                for entry in result.requested_slots
            ],
            requested_architecture=result.requested_architecture,
            success=result.success,
            reason_hint=reason_hint,
        )

    # -------------------------------------------------------------------------
    # Get single session
    # -------------------------------------------------------------------------

    async def get(self, session_id: SessionId) -> SessionNode:
        """Get a single session by ID with RBAC validation."""
        action_result = await self._session.get_session.run(
            GetSessionAction(session_id=SessionID(session_id))
        )
        return (await self._session_data_to_nodes([action_result.session_data]))[0]

    # -------------------------------------------------------------------------
    # Batch load (DataLoader)
    # -------------------------------------------------------------------------

    async def batch_load_by_ids(
        self, session_ids: Sequence[SessionID]
    ) -> list[SessionNode | Exception | None]:
        """Batch load sessions by their IDs for DataLoader use, checked per session."""
        if not session_ids:
            return []
        result = await self._session.bulk_get.run(BulkGetSessionsAction(ids=list(session_ids)))
        nodes = iter(
            await self._session_data_to_nodes([
                item.value.to_session_data() for item in result.items if item.value is not None
            ])
        )
        return [
            next(nodes) if item.value is not None else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def batch_load_kernels_by_ids(
        self, kernel_ids: Sequence[KernelID]
    ) -> list[KernelNode | Exception | None]:
        """Batch load kernels for DataLoader use, checked per owning session."""
        if not kernel_ids:
            return []
        ids = list(kernel_ids)
        try:
            result = await self._session.bulk_get_kernels.run(BulkGetKernelsAction(ids=ids))
        except NotFoundError:
            return [None for _ in ids]
        readable = [
            result.successes[kernel_id] for kernel_id in ids if kernel_id in result.successes
        ]
        nodes = dict(
            zip(
                [KernelID(info.id) for info in readable],
                await self._kernel_infos_to_nodes(readable),
                strict=True,
            )
        )
        return [
            nodes[kernel_id]
            if kernel_id in nodes
            else self.batch_load_failure(result.errors.get(kernel_id))
            for kernel_id in ids
        ]

    @staticmethod
    def _aggregate_to_allocation_dto(
        aggregate: ResourceAllocationAggregate | None,
    ) -> ResourceAllocationGQLDTO:
        """Convert a per-owner resource-allocation aggregate to the shared GQL DTO.

        A missing aggregate (owner with no resource_allocations rows) maps to empty
        slot sets rather than null.
        """

        def _to_info(slots: ResourceSlot | None) -> ResourceSlotInfo:
            return ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type=k, quantity=Decimal(str(v)))
                    for k, v in (slots or {}).items()
                ]
            )

        return ResourceAllocationGQLDTO(
            requested=_to_info(aggregate.requested if aggregate else None),
            used=_to_info(aggregate.used if aggregate else None),
            allocated=_to_info(aggregate.allocated if aggregate else None),
        )

    async def batch_resource_allocation_by_session(
        self, session_ids: Sequence[SessionID]
    ) -> list[ResourceAllocationGQLDTO | Exception]:
        """Batch-aggregate resource_allocations per session for DataLoader use.

        Returns one DTO per input session id, in the same order. A session the caller
        may not read answers with its denial.
        """
        if not session_ids:
            return []
        action_result = await self._session.batch_get_session_resource_allocation.run(
            BatchGetSessionResourceAllocationAction(
                session_ids=[SessionId(sid) for sid in session_ids]
            )
        )
        answers: list[ResourceAllocationGQLDTO | Exception] = []
        for item in action_result.items:
            error = self.batch_load_failure(item.error)
            if error is not None:
                answers.append(error)
                continue
            answers.append(self._aggregate_to_allocation_dto(item.value))
        return answers

    async def batch_resource_allocation_by_kernel(
        self, kernel_ids: Sequence[KernelID]
    ) -> list[ResourceAllocationGQLDTO]:
        """Batch-aggregate resource_allocations per kernel for DataLoader use.

        Returns one DTO per input kernel id, in the same order.
        """
        if not kernel_ids:
            return []
        action_result = await self._session.batch_get_kernel_resource_allocation.run(
            BatchGetKernelResourceAllocationAction(kernel_ids=list(kernel_ids))
        )
        return [
            self._aggregate_to_allocation_dto(action_result.data.get(KernelId(kid)))
            for kid in kernel_ids
        ]

    async def _session_data_to_nodes(self, data: Sequence[SessionData]) -> list[SessionNode]:
        """Convert session data to nodes, batch-loading their slot allocations."""
        allocations = await self.batch_resource_allocation_by_session([
            SessionID(item.id) for item in data
        ])
        nodes: list[SessionNode] = []
        for item, allocation in zip(data, allocations, strict=True):
            if isinstance(allocation, Exception):
                raise allocation
            nodes.append(self._session_data_to_node(item, allocation))
        return nodes

    async def _kernel_infos_to_nodes(self, data: Sequence[KernelInfo]) -> list[KernelNode]:
        """Convert kernel infos to nodes, batch-loading their slot allocations."""
        allocations = await self.batch_resource_allocation_by_kernel([
            KernelID(item.id) for item in data
        ])
        return [
            self._kernel_info_to_node(item, allocation)
            for item, allocation in zip(data, allocations, strict=True)
        ]

    # -------------------------------------------------------------------------
    # Session search
    # -------------------------------------------------------------------------

    async def admin_search(
        self,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions (admin, no scope) with filters, orders, and pagination."""
        action_result = await self._session.global_search.run(
            GlobalSearchSessionsAction(searcher=self._build_session_searcher(input))
        )

        return AdminSearchSessionsPayload(
            items=await self._session_data_to_nodes([
                item.to_session_data() for item in action_result.items
            ]),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_sessions_by_agent(
        self,
        agent_id: AgentId,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search the sessions with a kernel on a specific agent (superadmin)."""
        searcher = self._build_searcher(
            SessionSearcher,
            conditions=[
                SessionConditions.by_agent_id(agent_id),
                *(self._convert_session_filter(input.filter) if input.filter else []),
            ],
            orders=self._convert_session_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._session.global_search.run(
            GlobalSearchSessionsAction(searcher=searcher)
        )

        return AdminSearchSessionsPayload(
            items=await self._session_data_to_nodes([
                item.to_session_data() for item in action_result.items
            ]),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def my_search(self, input: AdminSearchSessionsInput) -> AdminSearchSessionsPayload:
        """Search sessions owned by the current user."""
        action_result = await self._session.scoped_search.run(
            ScopedSearchSessionsAction(
                items=[UserSessionScopeItem(user_id=UserID(self._require_user_id()))],
                searcher=self._build_session_searcher(input),
            )
        )
        return AdminSearchSessionsPayload(
            items=await self._session_data_to_nodes([
                item.to_session_data() for item in action_result.items
            ]),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_by_project(
        self,
        project_id: ProjectID,
        input: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions within a project, cursor-based pagination."""
        action_result = await self._session.scoped_search.run(
            ScopedSearchSessionsAction(
                items=[ProjectSessionScopeItem(project_id=project_id)],
                searcher=self._build_session_searcher(input),
            )
        )
        return AdminSearchSessionsPayload(
            items=await self._session_data_to_nodes([
                item.to_session_data() for item in action_result.items
            ]),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _scope_items(self, scope: SessionScope) -> list[SessionScopeItem]:
        """The scope items the request named, in the order the input lists them."""
        items: list[SessionScopeItem] = [
            DomainSessionScopeItem(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        items.extend(
            ProjectSessionScopeItem(project_id=ProjectID(entry.value))
            for entry in scope.project or ()
        )
        items.extend(
            UserSessionScopeItem(user_id=UserID(entry.value)) for entry in scope.user or ()
        )
        return items

    async def scoped_search(
        self,
        input: ScopedSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search the sessions the named scopes reach, combined with OR."""
        action_result = await self._session.scoped_search.run(
            ScopedSearchSessionsAction(
                items=self._scope_items(input.scope),
                searcher=self._build_scoped_session_searcher(input),
            )
        )
        return AdminSearchSessionsPayload(
            items=await self._session_data_to_nodes([
                item.to_session_data() for item in action_result.items
            ]),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_scoped_session_searcher(self, input: ScopedSearchSessionsInput) -> SessionSearcher:
        return self._build_searcher(
            SessionSearcher,
            conditions=self._convert_session_filter(input.filter) if input.filter else [],
            orders=self._convert_session_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_session_searcher(self, input: AdminSearchSessionsInput) -> SessionSearcher:
        return self._build_searcher(
            SessionSearcher,
            conditions=self._convert_session_filter(input.filter) if input.filter else [],
            orders=self._convert_session_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    async def project_search(
        self, project_id: UUID, input: AdminSearchSessionsInput
    ) -> AdminSearchSessionsPayload:
        """Search sessions within a specific project."""
        return await self.gql_search_by_project(ProjectID(project_id), input)

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
        if f.status is not None:
            conditions.extend(self._convert_session_status_filter(f.status))
        if f.created_at is not None:
            c = f.created_at.build_query_condition(
                before_factory=SessionConditions.by_created_at_before,
                after_factory=SessionConditions.by_created_at_after,
                equals_factory=SessionConditions.by_created_at_equals,
            )
            if c is not None:
                conditions.append(c)
        if f.labels is not None:
            conditions.extend(
                self.apply_to_many_filter(
                    f.labels, SessionConditions.labels, self._convert_entity_label_filter
                )
            )
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
    def _convert_session_status_filter(f: SessionStatusFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.equals is not None:
            conditions.append(SessionConditions.by_status_equals(SessionStatus(f.equals.value)))
        if f.in_:
            conditions.append(
                SessionConditions.by_status_in([SessionStatus(s.value) for s in f.in_])
            )
        if f.not_equals is not None:
            conditions.append(
                SessionConditions.by_status_not_equals(SessionStatus(f.not_equals.value))
            )
        if f.not_in:
            conditions.append(
                SessionConditions.by_status_not_in([SessionStatus(s.value) for s in f.not_in])
            )
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
        action_result = await self._session.global_search_kernels.run(
            GlobalSearchKernelsAction(searcher=self._build_kernel_searcher(input))
        )

        return AdminSearchKernelsPayload(
            items=await self._kernel_infos_to_nodes(action_result.items),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_kernels_by_agent(
        self,
        agent_id: AgentId,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search the kernels on a specific agent (superadmin)."""
        action_result = await self._session.global_search_kernels.run(
            GlobalSearchKernelsAction(
                searcher=self._build_kernel_searcher(
                    input, base_condition=KernelConditions.by_agent_id(agent_id)
                )
            )
        )

        return AdminSearchKernelsPayload(
            items=await self._kernel_infos_to_nodes(action_result.items),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_kernels_by_session(
        self,
        session_id: SessionId,
        input: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search the kernels of a specific session, authorized on that session."""
        action_result = await self._session.scoped_search_kernels.run(
            ScopedSearchKernelsAction(
                session_ids=[SessionID(session_id)],
                searcher=self._build_kernel_searcher(input),
            )
        )

        return AdminSearchKernelsPayload(
            items=await self._kernel_infos_to_nodes(action_result.items),
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_kernel_searcher(
        self,
        input: AdminSearchKernelsInput,
        base_condition: QueryCondition | None = None,
    ) -> KernelSearcher:
        conditions = [base_condition] if base_condition is not None else []
        if input.filter:
            conditions.extend(self._convert_kernel_filter(input.filter))
        return self._build_searcher(
            KernelSearcher,
            conditions=conditions,
            orders=self._convert_kernel_orders(input.order) if input.order else [],
            pagination_spec=_KERNEL_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
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
            conditions.extend(self._convert_kernel_status_filter(f.status))
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
    def _convert_kernel_status_filter(f: KernelStatusFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.equals is not None:
            conditions.append(
                KernelConditions.by_status_filter_in(
                    KernelStatusInMatchSpec(values=[KernelStatus(f.equals)], negated=False)
                )
            )
        if f.in_:
            conditions.append(
                KernelConditions.by_status_filter_in(
                    KernelStatusInMatchSpec(values=[KernelStatus(s) for s in f.in_], negated=False)
                )
            )
        if f.not_equals is not None:
            conditions.append(
                KernelConditions.by_status_filter_in(
                    KernelStatusInMatchSpec(values=[KernelStatus(f.not_equals)], negated=True)
                )
            )
        if f.not_in:
            conditions.append(
                KernelConditions.by_status_filter_in(
                    KernelStatusInMatchSpec(
                        values=[KernelStatus(s) for s in f.not_in], negated=True
                    )
                )
            )
        return conditions

    @staticmethod
    def _convert_kernel_orders(orders: list[KernelOrder]) -> list[QueryOrder]:
        return [resolve_kernel_order(o.field, o.direction) for o in orders]

    # -------------------------------------------------------------------------
    # Terminate
    # -------------------------------------------------------------------------

    async def terminate(self, input: TerminateSessionsInput) -> TerminateSessionsPayload:
        """Terminate one or more sessions.

        The action answers per session; a denial is raised here because the payload
        has no place for a session that was not acted on.
        """
        action = TerminateSessionsAction(
            session_ids=[SessionId(sid) for sid in input.session_ids],
            forced=input.forced,
        )
        result = await self._session.terminate_sessions.run(action)
        denied = next((item.error for item in result.items if item.is_denied), None)
        if denied is not None:
            raise denied
        by_state: dict[SessionTerminationStatus, list[SessionId]] = defaultdict(list)
        for item in result.items:
            if item.value is not None:
                by_state[item.value].append(SessionId(item.entity_id))
        return TerminateSessionsPayload(
            cancelled=by_state[SessionTerminationStatus.CANCELLED],
            terminating=by_state[SessionTerminationStatus.TERMINATING],
            force_terminated=by_state[SessionTerminationStatus.FORCE_TERMINATED],
            skipped=by_state[SessionTerminationStatus.SKIPPED],
        )

    async def exclude_idle_checks(
        self, input: ExcludeSessionIdleChecksInput
    ) -> ExcludeSessionIdleChecksPayload:
        """Exclude checker-session pairs from idle checks."""
        result = await self._idle_checker.exclude_sessions.run(
            ExcludeSessionIdleChecksAction(
                targets=[
                    SessionIdleCheckPair(
                        session_id=SessionId(target.session_id),
                        checker_id=target.checker_id,
                    )
                    for target in input.targets
                ],
                user_id=UserID(self._require_user_id()),
            )
        )
        return ExcludeSessionIdleChecksPayload(
            items=[
                SessionIdleCheckTargetInfo(
                    checker_id=item.pair.checker_id,
                    session_id=SessionID(item.pair.session_id),
                )
                for item in result.results
                if item.applied
            ],
            failed=[
                ExcludeSessionIdleChecksFailureInfo(
                    checker_id=item.pair.checker_id,
                    session_id=SessionID(item.pair.session_id),
                    message=str(item.error) if item.error is not None else "Not excluded.",
                )
                for item in result.results
                if not item.applied
            ],
        )

    async def include_idle_checks(
        self, input: IncludeSessionIdleChecksInput
    ) -> IncludeSessionIdleChecksPayload:
        """Re-include previously excluded checker-session pairs into idle checks."""
        result = await self._idle_checker.include_sessions.run(
            IncludeSessionIdleChecksAction(
                targets=[
                    SessionIdleCheckPair(
                        session_id=SessionId(target.session_id),
                        checker_id=target.checker_id,
                    )
                    for target in input.targets
                ],
                user_id=UserID(self._require_user_id()),
            )
        )
        return IncludeSessionIdleChecksPayload(
            items=[
                SessionIdleCheckTargetInfo(
                    checker_id=item.pair.checker_id,
                    session_id=SessionID(item.pair.session_id),
                )
                for item in result.results
                if item.applied
            ],
            failed=[
                IncludeSessionIdleChecksFailureInfo(
                    checker_id=item.pair.checker_id,
                    session_id=SessionID(item.pair.session_id),
                    message=str(item.error) if item.error is not None else "Not included.",
                )
                for item in result.results
                if not item.applied
            ],
        )

    # -------------------------------------------------------------------------
    # Service management
    # -------------------------------------------------------------------------

    async def start_service(
        self,
        session_id: SessionID,
        input: StartSessionServiceInput,
    ) -> StartSessionServicePayload:
        """Start an app service in a session."""
        action = StartServiceAction(
            session_id=SessionID(session_id),
            service=input.service,
            login_session_token=input.login_session_token,
            port=input.port,
            arguments=json.dumps(input.arguments) if input.arguments else None,
            envs=json.dumps(input.envs) if input.envs else None,
        )
        result = await self._session.start_service.run(action)
        return StartSessionServicePayload(token=result.token, wsproxy_addr=result.wsproxy_addr)

    async def shutdown_service(
        self,
        session_id: UUID,
        input: ShutdownSessionServiceInput,
        access_key: str,
    ) -> None:
        """Shut down a service in a session."""
        action = ShutdownServiceAction(
            session_id=SessionID(session_id),
            session_name=str(session_id),
            owner_access_key=AccessKey(access_key),
            service_name=input.service,
        )
        await self._session.shutdown_service.run(action)

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
            session_id=SessionID(session_id),
            session_name=str(session_id),
            owner_access_key=AccessKey(access_key),
            kernel_id=KernelId(kernel_id) if kernel_id else None,
        )
        result = await self._session.get_container_logs.run(action)
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
                session_id=SessionID(session_id),
                session_name=str(session_id),
                new_name=input.name,
                owner_access_key=AccessKey(access_key),
            )
            result = await self._session.rename_session.run(action)
            return UpdateSessionPayload(
                session=(await self._session_data_to_nodes([result.session_data]))[0]
            )
        # If no fields to update, just return the current session
        session_node = await self.get(SessionId(session_id))
        return UpdateSessionPayload(session=session_node)

    # -------------------------------------------------------------------------
    # Data → DTO conversion
    # -------------------------------------------------------------------------

    @staticmethod
    def _session_data_to_node(
        data: SessionData, allocation: ResourceAllocationGQLDTO
    ) -> SessionNode:
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
            entity_id=data.entity_id(),
            image_ids=data.image_ids,
            domain_name=data.domain_name,
            user_id=UserID(data.user_uuid),
            project_id=data.group_id,
            metadata=SessionMetadataInfoGQLDTO(
                creation_id=data.creation_id or "",
                name=data.name or "",
                session_type=data.session_type.value,
                access_key=str(data.access_key) if data.access_key else "",
                cluster_mode=data.cluster_mode.name,
                cluster_size=data.cluster_size,
                priority=data.priority,
                job_priority=data.job_priority,
                is_preemptible=data.is_preemptible,
                tag=data.tag,
            ),
            resource=SessionResourceInfoGQLDTO(
                allocation=allocation,
                resource_group_name=data.resource_group_name,
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
            replica_id=data.replica_id,
        )

    @staticmethod
    def _kernel_info_to_node(info: KernelInfo, allocation: ResourceAllocationGQLDTO) -> KernelNode:
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
            field_id=info.id,
            image_id=info.image.image_id,
            startup_command=info.runtime.startup_command,
            session_info=KernelSessionInfoGQLDTO(
                session_id=UUID(info.session.session_id),
                creation_id=info.session.creation_id,
                name=info.session.name,
                session_type=info.session.session_type.value,
            ),
            user_info=KernelUserInfoGQLDTO(
                user_id=UserID(info.user_permission.user_uuid),
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
                resource_group_name=info.resource.resource_group,
                container_id=info.resource.container_id,
                allocation=allocation,
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
