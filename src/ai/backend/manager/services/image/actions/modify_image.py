from dataclasses import dataclass
from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
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

<<<<<<< HEAD:src/ai/backend/manager/services/image/actions/modify_image.py

class ModifyImageActionUnknownImageReferenceError(BackendAIError):
=======
class UpdateImageActionUnknownImageReferenceError(BackendAIError, web.HTTPNotFound):
>>>>>>> d2ebe76c5 (fix(BA-9049): give the error classes of the agent, common, manager and storage packages an HTTP status (#17132)):src/ai/backend/manager/services/image/actions/update_image.py
    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Unknown image reference."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
