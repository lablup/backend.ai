from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import DispatchResult
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class RescanImagesAction(ImageAction):
    registry: Optional[str] = None
    project: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "rescan_images"


@dataclass
class Image:
    alias: str
    architecture: str
    digest: str
    created_at: str
    updated_at: str
    size: int
    status: str
    tags: list[str]

# TODO: BatchAction으로 업데이트, entity_ids는 image row ids로.
@dataclass
class RescanImagesActionResult(BaseActionResult):
    # TODO: DispatchResult를 직접 반환하지 않도록 업데이트 해야하지 않을까?
    # DispatchResult가 bgtask와만 사용될 수 있는 맥락이라면 이 타입을 여기서 쓰면 안 됨.

    image: Image

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> str:
        return self.result.message()

    # @override
    # def to_bgtask_result(self) -> DispatchResult:
    #     return self.result

    # TODO: 여기선 어떻게 비교?
    # def __eq__(self, other: Any) -> bool:
    #     if not isinstance(other, AliasImageActionResult):
    #         return False
    #     return self.image_alias.alias == other.image_alias.alias
