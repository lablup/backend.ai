from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
    GetArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.get_installed_storages import (
    GetInstalledStoragesAction,
    GetInstalledStoragesActionResult,
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
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
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
    get: ActionProcessor[GetArtifactAction, GetArtifactActionResult]
    list_artifacts: ActionProcessor[ListArtifactsAction, ListArtifactsActionResult]
    list_artifacts_with_revisions: ActionProcessor[
        ListArtifactsWithRevisionsAction, ListArtifactsWithRevisionsActionResult
    ]
    get_revisions: ActionProcessor[GetArtifactRevisionsAction, GetArtifactRevisionsActionResult]
    get_installed_storages: ActionProcessor[
        GetInstalledStoragesAction, GetInstalledStoragesActionResult
    ]
    update: ActionProcessor[UpdateArtifactAction, UpdateArtifactActionResult]
    upsert: ActionProcessor[UpsertArtifactsAction, UpsertArtifactsActionResult]

    def __init__(self, service: ArtifactService, action_monitors: list[ActionMonitor]) -> None:
        self.scan = ActionProcessor(service.scan, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_artifacts = ActionProcessor(service.list, action_monitors)
        self.list_artifacts_with_revisions = ActionProcessor(
            service.list_with_revisions, action_monitors
        )
        self.get_revisions = ActionProcessor(service.get_revisions, action_monitors)
        self.get_installed_storages = ActionProcessor(
            service.get_installed_storages, action_monitors
        )
        self.update = ActionProcessor(service.update, action_monitors)
        self.upsert = ActionProcessor(service.upsert, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ScanArtifactsAction.spec(),
            GetArtifactAction.spec(),
            ListArtifactsAction.spec(),
            ListArtifactsWithRevisionsAction.spec(),
            GetArtifactRevisionsAction.spec(),
            GetInstalledStoragesAction.spec(),
            UpdateArtifactAction.spec(),
            UpsertArtifactsAction.spec(),
        ]
