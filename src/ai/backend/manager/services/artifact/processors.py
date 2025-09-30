from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact.actions.delegate_scan import (
    DelegateScanArtifactsAction,
    DelegateScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.delete_multi import (
    DeleteArtifactsAction,
    DeleteArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
    GetArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.get_revisions import (
    GetArtifactRevisionsAction,
    GetArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact.actions.list import (
    ListArtifactsAction,
    ListArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
    ListArtifactsWithRevisionsActionResult,
)
from ai.backend.manager.services.artifact.actions.restore_multi import (
    RestoreArtifactsAction,
    RestoreArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.retrieve_model import (
    RetrieveModelAction,
    RetrieveModelActionResult,
)
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
    RetrieveModelsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan_sync import (
    ScanArtifactsSyncAction,
    ScanArtifactsSyncActionResult,
)
from ai.backend.manager.services.artifact.actions.update import (
    UpdateArtifactAction,
    UpdateArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.upsert_multi import (
    UpsertArtifactsAction,
    UpsertArtifactsActionResult,
)

from .service import ArtifactService


class ArtifactProcessors(AbstractProcessorPackage):
    scan: ActionProcessor[ScanArtifactsAction, ScanArtifactsActionResult]
    scan_sync: ActionProcessor[ScanArtifactsSyncAction, ScanArtifactsSyncActionResult]
    get: ActionProcessor[GetArtifactAction, GetArtifactActionResult]
    list_artifacts: ActionProcessor[ListArtifactsAction, ListArtifactsActionResult]
    list_artifacts_with_revisions: ActionProcessor[
        ListArtifactsWithRevisionsAction, ListArtifactsWithRevisionsActionResult
    ]
    get_revisions: ActionProcessor[GetArtifactRevisionsAction, GetArtifactRevisionsActionResult]
    update: ActionProcessor[UpdateArtifactAction, UpdateArtifactActionResult]
    upsert_artifacts_with_revisions: ActionProcessor[
        UpsertArtifactsAction, UpsertArtifactsActionResult
    ]
    retrieve_models: ActionProcessor[RetrieveModelsAction, RetrieveModelsActionResult]
    retrieve_single_model: ActionProcessor[RetrieveModelAction, RetrieveModelActionResult]
    delete_artifacts: ActionProcessor[DeleteArtifactsAction, DeleteArtifactsActionResult]
    restore_artifacts: ActionProcessor[RestoreArtifactsAction, RestoreArtifactsActionResult]

    delegate_scan: ActionProcessor[DelegateScanArtifactsAction, DelegateScanArtifactsActionResult]

    def __init__(self, service: ArtifactService, action_monitors: list[ActionMonitor]) -> None:
        # TODO: Move scan action to ArtifactRegistryService
        self.scan = ActionProcessor(service.scan, action_monitors)
        self.scan_sync = ActionProcessor(service.scan_sync, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_artifacts = ActionProcessor(service.list, action_monitors)
        self.list_artifacts_with_revisions = ActionProcessor(
            service.list_with_revisions, action_monitors
        )
        self.get_revisions = ActionProcessor(service.get_revisions, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.upsert_artifacts_with_revisions = ActionProcessor(
            service.upsert_artifacts_with_revisions, action_monitors
        )
        self.retrieve_models = ActionProcessor(service.retrieve_models, action_monitors)
        self.retrieve_single_model = ActionProcessor(service.retrieve_single_model, action_monitors)
        self.delete_artifacts = ActionProcessor(service.delete_artifacts, action_monitors)
        self.restore_artifacts = ActionProcessor(service.restore_artifacts, action_monitors)
        self.delegate_scan = ActionProcessor(service.delegate_scan_artifacts, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ScanArtifactsAction.spec(),
            ScanArtifactsSyncAction.spec(),
            DelegateScanArtifactsAction.spec(),
            GetArtifactAction.spec(),
            ListArtifactsAction.spec(),
            ListArtifactsWithRevisionsAction.spec(),
            GetArtifactRevisionsAction.spec(),
            UpdateArtifactAction.spec(),
            UpsertArtifactsAction.spec(),
            RetrieveModelAction.spec(),
            RetrieveModelsAction.spec(),
            DeleteArtifactsAction.spec(),
            RestoreArtifactsAction.spec(),
        ]
