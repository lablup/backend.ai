from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.dto.agent.response import PurgeImageResponse, PurgeImageResponses
from ai.backend.common.types import DispatchResult
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageAction


# TODO: 타입 위치 이동
@dataclass
class ImageRefInputType:
    """
    DTO for ImageRefType.
    """

    name: str
    registry: str
    architecture: str


@dataclass
class PurgeImagesAction(ImageAction):
    agent_id: str
    images: list[ImageRefInputType]

    @override
    def entity_id(self) -> str:
        return f"{self.agent_id}, {self.images}"

    @override
    def operation_type(self) -> str:
        return "purge_images"


@dataclass
class PurgeImagesActionResult(BaseActionResult):
    reserved_bytes: int
    results: list[PurgeImageResponse]  # TODO: Don't use DTO here
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> str:
        return ""

    @override
    def to_bgtask_result(self) -> DispatchResult:
        from ai.backend.manager.models.gql_models.image import PurgeImagesResult

        return DispatchResult(
            result=PurgeImagesResult(
                results=PurgeImageResponses(self.results),
                reserved_bytes=self.reserved_bytes,
            ),
            errors=self.errors,
        )
