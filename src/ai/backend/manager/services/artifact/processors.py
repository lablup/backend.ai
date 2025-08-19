from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.authorize import (
    AuthorizeArtifactAction,
    AuthorizeArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact.actions.delete import (
    DeleteArtifactAction,
    DeleteArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
    GetArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.list import (
    ListArtifactsAction,
    ListArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.unauthorize import (
    UnauthorizeArtifactAction,
    UnauthorizeArtifactActionResult,
)

from .service import ArtifactService


class ArtifactProcessors(AbstractProcessorPackage):
    scan: ActionProcessor[ScanArtifactsAction, ScanArtifactsActionResult]
    import_: ActionProcessor[ImportArtifactAction, ImportArtifactActionResult]
    cancel_import: ActionProcessor[CancelImportAction, CancelImportActionResult]
    associate_with_storage: ActionProcessor[
        AssociateWithStorageAction, AssociateWithStorageActionResult
    ]
    disassociate_with_storage: ActionProcessor[
        DisassociateWithStorageAction, DisassociateWithStorageActionResult
    ]
    authorize: ActionProcessor[AuthorizeArtifactAction, AuthorizeArtifactActionResult]
    unauthorize: ActionProcessor[UnauthorizeArtifactAction, UnauthorizeArtifactActionResult]
    delete: ActionProcessor[DeleteArtifactAction, DeleteArtifactActionResult]
    get: ActionProcessor[GetArtifactAction, GetArtifactActionResult]
    list_artifacts: ActionProcessor[ListArtifactsAction, ListArtifactsActionResult]

    def __init__(self, service: ArtifactService, action_monitors: list[ActionMonitor]) -> None:
        self.scan = ActionProcessor(service.scan, action_monitors)
        self.import_ = ActionProcessor(service.import_, action_monitors)
        self.cancel_import = ActionProcessor(service.cancel_import, action_monitors)
        self.associate_with_storage = ActionProcessor(
            service.associate_with_storage, action_monitors
        )
        self.disassociate_with_storage = ActionProcessor(
            service.disassociate_with_storage, action_monitors
        )
        self.authorize = ActionProcessor(service.authorize, action_monitors)
        self.unauthorize = ActionProcessor(service.unauthorize, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_artifacts = ActionProcessor(service.list, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ScanArtifactsAction.spec(),
            ImportArtifactAction.spec(),
            CancelImportAction.spec(),
            AssociateWithStorageAction.spec(),
            DisassociateWithStorageAction.spec(),
            AuthorizeArtifactAction.spec(),
            UnauthorizeArtifactAction.spec(),
            DeleteArtifactAction.spec(),
            GetArtifactAction.spec(),
            ListArtifactsAction.spec(),
        ]
