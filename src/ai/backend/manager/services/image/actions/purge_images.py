from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageAction
from ai.backend.manager.services.image.types import ImageRefData


@dataclass
class PurgedImagesData:
    agent_id: AgentId
    purged_images: list[str]


@dataclass
class PurgeImagesKeyData:
    agent_id: AgentId
    images: list[ImageRefData]


@dataclass
class PurgeImageAction(ImageAction):
    key: PurgeImagesKeyData
    force: bool
    noprune: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "purge"


@dataclass
class PurgeImagesAction(ImageAction):
    keys: list[PurgeImagesKeyData]
    force: bool
    noprune: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "purge_multi"


@dataclass
class PurgeImagesActionResult(BaseActionResult):
    total_reserved_bytes: int
    purged_images: list[PurgedImagesData]
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None
