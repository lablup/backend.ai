from dataclasses import dataclass
from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class UpdateImageAction(ImageAction):
    target: str
    architecture: str
    updater_spec: ImageUpdaterSpec

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateImageActionResult:
    image: ImageData


class UpdateImageActionUnknownImageReferenceError(BackendAIError):
    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Unknown image reference."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
