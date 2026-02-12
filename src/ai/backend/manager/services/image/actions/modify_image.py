from dataclasses import dataclass
from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ModifyImageAction(ImageAction):
    target: str
    architecture: str
    updater_spec: ImageUpdaterSpec

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image.id)


@dataclass
class ModifyImageByIdAction(ImageAction):
    image_id: ImageID
    updater_spec: ImageUpdaterSpec

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify_by_id"


@dataclass
class ModifyImageByIdActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ModifyImageActionUnknownImageReferenceError(BackendAIError):
    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Unknown image reference."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
