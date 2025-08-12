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

from .service import ArtifactRegistryService


class ArtifactRegistryProcessors(AbstractProcessorPackage):
    create: ActionProcessor[ImportArtifactAction, ImportArtifactActionResult]

    def __init__(self, service: ArtifactRegistryService, action_monitors: list[ActionMonitor]) -> None:
        self.create = 

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ImportArtifactAction.spec(),
            ScanArtifactsAction.spec(),
            AssociateWithStorageAction.spec(),
            DisassociateWithStorageAction.spec(),
        ]
