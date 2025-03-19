from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.services.image.base import ImageAction


# TODO: 타입 위치 옮길 것.
@dataclass
class ResourceLimitInput:
    key: Optional[str] = None
    min: Optional[str] = None
    max: Optional[str] = None


@dataclass
class KVPairInput:
    key: str
    value: str


@dataclass
class ModifyImageInput:
    name: Optional[str] = None
    registry: Optional[str] = None
    image: Optional[str] = None
    tag: Optional[str] = None
    architecture: Optional[str] = None
    is_local: Optional[bool] = None
    size_bytes: Optional[int] = None
    type: Optional[str] = None
    digest: Optional[str] = None
    labels: list[KVPairInput] = field(default_factory=list)
    supported_accelerators: list[str] = field(default_factory=list)
    resource_limits: list[ResourceLimitInput] = field(default_factory=list)


@dataclass
class ModifyImageAction(ImageAction):
    # TODO: 아래 필드는 image_alias도 될 수 있어야 함. -> target으로 이름 변경?
    image_canonical: str
    architecture: str
    props: ModifyImageInput

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.image_canonical}/{self.architecture}"

    @override
    def operation_type(self):
        return "modify_image"


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The image has been modified."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ModifyImageActionResult):
            return False
        return self.image_row.id == other.image_row.id


class ModifyImageActionUnknownImageReferenceError(Exception):
    pass


# TODO: Remove this.
class ModifyImageActionValueError(Exception):
    pass
