from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image import ImageRow, ImageType
from ai.backend.manager.services.image.base import ImageAction
from ai.backend.manager.types import NoUnsetStatus, TriStatus


@dataclass
class ModifyImageInputData:
    name: NoUnsetStatus[str] = field(default_factory=lambda: NoUnsetStatus("name", None))
    registry: NoUnsetStatus[str] = field(default_factory=lambda: NoUnsetStatus("registry", None))
    image: NoUnsetStatus[str] = field(default_factory=lambda: NoUnsetStatus("image", None))
    tag: NoUnsetStatus[str] = field(default_factory=lambda: NoUnsetStatus("tag", None))
    architecture: NoUnsetStatus[str] = field(
        default_factory=lambda: NoUnsetStatus("architecture", None)
    )
    is_local: NoUnsetStatus[bool] = field(default_factory=lambda: NoUnsetStatus("is_local", None))
    size_bytes: NoUnsetStatus[int] = field(
        default_factory=lambda: NoUnsetStatus("size_bytes", None)
    )
    type: NoUnsetStatus[ImageType] = field(default_factory=lambda: NoUnsetStatus("type", None))
    config_digest: NoUnsetStatus[str] = field(
        default_factory=lambda: NoUnsetStatus("config_digest", None)
    )
    labels: NoUnsetStatus[dict[str, Any]] = field(
        default_factory=lambda: NoUnsetStatus("labels", None)
    )
    accelerators: TriStatus[str] = field(
        default_factory=lambda: TriStatus("accelerators", False, None)
    )
    resources: NoUnsetStatus[dict[str, Any]] = field(
        default_factory=lambda: NoUnsetStatus("resources", None)
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
        return "modify_image"


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ModifyImageActionUnknownImageReferenceError(BaseActionException):
    pass


# TODO: Remove this.
class ModifyImageActionValueError(BaseActionException):
    pass
