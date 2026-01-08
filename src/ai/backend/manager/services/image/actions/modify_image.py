from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ModifyImageAction(ImageAction):
    target: str
    architecture: str
    updater_spec: ImageUpdaterSpec

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyImageActionResult(BaseActionResult):
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
