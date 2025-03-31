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
