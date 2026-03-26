from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.user import UserRow
    from ai.backend.manager.repositories.base.creator import Creator
    from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec


class NoUserUpdateError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/no-update-error"
    error_title = "No update user fields provided."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


@dataclass
class UserCreateSpec:
    """Specification for creating a single user, including group assignments."""

    creator: Creator[UserRow]
    group_ids: list[str] | None = None


@dataclass
class UserUpdateSpec:
    """Specification for updating a single user, including the target user ID."""

    user_id: UUID
    updater_spec: UserUpdaterSpec
