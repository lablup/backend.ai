from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image import ImageRow, ImageType
from ai.backend.manager.services.image.base import ImageAction
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ModifyImageInputData:
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.none("name"))
    registry: OptionalState[str] = field(default_factory=lambda: OptionalState.none("registry"))
    image: OptionalState[str] = field(default_factory=lambda: OptionalState.none("image"))
    tag: OptionalState[str] = field(default_factory=lambda: OptionalState.none("tag"))
    architecture: OptionalState[str] = field(
        default_factory=lambda: OptionalState.none("architecture")
    )
    is_local: OptionalState[bool] = field(default_factory=lambda: OptionalState.none("is_local"))
    size_bytes: OptionalState[int] = field(default_factory=lambda: OptionalState.none("size_bytes"))
    type: OptionalState[ImageType] = field(default_factory=lambda: OptionalState.none("type"))
    config_digest: OptionalState[str] = field(
        default_factory=lambda: OptionalState.none("config_digest")
    )
    labels: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.none("labels")
    )
    accelerators: TriState[str] = field(default_factory=lambda: TriState.nop("accelerators"))
    resources: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.none("resources")
    )

    def set_attr(self, image_row: ImageRow):
        self.name.set_attr(image_row)
        self.registry.set_attr(image_row)
        self.image.set_attr(image_row)
        self.tag.set_attr(image_row)
        self.architecture.set_attr(image_row)
        self.is_local.set_attr(image_row)
        self.size_bytes.set_attr(image_row)
        self.type.set_attr(image_row)
        self.config_digest.set_attr(image_row)
        self.labels.set_attr(image_row)
        self.accelerators.set_attr(image_row)
        self.resources.set_attr(image_row)


@dataclass
class ModifyImageAction(ImageAction):
    target: str
    architecture: str
    props: ModifyImageInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify"


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ModifyImageActionUnknownImageReferenceError(BaseActionException):
    pass


class ModifyImageActionValueError(BaseActionException):
    pass
