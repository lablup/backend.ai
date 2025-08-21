from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.delete import (
    DeleteArtifactAction,
    DeleteArtifactActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.disapprove import (
    DisapproveArtifactRevisionAction,
    DisapproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


class ArtifactRevisionProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetArtifactRevisionAction, GetArtifactRevisionActionResult]
    list_: ActionProcessor[ListArtifactRevisionsAction, ListArtifactRevisionsActionResult]
    approve: ActionProcessor[ApproveArtifactRevisionAction, ApproveArtifactRevisionActionResult]
    disapprove: ActionProcessor[
        DisapproveArtifactRevisionAction, DisapproveArtifactRevisionActionResult
    ]
    import_: ActionProcessor[ImportArtifactAction, ImportArtifactActionResult]
    cancel_import: ActionProcessor[CancelImportAction, CancelImportActionResult]
    delete: ActionProcessor[DeleteArtifactAction, DeleteArtifactActionResult]

    def __init__(
        self, service: ArtifactRevisionService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_ = ActionProcessor(service.list_, action_monitors)
        self.approve = ActionProcessor(service.approve, action_monitors)
        self.disapprove = ActionProcessor(service.disapprove, action_monitors)
        self.import_ = ActionProcessor(service.import_, action_monitors)
        self.cancel_import = ActionProcessor(service.cancel_import, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetArtifactRevisionAction.spec(),
            ListArtifactRevisionsAction.spec(),
            ApproveArtifactRevisionAction.spec(),
            DisapproveArtifactRevisionAction.spec(),
            ImportArtifactAction.spec(),
            CancelImportAction.spec(),
            DeleteArtifactAction.spec(),
        ]
