from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction
from ai.backend.manager.services.image.types import ImageRefData


@dataclass
class PurgeImageAction(ImageAction):
    image: ImageRefData
    agent_id: AgentId
    force: bool
    noprune: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge"


@dataclass
class PurgeImageActionResult(BaseActionResult):
    reserved_bytes: int
    purged_image: ImageData
    error: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purged_image.id)


@dataclass
class PurgedImagesData:
    agent_id: AgentId
    purged_images: list[str]


@dataclass
class PurgeImagesKeyData:
    agent_id: AgentId
    images: list[ImageRefData]


# TODO: Remove this?
@dataclass
class PurgeImagesAction(ImageAction):
    keys: list[PurgeImagesKeyData]
    force: bool
    noprune: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge_multi"


@dataclass
class PurgeImagesActionResult(BaseActionResult):
    total_reserved_bytes: int
    purged_images: list[PurgedImagesData]
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None
