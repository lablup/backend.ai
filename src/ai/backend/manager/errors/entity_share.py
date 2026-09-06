from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class EntityShareNotFound(ObjectNotFound):
    object_name = "entity-share"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DuplicateEntityShareError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-entity-share"
    error_title = "Duplicate entity share."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class ShareToAPersonalProject(BackendAIError, web.HTTPConflict):
    """A project that is one person's own is not offered to as a project.

    It is that person under another name, and naming them twice would stand two rows
    where the graph holds one edge.
    """

    error_type = "https://api.backend.ai/probs/entity-share-to-a-personal-project"
    error_title = "That project is one person's own."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class ShareToTheOwningScope(BackendAIError, web.HTTPConflict):
    """A scope that owns the entity cannot be offered it.

    Accepting one would lend back what is already held outright, and lending states
    what holds now, so the owning edge would come back capped.
    """

    error_type = "https://api.backend.ai/probs/entity-share-to-the-owning-scope"
    error_title = "The scope already owns the entity."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class EntityShareInvalidStatus(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/entity-share-invalid-status"
    error_title = "Invalid entity invitation status transition."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
