from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
)

from .service import ArtifactService


class ArtifactProcessors(AbstractProcessorPackage):
    import_: ActionProcessor[ImportArtifactAction, ImportArtifactActionResult]
    scan: ActionProcessor[ScanArtifactsAction, ScanArtifactsActionResult]

    def __init__(self, service: ArtifactService, action_monitors: list[ActionMonitor]) -> None:
        self.import_ = ActionProcessor(service.import_, action_monitors)
        self.scan = ActionProcessor(service.scan, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            RescanImagesAction.spec(),
            ImportArtifactAction.spec(),
        ]
