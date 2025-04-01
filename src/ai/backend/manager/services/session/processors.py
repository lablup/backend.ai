from ai.backend.manager.actions.processor import ActionProcessor
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
from ai.backend.manager.services.session.actions.destory_session import (
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
from ai.backend.manager.services.session.actions.get_task_logs import (
    GetTaskLogsAction,
    GetTaskLogsActionResult,
)
from ai.backend.manager.services.session.actions.interrupt import (
    InterruptAction,
    InterruptActionResult,
)
from ai.backend.manager.services.session.actions.list_files import (
    ListFilesAction,
    ListFilesActionResult,
)
from ai.backend.manager.services.session.service import SessionService


class SessionProcessors:
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
    get_task_logs: ActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]
    interrupt: ActionProcessor[InterruptAction, InterruptActionResult]
    list_files: ActionProcessor[ListFilesAction, ListFilesActionResult]

    def __init__(self, service: SessionService) -> None:
        self.commit_session = ActionProcessor(service.commit_session)
        self.complete = ActionProcessor(service.complete)
        self.convert_session_to_image = ActionProcessor(service.convert_session_to_image)
        self.create_cluster = ActionProcessor(service.create_cluster)
        self.create_from_params = ActionProcessor(service.create_from_params)
        self.create_from_template = ActionProcessor(service.create_from_template)
        self.destroy_session = ActionProcessor(service.destroy_session)
        self.download_file = ActionProcessor(service.download_file)
        self.download_files = ActionProcessor(service.download_files)
        self.execute_session = ActionProcessor(service.execute_session)
        self.get_abusing_report = ActionProcessor(service.get_abusing_report)
        self.get_commit_status = ActionProcessor(service.get_commit_status)
        self.get_container_logs = ActionProcessor(service.get_container_logs)
        self.get_dependency_graph = ActionProcessor(service.get_dependency_graph)
        self.get_direct_access_info = ActionProcessor(service.get_direct_access_info)
        self.get_session_info = ActionProcessor(service.get_session_info)
        self.get_task_logs = ActionProcessor(service.get_task_logs)
        self.interrupt = ActionProcessor(service.interrupt)
        self.list_files = ActionProcessor(service.list_files)
