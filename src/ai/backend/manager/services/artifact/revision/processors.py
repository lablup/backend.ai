from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactRevisionData
from ai.backend.manager.services.artifact.revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
    CleanupArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
    DelegateImportArtifactRevisionBatchActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.get_download_progress import (
    GetDownloadProgressAction,
    GetDownloadProgressActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
    GetArtifactRevisionReadmeActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.get_verification_result import (
    GetArtifactRevisionVerificationResultAction,
    GetArtifactRevisionVerificationResultActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.search import (
    SearchArtifactRevisionsAction,
    SearchArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact.revision.service import ArtifactRevisionService


class ArtifactRevisionProcessors:
    get: SingleFieldActionProcessor[GetArtifactRevisionAction, GetArtifactRevisionActionResult]
    get_readme: SingleFieldActionProcessor[
        GetArtifactRevisionReadmeAction, GetArtifactRevisionReadmeActionResult
    ]
    get_verification_result: SingleFieldActionProcessor[
        GetArtifactRevisionVerificationResultAction,
        GetArtifactRevisionVerificationResultActionResult,
    ]
    get_download_progress: SingleFieldActionProcessor[
        GetDownloadProgressAction, GetDownloadProgressActionResult
    ]
    search_revision: GlobalActionProcessor[
        SearchArtifactRevisionsAction, SearchArtifactRevisionsActionResult
    ]
    approve: SingleFieldActionProcessor[
        ApproveArtifactRevisionAction, ApproveArtifactRevisionActionResult
    ]
    reject: SingleFieldActionProcessor[
        RejectArtifactRevisionAction, RejectArtifactRevisionActionResult
    ]
    import_revision: SingleFieldActionProcessor[
        ImportArtifactRevisionAction, ImportArtifactRevisionActionResult
    ]
    delegate_import_revision_batch: GlobalActionProcessor[
        DelegateImportArtifactRevisionBatchAction, DelegateImportArtifactRevisionBatchActionResult
    ]
    cancel_import: SingleFieldActionProcessor[CancelImportAction, CancelImportActionResult]
    cleanup: SingleFieldActionProcessor[
        CleanupArtifactRevisionAction, CleanupArtifactRevisionActionResult
    ]
    associate_with_storage: SingleFieldActionProcessor[
        AssociateWithStorageAction, AssociateWithStorageActionResult
    ]
    disassociate_with_storage: SingleFieldActionProcessor[
        DisassociateWithStorageAction, DisassociateWithStorageActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[ArtifactData],
        revisions: LookupFieldGroup[ArtifactRevisionData],
        service: ArtifactRevisionService,
    ) -> None:
        self.get = revisions.single_field(GetArtifactRevisionAction, service.get)
        self.get_readme = revisions.single_field(
            GetArtifactRevisionReadmeAction, service.get_readme
        )
        self.get_verification_result = revisions.single_field(
            GetArtifactRevisionVerificationResultAction, service.get_verification_result
        )
        self.get_download_progress = revisions.single_field(
            GetDownloadProgressAction, service.get_download_progress
        )
        self.search_revision = group.global_scope(
            SearchArtifactRevisionsAction, service.search_revision
        )
        self.approve = revisions.single_field(ApproveArtifactRevisionAction, service.approve)
        self.reject = revisions.single_field(RejectArtifactRevisionAction, service.reject)
        self.import_revision = revisions.single_field(
            ImportArtifactRevisionAction, service.import_revision
        )
        self.delegate_import_revision_batch = group.global_scope(
            DelegateImportArtifactRevisionBatchAction, service.delegate_import_revision_batch
        )
        self.cancel_import = revisions.single_field(CancelImportAction, service.cancel_import)
        self.cleanup = revisions.single_field(CleanupArtifactRevisionAction, service.cleanup)
        self.associate_with_storage = revisions.single_field(
            AssociateWithStorageAction, service.associate_with_storage
        )
        self.disassociate_with_storage = revisions.single_field(
            DisassociateWithStorageAction, service.disassociate_with_storage
        )
