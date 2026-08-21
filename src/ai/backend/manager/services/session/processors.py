from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import PublicActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.services.session.actions.batch_get_kernel_resource_allocation import (
    BatchGetKernelResourceAllocationAction,
    BatchGetKernelResourceAllocationActionResult,
)
from ai.backend.manager.services.session.actions.batch_get_session_resource_allocation import (
    BatchGetSessionResourceAllocationAction,
    BatchGetSessionResourceAllocationActionResult,
)
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.actions.compute_schedule import (
    ComputeScheduleAction,
    ComputeScheduleActionResult,
)
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
    ConvertSessionToImageActionResult,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
    CreateClusterActionResult,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionResult,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionResult,
)
from ai.backend.manager.services.session.actions.destroy_session import (
    DestroySessionAction,
    DestroySessionActionResult,
)
from ai.backend.manager.services.session.actions.download_file import (
    DownloadFileAction,
    DownloadFileActionResult,
)
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
)
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    EnqueueSessionActionResult,
)
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionResult,
)
from ai.backend.manager.services.session.actions.get_abusing_report import (
    GetAbusingReportAction,
    GetAbusingReportActionResult,
)
from ai.backend.manager.services.session.actions.get_commit_status import (
    GetCommitStatusAction,
    GetCommitStatusActionResult,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
    GetContainerLogsActionResult,
)
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
    GetDependencyGraphActionResult,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_session import (
    GetSessionAction,
    GetSessionActionResult,
)
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
    GetStatusHistoryActionResult,
)
from ai.backend.manager.services.session.actions.interrupt_session import (
    InterruptSessionAction,
    InterruptSessionActionResult,
)
from ai.backend.manager.services.session.actions.list_files import (
    ListFilesAction,
    ListFilesActionResult,
)
from ai.backend.manager.services.session.actions.lookup import LookupSessionAction
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
    MatchSessionsActionResult,
)
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
    RenameSessionActionResult,
)
from ai.backend.manager.services.session.actions.resolve_session_name import (
    ResolveSessionNameAction,
    ResolveSessionNameActionResult,
)
from ai.backend.manager.services.session.actions.search import (
    SearchSessionsAction,
    SearchSessionsActionResult,
)
from ai.backend.manager.services.session.actions.search_in_project import (
    SearchSessionsInProjectAction,
    SearchSessionsInProjectActionResult,
)
from ai.backend.manager.services.session.actions.search_kernel import (
    SearchKernelsAction,
    SearchKernelsActionResult,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
)
from ai.backend.manager.services.session.actions.terminate_sessions import (
    TerminateSessionsAction,
    TerminateSessionsActionResult,
)
from ai.backend.manager.services.session.actions.update_session import (
    UpdateSessionAction,
    UpdateSessionActionResult,
)
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.service import SessionService


