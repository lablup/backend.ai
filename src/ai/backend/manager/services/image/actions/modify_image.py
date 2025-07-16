from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image import ImageType
from ai.backend.manager.services.image.actions.base import ImageAction
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class ImageModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    registry: OptionalState[str] = field(default_factory=OptionalState.nop)
    image: OptionalState[str] = field(default_factory=OptionalState.nop)
    tag: OptionalState[str] = field(default_factory=OptionalState.nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState.nop)
    is_local: OptionalState[bool] = field(default_factory=OptionalState.nop)
    size_bytes: OptionalState[int] = field(default_factory=OptionalState.nop)
    type: OptionalState[ImageType] = field(default_factory=OptionalState.nop)
    config_digest: OptionalState[str] = field(default_factory=OptionalState.nop)
    labels: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)
    accelerators: TriState[str] = field(default_factory=TriState.nop)
    resources: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.registry.update_dict(to_update, "registry")
        self.image.update_dict(to_update, "image")
        self.tag.update_dict(to_update, "tag")
        self.architecture.update_dict(to_update, "architecture")
        self.is_local.update_dict(to_update, "is_local")
        self.size_bytes.update_dict(to_update, "size_bytes")
        self.type.update_dict(to_update, "type")
        self.config_digest.update_dict(to_update, "config_digest")
        self.labels.update_dict(to_update, "labels")
        self.accelerators.update_dict(to_update, "accelerators")
        self.resources.update_dict(to_update, "_resources")
        return to_update


@dataclass
class ModifyImageAction(ImageAction):
    target: str
    architecture: str
    modifier: ImageModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ModifyImageActionUnknownImageReferenceError(BackendAIError):
    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Unknown image reference."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
