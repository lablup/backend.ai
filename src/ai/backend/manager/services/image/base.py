from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ImageAction(BaseAction):
    @override
    def entity_type(self):
        return "image"

    @override
    def request_id(self):
        # TODO: request_id는 어떻게 생성?
        return "..."


@dataclass
class ImageBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "image"


class ImageRef:
    """
    DTO for ImageRefType.
    """

    name: str
    registry: str
    architecture: str