class SessionProcessors:
    commit_session: SingleEntityActionProcessor[CommitSessionAction, CommitSessionActionResult]
    compute_schedule: PublicActionProcessor[ComputeScheduleAction, ComputeScheduleActionResult]
    complete: SingleEntityActionProcessor[CompleteAction, CompleteActionResult]
    convert_session_to_image: SingleEntityActionProcessor[
        ConvertSessionToImageAction, ConvertSessionToImageActionResult
    ]
    create_cluster: ScopeActionProcessor[CreateClusterAction, CreateClusterActionResult]
    create_from_params: ScopeActionProcessor[
        CreateFromParamsAction,
        CreateFromParamsActionResult,
    ]
    create_from_template: ScopeActionProcessor[
        CreateFromTemplateAction,
        CreateFromTemplateActionResult,
    ]
    enqueue_session: ScopeActionProcessor[EnqueueSessionAction, EnqueueSessionActionResult]
    destroy_session: SingleEntityActionProcessor[DestroySessionAction, DestroySessionActionResult]
    download_file: SingleEntityActionProcessor[DownloadFileAction, DownloadFileActionResult]
    download_files: SingleEntityActionProcessor[DownloadFilesAction, DownloadFilesActionResult]
    execute_session: SingleEntityActionProcessor[ExecuteSessionAction, ExecuteSessionActionResult]
    get_abusing_report: SingleEntityActionProcessor[
        GetAbusingReportAction, GetAbusingReportActionResult
    ]
    get_commit_status: SingleEntityActionProcessor[
        GetCommitStatusAction, GetCommitStatusActionResult
    ]
    get_container_logs: SingleEntityActionProcessor[
        GetContainerLogsAction, GetContainerLogsActionResult
    ]
    get_dependency_graph: SingleEntityActionProcessor[
        GetDependencyGraphAction, GetDependencyGraphActionResult
    ]
    get_direct_access_info: SingleEntityActionProcessor[
        GetDirectAccessInfoAction, GetDirectAccessInfoActionResult
    ]
    get_session_info: SingleEntityActionProcessor[GetSessionInfoAction, GetSessionInfoActionResult]
    get_status_history: SingleEntityActionProcessor[
        GetStatusHistoryAction, GetStatusHistoryActionResult
    ]
    interrupt: SingleEntityActionProcessor[InterruptSessionAction, InterruptSessionActionResult]
    list_files: SingleEntityActionProcessor[ListFilesAction, ListFilesActionResult]
    match_sessions: ScopeActionProcessor[MatchSessionsAction, MatchSessionsActionResult]
    rename_session: SingleEntityActionProcessor[RenameSessionAction, RenameSessionActionResult]
    resolve_session_name: SingleEntityActionProcessor[
        ResolveSessionNameAction, ResolveSessionNameActionResult
    ]
    search_kernels: ScopeActionProcessor[SearchKernelsAction, SearchKernelsActionResult]
    batch_get_session_resource_allocation: BulkActionProcessor[
        BatchGetSessionResourceAllocationAction, BatchGetSessionResourceAllocationActionResult
    ]
    batch_get_kernel_resource_allocation: BulkActionProcessor[
        BatchGetKernelResourceAllocationAction, BatchGetKernelResourceAllocationActionResult
    ]
    search_sessions: ScopeActionProcessor[SearchSessionsAction, SearchSessionsActionResult]
    search_sessions_in_project: ScopeActionProcessor[
        SearchSessionsInProjectAction, SearchSessionsInProjectActionResult
    ]
    shutdown_service: SingleEntityActionProcessor[
        ShutdownServiceAction, ShutdownServiceActionResult
    ]
    start_service: SingleEntityActionProcessor[StartServiceAction, StartServiceActionResult]
    terminate_sessions: BulkActionProcessor[TerminateSessionsAction, TerminateSessionsActionResult]
    upload_files: SingleEntityActionProcessor[UploadFilesAction, UploadFilesActionResult]
    get_session: SingleEntityActionProcessor[GetSessionAction, GetSessionActionResult]
    update_session: SingleEntityActionProcessor[UpdateSessionAction, UpdateSessionActionResult]
    lookup: LookupActionProcessor[LookupSessionAction, LookupOpsResult[SessionEntityData]]

    resource_allocation: ResourceAllocationProcessors

    def __init__(
        self,
        group: ProcessorGroup[SessionEntityData],
        resource_allocation: ResourceAllocationProcessors,
        service: SessionService,
    ) -> None:
        self.resource_allocation = resource_allocation
        # Actions without RBAC validation (internal/legacy)
        self.lookup = group.public_lookup_ops(LookupSessionAction)
        self.commit_session = group.single_entity(CommitSessionAction, service.commit_session)
        self.compute_schedule = group.public(ComputeScheduleAction, service.compute_schedule)
        self.complete = group.single_entity(CompleteAction, service.complete)
        self.convert_session_to_image = group.single_entity(
            ConvertSessionToImageAction, service.convert_session_to_image
        )
        self.download_file = group.single_entity(DownloadFileAction, service.download_file)
        self.download_files = group.single_entity(DownloadFilesAction, service.download_files)
        self.get_abusing_report = group.single_entity(
            GetAbusingReportAction, service.get_abusing_report
        )
        self.get_commit_status = group.single_entity(
            GetCommitStatusAction, service.get_commit_status
        )
        self.get_container_logs = group.single_entity(
            GetContainerLogsAction, service.get_container_logs
        )
        self.get_dependency_graph = group.single_entity(
            GetDependencyGraphAction, service.get_dependency_graph
        )
        self.get_direct_access_info = group.single_entity(
            GetDirectAccessInfoAction, service.get_direct_access_info
        )
        self.get_status_history = group.single_entity(
            GetStatusHistoryAction, service.get_status_history
        )
        self.interrupt = group.single_entity(InterruptSessionAction, service.interrupt)
        self.list_files = group.single_entity(ListFilesAction, service.list_files)
        self.rename_session = group.single_entity(RenameSessionAction, service.rename_session)
        self.resolve_session_name = group.single_entity(
            ResolveSessionNameAction, service.resolve_session_name
        )
        self.shutdown_service = group.single_entity(ShutdownServiceAction, service.shutdown_service)
        self.upload_files = group.single_entity(UploadFilesAction, service.upload_files)

        # Scope actions with RBAC validation
        self.create_cluster = group.scope(CreateClusterAction, service.create_cluster)
        self.enqueue_session = group.scope(EnqueueSessionAction, service.enqueue_session)
        self.create_from_params = group.scope(CreateFromParamsAction, service.create_from_params)
        self.create_from_template = group.scope(
            CreateFromTemplateAction, service.create_from_template
        )
        self.match_sessions = group.scope(MatchSessionsAction, service.match_sessions)
        self.search_kernels = group.scope(SearchKernelsAction, service.search_kernels)
        # Bulk read for GraphQL DataLoaders; ids come from already-authorized
        # session/kernel nodes, so no per-target RBAC re-validation is applied.
        self.batch_get_session_resource_allocation = group.bulk(
            BatchGetSessionResourceAllocationAction, service.batch_get_session_resource_allocation
        )
        self.batch_get_kernel_resource_allocation = group.bulk(
            BatchGetKernelResourceAllocationAction, service.batch_get_kernel_resource_allocation
        )
        self.search_sessions = group.scope(SearchSessionsAction, service.search)
        self.search_sessions_in_project = group.scope(
            SearchSessionsInProjectAction, service.search_in_project
        )
        self.terminate_sessions = group.bulk(TerminateSessionsAction, service.terminate_sessions)

        # Actions without RBAC validation (name-based, no session_id at construction)
        self.destroy_session = group.single_entity(DestroySessionAction, service.destroy_session)
        self.execute_session = group.single_entity(ExecuteSessionAction, service.execute_session)
        self.get_session_info = group.single_entity(GetSessionInfoAction, service.get_session_info)

        # Single entity actions with RBAC validation
        self.get_session = group.single_entity(GetSessionAction, service.get_session)
        self.update_session = group.single_entity(UpdateSessionAction, service.update_session)
        self.start_service = group.single_entity(StartServiceAction, service.start_service)
