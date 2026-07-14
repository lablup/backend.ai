from typing import cast, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validator.base import ActionValidator
from ai.backend.manager.actions.validators import ActionValidators
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
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
    MatchSessionsActionResult,
)
from ai.backend.manager.services.session.actions.modify_session import (
    ModifySessionAction,
    ModifySessionActionResult,
)
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
    RenameSessionActionResult,
)
from ai.backend.manager.services.session.actions.resolve_session import (
    ResolveSessionAction,
    ResolveSessionActionResult,
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
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.services.session.service import SessionService


class SessionProcessors(AbstractProcessorPackage):
    commit_session: ActionProcessor[CommitSessionAction, CommitSessionActionResult]
    complete: ActionProcessor[CompleteAction, CompleteActionResult]
    convert_session_to_image: ActionProcessor[
        ConvertSessionToImageAction, ConvertSessionToImageActionResult
    ]
    create_cluster: ActionProcessor[CreateClusterAction, CreateClusterActionResult]
    create_from_params: ActionProcessor[
        CreateFromParamsAction,
        CreateFromParamsActionResult,
    ]
    create_from_template: ActionProcessor[
        CreateFromTemplateAction,
        CreateFromTemplateActionResult,
    ]
    enqueue_session: ActionProcessor[EnqueueSessionAction, EnqueueSessionActionResult]
    destroy_session: ActionProcessor[DestroySessionAction, DestroySessionActionResult]
    download_file: ActionProcessor[DownloadFileAction, DownloadFileActionResult]
    download_files: ActionProcessor[DownloadFilesAction, DownloadFilesActionResult]
    execute_session: ActionProcessor[ExecuteSessionAction, ExecuteSessionActionResult]
    get_abusing_report: ActionProcessor[GetAbusingReportAction, GetAbusingReportActionResult]
    get_commit_status: ActionProcessor[GetCommitStatusAction, GetCommitStatusActionResult]
    get_container_logs: ActionProcessor[GetContainerLogsAction, GetContainerLogsActionResult]
    get_dependency_graph: ActionProcessor[GetDependencyGraphAction, GetDependencyGraphActionResult]
    get_direct_access_info: ActionProcessor[
        GetDirectAccessInfoAction, GetDirectAccessInfoActionResult
    ]
    get_session_info: ActionProcessor[GetSessionInfoAction, GetSessionInfoActionResult]
    get_status_history: ActionProcessor[GetStatusHistoryAction, GetStatusHistoryActionResult]
    interrupt: ActionProcessor[InterruptSessionAction, InterruptSessionActionResult]
    list_files: ActionProcessor[ListFilesAction, ListFilesActionResult]
    match_sessions: ActionProcessor[MatchSessionsAction, MatchSessionsActionResult]
    rename_session: ActionProcessor[RenameSessionAction, RenameSessionActionResult]
    resolve_session: ActionProcessor[ResolveSessionAction, ResolveSessionActionResult]
    resolve_session_name: ActionProcessor[ResolveSessionNameAction, ResolveSessionNameActionResult]
    search_kernels: ActionProcessor[SearchKernelsAction, SearchKernelsActionResult]
    batch_get_session_resource_allocation: BulkActionProcessor[
        BatchGetSessionResourceAllocationAction, BatchGetSessionResourceAllocationActionResult
    ]
    batch_get_kernel_resource_allocation: BulkActionProcessor[
        BatchGetKernelResourceAllocationAction, BatchGetKernelResourceAllocationActionResult
    ]
    search_sessions: ActionProcessor[SearchSessionsAction, SearchSessionsActionResult]
    search_sessions_in_project: ActionProcessor[
        SearchSessionsInProjectAction, SearchSessionsInProjectActionResult
    ]
    shutdown_service: ActionProcessor[ShutdownServiceAction, ShutdownServiceActionResult]
    start_service: SingleEntityActionProcessor[StartServiceAction, StartServiceActionResult]
    terminate_sessions: BulkActionProcessor[TerminateSessionsAction, TerminateSessionsActionResult]
    upload_files: ActionProcessor[UploadFilesAction, UploadFilesActionResult]
    get_session: SingleEntityActionProcessor[GetSessionAction, GetSessionActionResult]
    modify_session: SingleEntityActionProcessor[ModifySessionAction, ModifySessionActionResult]

    def __init__(
        self,
        service: SessionService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        scope_validator = validators.rbac.scope
        single_entity_validator = validators.rbac.single_entity

        # Actions without RBAC validation (internal/legacy)
        self.commit_session = ActionProcessor(service.commit_session, action_monitors)
        self.complete = ActionProcessor(service.complete, action_monitors)
        self.convert_session_to_image = ActionProcessor(
            service.convert_session_to_image, action_monitors
        )
        self.download_file = ActionProcessor(service.download_file, action_monitors)
        self.download_files = ActionProcessor(service.download_files, action_monitors)
        self.get_abusing_report = ActionProcessor(service.get_abusing_report, action_monitors)
        self.get_commit_status = ActionProcessor(service.get_commit_status, action_monitors)
        self.get_container_logs = ActionProcessor(service.get_container_logs, action_monitors)
        self.get_dependency_graph = ActionProcessor(service.get_dependency_graph, action_monitors)
        self.get_direct_access_info = ActionProcessor(
            service.get_direct_access_info, action_monitors
        )
        self.get_status_history = ActionProcessor(service.get_status_history, action_monitors)
        self.interrupt = ActionProcessor(service.interrupt, action_monitors)
        self.list_files = ActionProcessor(service.list_files, action_monitors)
        self.rename_session = ActionProcessor(service.rename_session, action_monitors)
        self.resolve_session = ActionProcessor(service.resolve_session, action_monitors)
        self.resolve_session_name = ActionProcessor(service.resolve_session_name, action_monitors)
        self.shutdown_service = ActionProcessor(service.shutdown_service, action_monitors)
        self.upload_files = ActionProcessor(service.upload_files, action_monitors)

        # Scope actions with RBAC validation
        self.create_cluster = ActionProcessor(
            service.create_cluster,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.enqueue_session = ActionProcessor(
            service.enqueue_session,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.create_from_params = ActionProcessor(
            service.create_from_params,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.create_from_template = ActionProcessor(
            service.create_from_template,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.match_sessions = ActionProcessor(
            service.match_sessions,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.search_kernels = ActionProcessor(
            service.search_kernels,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        # Bulk read for GraphQL DataLoaders; ids come from already-authorized
        # session/kernel nodes, so no per-target RBAC re-validation is applied.
        self.batch_get_session_resource_allocation = BulkActionProcessor(
            service.batch_get_session_resource_allocation,
            monitors=action_monitors,
        )
        self.batch_get_kernel_resource_allocation = BulkActionProcessor(
            service.batch_get_kernel_resource_allocation,
            monitors=action_monitors,
        )
        self.search_sessions = ActionProcessor(
            service.search, action_monitors, validators=[cast(ActionValidator, scope_validator)]
        )
        self.search_sessions_in_project = ActionProcessor(
            service.search_in_project,
            action_monitors,
            validators=[cast(ActionValidator, scope_validator)],
        )
        self.terminate_sessions = BulkActionProcessor(
            service.terminate_sessions,
            monitors=action_monitors,
            validators=[validators.rbac.bulk],
        )

        # Actions without RBAC validation (name-based, no session_id at construction)
        self.destroy_session = ActionProcessor(service.destroy_session, action_monitors)
        self.execute_session = ActionProcessor(service.execute_session, action_monitors)
        self.get_session_info = ActionProcessor(service.get_session_info, action_monitors)

        # Single entity actions with RBAC validation
        rbac_single_entity_validators = [single_entity_validator]
        self.get_session = SingleEntityActionProcessor(
            service.get_session,
            action_monitors,
            validators=rbac_single_entity_validators,
        )
        self.modify_session = SingleEntityActionProcessor(
            service.modify_session,
            action_monitors,
            validators=rbac_single_entity_validators,
        )
        self.start_service = SingleEntityActionProcessor(
            service.start_service,
            action_monitors,
            validators=rbac_single_entity_validators,
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CommitSessionAction.spec(),
            CompleteAction.spec(),
            ConvertSessionToImageAction.spec(),
            CreateClusterAction.spec(),
            EnqueueSessionAction.spec(),
            CreateFromParamsAction.spec(),
            CreateFromTemplateAction.spec(),
            DestroySessionAction.spec(),
            DownloadFileAction.spec(),
            DownloadFilesAction.spec(),
            ExecuteSessionAction.spec(),
            GetAbusingReportAction.spec(),
            GetCommitStatusAction.spec(),
            GetContainerLogsAction.spec(),
            GetDependencyGraphAction.spec(),
            GetDirectAccessInfoAction.spec(),
            GetSessionInfoAction.spec(),
            GetStatusHistoryAction.spec(),
            InterruptSessionAction.spec(),
            ListFilesAction.spec(),
            MatchSessionsAction.spec(),
            RenameSessionAction.spec(),
            ResolveSessionAction.spec(),
            ResolveSessionNameAction.spec(),
            SearchKernelsAction.spec(),
            BatchGetSessionResourceAllocationAction.spec(),
            BatchGetKernelResourceAllocationAction.spec(),
            SearchSessionsAction.spec(),
            SearchSessionsInProjectAction.spec(),
            ShutdownServiceAction.spec(),
            StartServiceAction.spec(),
            TerminateSessionsAction.spec(),
            UploadFilesAction.spec(),
            GetSessionAction.spec(),
            ModifySessionAction.spec(),
        ]
