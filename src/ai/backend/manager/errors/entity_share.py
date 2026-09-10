from typing import override

from aiohttp import web

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.common import ObjectNotFound


class EntityShareNotFound(EntityError, ObjectNotFound):
    object_name = "entity-share"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            EntityShareEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class DuplicateEntityShareError(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-entity-share"
    error_title = "Duplicate entity share."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            EntityShareEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class ShareToAPersonalProject(EntityError, web.HTTPConflict):
    """A project that is one person's own is not offered to as a project.

    It is that person under another name, and naming them twice would stand two rows
    where the graph holds one edge.
    """

    error_type = "https://api.backend.ai/probs/entity-share-to-a-personal-project"
    error_title = "That project is one person's own."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            EntityShareEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class ShareToTheOwningScope(EntityError, web.HTTPConflict):
    """A scope that owns the entity cannot be offered it.

    Accepting one would lend back what is already held outright, and lending states
    what holds now, so the owning edge would come back capped.
    """

    error_type = "https://api.backend.ai/probs/entity-share-to-the-owning-scope"
    error_title = "The scope already owns the entity."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            EntityShareEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )
