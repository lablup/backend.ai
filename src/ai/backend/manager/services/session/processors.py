from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.service import SessionService


class SessionProcessors:
    commit_session: ActionProcessor[CommitSessionAction, CommitSessionActionResult]
    complete: ActionProcessor[CompleteAction, CompleteActionResult]

    def __init__(self, service: SessionService) -> None:
        self.commit_session = ActionProcessor(service.commit_session)
        self.complete = ActionProcessor(service.complete)
