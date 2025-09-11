from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
    CleanupArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
    GetArtifactRevisionReadmeActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


class ArtifactRevisionProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetArtifactRevisionAction, GetArtifactRevisionActionResult]
    get_readme: ActionProcessor[
        GetArtifactRevisionReadmeAction, GetArtifactRevisionReadmeActionResult
    ]
    list_revision: ActionProcessor[ListArtifactRevisionsAction, ListArtifactRevisionsActionResult]
    approve: ActionProcessor[ApproveArtifactRevisionAction, ApproveArtifactRevisionActionResult]
    reject: ActionProcessor[RejectArtifactRevisionAction, RejectArtifactRevisionActionResult]
    import_revision: ActionProcessor[
        ImportArtifactRevisionAction, ImportArtifactRevisionActionResult
    ]
    cancel_import: ActionProcessor[CancelImportAction, CancelImportActionResult]
    cleanup: ActionProcessor[CleanupArtifactRevisionAction, CleanupArtifactRevisionActionResult]
    associate_with_storage: ActionProcessor[
        AssociateWithStorageAction, AssociateWithStorageActionResult
    ]
    disassociate_with_storage: ActionProcessor[
        DisassociateWithStorageAction, DisassociateWithStorageActionResult
    ]

    def __init__(
        self, service: ArtifactRevisionService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.get_readme = ActionProcessor(service.get_readme, action_monitors)
        self.list_revision = ActionProcessor(service.list_revision, action_monitors)
        self.approve = ActionProcessor(service.approve, action_monitors)
        self.reject = ActionProcessor(service.reject, action_monitors)
        self.import_revision = ActionProcessor(service.import_revision, action_monitors)
        self.cancel_import = ActionProcessor(service.cancel_import, action_monitors)
        self.cleanup = ActionProcessor(service.cleanup, action_monitors)
        self.associate_with_storage = ActionProcessor(
            service.associate_with_storage, action_monitors
        )
        self.disassociate_with_storage = ActionProcessor(
            service.disassociate_with_storage, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetArtifactRevisionAction.spec(),
            GetArtifactRevisionReadmeAction.spec(),
            ListArtifactRevisionsAction.spec(),
            ApproveArtifactRevisionAction.spec(),
            RejectArtifactRevisionAction.spec(),
            ImportArtifactRevisionAction.spec(),
            CancelImportAction.spec(),
            CleanupArtifactRevisionAction.spec(),
            AssociateWithStorageAction.spec(),
            DisassociateWithStorageAction.spec(),
        ]
