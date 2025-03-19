from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.dto.agent.response import PurgeImageResponse
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageBatchAction, ImageRef


@dataclass
class PurgeImagesAction(ImageBatchAction):
    agent_id: str
    images: list[ImageRef]

    @override
    def entity_ids(self):
        return [image_ref.image_id() for image_ref in self.images]

    @override
    def operation_type(self):
        return "purge_images"


@dataclass
class PurgeImagesActionResult(BaseActionResult):
    reserved_bytes: int
    results: list[PurgeImageResponse]  # TODO: Don't use DTO here

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self):
        return ""
