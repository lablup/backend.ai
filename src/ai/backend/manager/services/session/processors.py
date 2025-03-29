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
from ai.backend.manager.services.session.service import SessionService


class SessionProcessors:
    commit_session: ActionProcessor[CommitSessionAction, CommitSessionActionResult]
    complete: ActionProcessor[CompleteAction, CompleteActionResult]
    convert_session_to_image: ActionProcessor[
        ConvertSessionToImageAction, ConvertSessionToImageActionResult
    ]

    def __init__(self, service: SessionService) -> None:
        self.commit_session = ActionProcessor(service.commit_session)
        self.complete = ActionProcessor(service.complete)
        self.convert_session_to_image = ActionProcessor(service.convert_session_to_image)
