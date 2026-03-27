from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.image.actions.base import (
    ImageAction,
    ImageSingleEntityAction,
    ImageSingleEntityActionResult,
)


@dataclass
class ForgetImageAction(ImageAction):
    """
    Deprecated. Use ForgetImageByIdAction instead.
    """

    reference: str
    architecture: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ForgetImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image.id)


@dataclass
class ForgetImageByIdAction(ImageSingleEntityAction):
    image_id: ImageID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.image_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.IMAGE, str(self.image_id))


@dataclass
class ForgetImageByIdActionResult(ImageSingleEntityActionResult):
    image: ImageData

    @override
    def target_entity_id(self) -> str:
        return str(self.image.id)
