from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
    CheckAndTransitStatusActionResult,
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
from ai.backend.manager.services.session.actions.restart_session import (
    RestartSessionAction,
    RestartSessionActionResult,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
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
    restart_session: ActionProcessor[RestartSessionAction, RestartSessionActionResult]
    shutdown_service: ActionProcessor[ShutdownServiceAction, ShutdownServiceActionResult]
    start_service: ActionProcessor[StartServiceAction, StartServiceActionResult]
    upload_files: ActionProcessor[UploadFilesAction, UploadFilesActionResult]
    modify_session: ActionProcessor[ModifySessionAction, ModifySessionActionResult]
    check_and_transit_status: ActionProcessor[
        CheckAndTransitStatusAction, CheckAndTransitStatusActionResult
    ]

    def __init__(self, service: SessionService, action_monitors: list[ActionMonitor]) -> None:
        self.commit_session = ActionProcessor(service.commit_session, action_monitors)
        self.complete = ActionProcessor(service.complete, action_monitors)
        self.convert_session_to_image = ActionProcessor(
            service.convert_session_to_image, action_monitors
        )
        self.create_cluster = ActionProcessor(service.create_cluster, action_monitors)
        self.create_from_params = ActionProcessor(service.create_from_params, action_monitors)
        self.create_from_template = ActionProcessor(service.create_from_template, action_monitors)
        self.destroy_session = ActionProcessor(service.destroy_session, action_monitors)
        self.download_file = ActionProcessor(service.download_file, action_monitors)
        self.download_files = ActionProcessor(service.download_files, action_monitors)
        self.execute_session = ActionProcessor(service.execute_session, action_monitors)
        self.get_abusing_report = ActionProcessor(service.get_abusing_report, action_monitors)
        self.get_commit_status = ActionProcessor(service.get_commit_status, action_monitors)
        self.get_container_logs = ActionProcessor(service.get_container_logs, action_monitors)
        self.get_dependency_graph = ActionProcessor(service.get_dependency_graph, action_monitors)
        self.get_direct_access_info = ActionProcessor(
            service.get_direct_access_info, action_monitors
        )
        self.get_session_info = ActionProcessor(service.get_session_info, action_monitors)
        self.get_status_history = ActionProcessor(service.get_status_history, action_monitors)
        self.interrupt = ActionProcessor(service.interrupt, action_monitors)
        self.list_files = ActionProcessor(service.list_files, action_monitors)
        self.match_sessions = ActionProcessor(service.match_sessions, action_monitors)
        self.rename_session = ActionProcessor(service.rename_session, action_monitors)
        self.restart_session = ActionProcessor(service.restart_session, action_monitors)
        self.shutdown_service = ActionProcessor(service.shutdown_service, action_monitors)
        self.start_service = ActionProcessor(service.start_service, action_monitors)
        self.upload_files = ActionProcessor(service.upload_files, action_monitors)
        self.modify_session = ActionProcessor(service.modify_session, action_monitors)
        self.check_and_transit_status = ActionProcessor(
            service.check_and_transit_status, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CommitSessionAction.spec(),
            CompleteAction.spec(),
            ConvertSessionToImageAction.spec(),
            CreateClusterAction.spec(),
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
            RestartSessionAction.spec(),
            ShutdownServiceAction.spec(),
            StartServiceAction.spec(),
            UploadFilesAction.spec(),
            ModifySessionAction.spec(),
            CheckAndTransitStatusAction.spec(),
        ]
