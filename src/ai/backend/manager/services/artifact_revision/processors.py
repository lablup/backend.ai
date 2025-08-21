from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


class ArtifactRevisionProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetArtifactRevisionAction, GetArtifactRevisionActionResult]
    list_: ActionProcessor[ListArtifactRevisionsAction, ListArtifactRevisionsActionResult]

    def __init__(
        self, service: ArtifactRevisionService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_ = ActionProcessor(service.list_, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetArtifactRevisionAction.spec(),
            ListArtifactRevisionsAction.spec(),
        ]
