from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ArtifactNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-not-found"
    error_title = "Artifact Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactNotVerified(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-not-verified"
    error_title = "Artifact Not Verified"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ArtifactUpdateError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-update-failed"
    error_title = "Artifact Update Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactDeletionBadRequestError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-deletion-failed"
    error_title = "Artifact Deletion Bad Request"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ArtifactDeletionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-deletion-failed"
    error_title = "Artifact Deletion Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactAssociationCreationError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-association-creation-failed"
    error_title = "Artifact Association Creation Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_ASSOCIATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactAssociationDeletionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-association-deletion-failed"
    error_title = "Artifact Association Deletion Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_ASSOCIATION,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactAssociationNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-association-not-found"
    error_title = "Artifact Association Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_ASSOCIATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactNotApproved(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/artifact-not-approved"
    error_title = "Artifact Not Approved"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ArtifactReadonly(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/artifact-readonly"
    error_title = "You cannot upload files to readonly artifact storage"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InvalidArtifactModifierTypeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-modifier-type"
    error_title = "Invalid Artifact Modifier Type"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ArtifactRevisionNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-revision-not-found"
    error_title = "Artifact Revision Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactScanLimitExceededError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-scan-limit-exceeded"
    error_title = "Artifact Scan Limit Exceeded"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
