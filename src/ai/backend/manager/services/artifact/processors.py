from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)

from .service import ArtifactService


class ArtifactProcessors(AbstractProcessorPackage):
    import_: ActionProcessor[ImportArtifactAction, ImportArtifactActionResult]
    scan: ActionProcessor[ScanArtifactsAction, ScanArtifactsActionResult]
    associate_with_storage: ActionProcessor[
        AssociateWithStorageAction, AssociateWithStorageActionResult
    ]
    disassociate_with_storage: ActionProcessor[
        DisassociateWithStorageAction, DisassociateWithStorageActionResult
    ]

    def __init__(self, service: ArtifactService, action_monitors: list[ActionMonitor]) -> None:
        self.import_ = ActionProcessor(service.import_, action_monitors)
        self.scan = ActionProcessor(service.scan, action_monitors)
        self.associate_with_storage = ActionProcessor(
            service.associate_with_storage, action_monitors
        )
        self.disassociate_with_storage = ActionProcessor(
            service.disassociate_with_storage, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ImportArtifactAction.spec(),
            ScanArtifactsAction.spec(),
            AssociateWithStorageAction.spec(),
            DisassociateWithStorageAction.spec(),
        ]
