"""Base of the manager's entity errors."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from aiohttp import web

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.not_found import NotFoundError


@dataclass(frozen=True)
class EntityErrorCode:
    """What an entity error answers with: the row's type, what was being done to it,
    and what went wrong. The entity axis of :class:`ErrorCode`."""

    entity_type: EntityType
    operation: ActionOperationType
    detail: ErrorDetail

    def to_error_code(self) -> ErrorCode:
        """The wire form. The type keeps its underscores; the domain hyphenates them,
        because no part of a code may carry an underscore."""
        return ErrorCode(
            domain=self.entity_type.replace("_", "-"),
            operation=self.operation.to_error_operation(),
            error_detail=self.detail,
        )


class EntityError(BackendAIError):
    """An error about one entity, reporting that entity's type as the code's domain.

    A subclass answers with the triple rather than declaring it in fields, the way
    every error answers with its code. Carries no ``web.HTTP*`` mixin; a concrete
    subclass adds its own.
    """

    @abstractmethod
    def entity_error_code(self) -> EntityErrorCode:
        """Return the entity, the operation and the detail this error reports."""
        raise NotImplementedError

    @override
    def error_code(self) -> ErrorCode:
        return self.entity_error_code().to_error_code()


class EntityNotFoundError(EntityError, NotFoundError, web.HTTPNotFound):
    """Raised when an operation names an entity row that does not exist."""

    error_type = "https://api.backend.ai/probs/entity-not-found"
    error_title = "Entity not found."

    _entity_type: EntityType
    _operation: ActionOperationType

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        entity_type: EntityType,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        self._entity_type = entity_type
        self._operation = operation
        super().__init__(extra_msg)

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(self._entity_type, self._operation, ErrorDetail.NOT_FOUND)
