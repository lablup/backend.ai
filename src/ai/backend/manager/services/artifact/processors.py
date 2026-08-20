from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.artifact.types import ArtifactData
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
from ai.backend.manager.services.artifact.actions.search import (
    SearchArtifactsAction,
    SearchArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.search_with_revisions import (
    SearchArtifactsWithRevisionsAction,
    SearchArtifactsWithRevisionsActionResult,
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


class ArtifactProcessors:
    scan: GlobalActionProcessor[ScanArtifactsAction, ScanArtifactsActionResult]
    get: SingleEntityActionProcessor[GetArtifactAction, GetArtifactActionResult]
    search_artifacts: GlobalActionProcessor[SearchArtifactsAction, SearchArtifactsActionResult]
    search_artifacts_with_revisions: GlobalActionProcessor[
        SearchArtifactsWithRevisionsAction, SearchArtifactsWithRevisionsActionResult
    ]
    get_revisions: SingleEntityActionProcessor[
        GetArtifactRevisionsAction, GetArtifactRevisionsActionResult
    ]
    update: SingleEntityActionProcessor[UpdateArtifactAction, UpdateArtifactActionResult]
    upsert_artifacts_with_revisions: GlobalActionProcessor[
        UpsertArtifactsAction, UpsertArtifactsActionResult
    ]
    retrieve_models: GlobalActionProcessor[RetrieveModelsAction, RetrieveModelsActionResult]
    retrieve_single_model: GlobalActionProcessor[RetrieveModelAction, RetrieveModelActionResult]
    delete_artifacts: GlobalActionProcessor[DeleteArtifactsAction, DeleteArtifactsActionResult]
    restore_artifacts: GlobalActionProcessor[RestoreArtifactsAction, RestoreArtifactsActionResult]

    delegate_scan: GlobalActionProcessor[
        DelegateScanArtifactsAction, DelegateScanArtifactsActionResult
    ]

    def __init__(self, group: ProcessorGroup[ArtifactData], service: ArtifactService) -> None:
        # TODO: Move scan action to ArtifactRegistryService
        self.scan = group.global_scope(ScanArtifactsAction, service.scan)
        self.get = group.single_entity(GetArtifactAction, service.get)
        self.search_artifacts = group.global_scope(SearchArtifactsAction, service.search)
        self.search_artifacts_with_revisions = group.global_scope(
            SearchArtifactsWithRevisionsAction, service.search_with_revisions
        )
        self.get_revisions = group.single_entity(GetArtifactRevisionsAction, service.get_revisions)
        self.update = group.single_entity(UpdateArtifactAction, service.update)
        self.upsert_artifacts_with_revisions = group.global_scope(
            UpsertArtifactsAction, service.upsert_artifacts_with_revisions
        )
        self.retrieve_models = group.global_scope(RetrieveModelsAction, service.retrieve_models)
        self.retrieve_single_model = group.global_scope(
            RetrieveModelAction, service.retrieve_single_model
        )
        self.delete_artifacts = group.global_scope(DeleteArtifactsAction, service.delete_artifacts)
        self.restore_artifacts = group.global_scope(
            RestoreArtifactsAction, service.restore_artifacts
        )
        self.delegate_scan = group.global_scope(
            DelegateScanArtifactsAction, service.delegate_scan_artifacts
        )
