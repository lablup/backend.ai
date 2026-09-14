"""Base of the manager's field row errors."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from aiohttp import web

from ai.backend.common.data.entity.types import FieldType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.not_found import NotFoundError


@dataclass(frozen=True)
class FieldErrorCode:
    """What a field error answers with: the row's type, what was being done to it,
    and what went wrong. The owning entity comes from the type, not from here."""

    field_type: FieldType
    operation: ActionOperationType
    detail: ErrorDetail

    def domain(self) -> str:
        """The owning entity and the field row as one domain. A dangling kind has no
        owner and reports its own type alone. No part carries an underscore."""
        field = self.field_type.replace("_", "-")
        owner = self.field_type.owner_type()
        if owner is None:
            return field
        return f"{owner.name().replace('_', '-')}-{field}"

    def to_error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=self.domain(),
            operation=self.operation.to_error_operation(),
            error_detail=self.detail,
        )


class FieldError(BackendAIError):
    """An error about one field row, reporting its owner and its own type as the
    code's domain.

    A subclass answers with the triple rather than declaring it in fields, the way
    every error answers with its code. Carries no ``web.HTTP*`` mixin; a concrete
    subclass adds its own.
    """

    @abstractmethod
    def field_error_code(self) -> FieldErrorCode:
        """Return the field row, the operation and the detail this error reports."""
        raise NotImplementedError

    @override
    def error_code(self) -> ErrorCode:
        return self.field_error_code().to_error_code()


class FieldNotFoundError(FieldError, NotFoundError, web.HTTPNotFound):
    """Raised when an operation names a field row that does not exist."""

    error_type = "https://api.backend.ai/probs/field-not-found"
    error_title = "Field row not found."

    _field_type: FieldType
    _operation: ActionOperationType

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        field_type: FieldType,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        self._field_type = field_type
        self._operation = operation
        super().__init__(extra_msg)

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(self._field_type, self._operation, ErrorDetail.NOT_FOUND)
