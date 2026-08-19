from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
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
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
    DelegateImportArtifactRevisionBatchActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_download_progress import (
    GetDownloadProgressAction,
    GetDownloadProgressActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
    GetArtifactRevisionReadmeActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_verification_result import (
    GetArtifactRevisionVerificationResultAction,
    GetArtifactRevisionVerificationResultActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
    SearchArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


class ArtifactRevisionProcessors:
    get: SingleEntityActionProcessor[GetArtifactRevisionAction, GetArtifactRevisionActionResult]
    get_readme: SingleEntityActionProcessor[
        GetArtifactRevisionReadmeAction, GetArtifactRevisionReadmeActionResult
    ]
    get_verification_result: SingleEntityActionProcessor[
        GetArtifactRevisionVerificationResultAction,
        GetArtifactRevisionVerificationResultActionResult,
    ]
    get_download_progress: SingleEntityActionProcessor[
        GetDownloadProgressAction, GetDownloadProgressActionResult
    ]
    search_revision: GlobalActionProcessor[
        SearchArtifactRevisionsAction, SearchArtifactRevisionsActionResult
    ]
    approve: SingleEntityActionProcessor[
        ApproveArtifactRevisionAction, ApproveArtifactRevisionActionResult
    ]
    reject: SingleEntityActionProcessor[
        RejectArtifactRevisionAction, RejectArtifactRevisionActionResult
    ]
    import_revision: SingleEntityActionProcessor[
        ImportArtifactRevisionAction, ImportArtifactRevisionActionResult
    ]
    delegate_import_revision_batch: GlobalActionProcessor[
        DelegateImportArtifactRevisionBatchAction, DelegateImportArtifactRevisionBatchActionResult
    ]
    cancel_import: SingleEntityActionProcessor[CancelImportAction, CancelImportActionResult]
    cleanup: SingleEntityActionProcessor[
        CleanupArtifactRevisionAction, CleanupArtifactRevisionActionResult
    ]
    associate_with_storage: SingleEntityActionProcessor[
        AssociateWithStorageAction, AssociateWithStorageActionResult
    ]
    disassociate_with_storage: SingleEntityActionProcessor[
        DisassociateWithStorageAction, DisassociateWithStorageActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ArtifactRevisionService) -> None:
        self.get = group.single_entity(GetArtifactRevisionAction, service.get)
        self.get_readme = group.single_entity(GetArtifactRevisionReadmeAction, service.get_readme)
        self.get_verification_result = group.single_entity(
            GetArtifactRevisionVerificationResultAction, service.get_verification_result
        )
        self.get_download_progress = group.single_entity(
            GetDownloadProgressAction, service.get_download_progress
        )
        self.search_revision = group.global_scope(
            SearchArtifactRevisionsAction, service.search_revision
        )
        self.approve = group.single_entity(ApproveArtifactRevisionAction, service.approve)
        self.reject = group.single_entity(RejectArtifactRevisionAction, service.reject)
        self.import_revision = group.single_entity(
            ImportArtifactRevisionAction, service.import_revision
        )
        self.delegate_import_revision_batch = group.global_scope(
            DelegateImportArtifactRevisionBatchAction, service.delegate_import_revision_batch
        )
        self.cancel_import = group.single_entity(CancelImportAction, service.cancel_import)
        self.cleanup = group.single_entity(CleanupArtifactRevisionAction, service.cleanup)
        self.associate_with_storage = group.single_entity(
            AssociateWithStorageAction, service.associate_with_storage
        )
        self.disassociate_with_storage = group.single_entity(
            DisassociateWithStorageAction, service.disassociate_with_storage
        )
