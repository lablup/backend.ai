import uuid
from typing import Optional

from ai.backend.manager.actions.action import BaseAction, BaseActionResult, BaseBatchAction
from ai.backend.manager.models.user import UserRole


class ImageAction(BaseAction):
    def entity_type(self):
        return "image"


class ImageBatchAction(BaseBatchAction):
    def entity_type(self):
        return "image"


class CreateImageAction(ImageAction):
    def entity_id(self):
        return None

    def operation_type(self):
        return "create"


class CreateImageActionResult(BaseActionResult):
    image_id: uuid.UUID

    def entity_id(self) -> Optional[str]:
        return str(self.image_id)


class ImageRef:
    name: str
    registry: str
    architecture: str

    def image_id(self) -> str:
        return f"{self.registry}/{self.name}"


class ForgetImageAction(ImageAction):
    client_role: UserRole
    image_uuid: uuid.UUID

    def __init__(self, image_id: uuid.UUID):
        self.image_id = image_id

    def entity_id(self) -> str:
        return str(self.image_uuid)

    def operation_type(self):
        return "forget"


class ForgetImageActionResult(BaseActionResult):
    def entity_id(self) -> Optional[str]:
        return None


class PurgeImagesAction(ImageBatchAction):
    agent_id: str
    images: list[ImageRef]

    def __init__(self, image_id: uuid.UUID):
        self.image_id = image_id

    def entity_ids(self):
        return [image_ref.image_id() for image_ref in self.images]

    def operation_type(self):
        return "purge"


class PurgeImagesActionResult(BaseActionResult):
    def entity_id(self) -> Optional[str]:
        return None
