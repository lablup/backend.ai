from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class ImageModifier(PartialModifier):
    """Modifier for image operations."""
    
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    registry: OptionalState[str] = field(default_factory=OptionalState.nop)
    tag: OptionalState[str] = field(default_factory=OptionalState.nop)
    image_type: OptionalState[ImageType] = field(default_factory=OptionalState.nop)
    status: OptionalState[ImageStatus] = field(default_factory=OptionalState.nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState.nop)
    size_bytes: OptionalState[int] = field(default_factory=OptionalState.nop)
    labels: TriState[dict[str, str]] = field(default_factory=TriState.nop)
    resources: TriState[dict[str, Any]] = field(default_factory=TriState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.registry.update_dict(to_update, "registry")
        self.tag.update_dict(to_update, "tag")
        self.image_type.update_dict(to_update, "image_type")
        self.status.update_dict(to_update, "status")
        self.architecture.update_dict(to_update, "architecture")
        self.size_bytes.update_dict(to_update, "size_bytes")
        self.labels.update_dict(to_update, "labels")
        self.resources.update_dict(to_update, "resources")
        return to_update


@dataclass
class ImageAliasModifier(PartialModifier):
    """Modifier for image alias operations."""
    
    alias: OptionalState[str] = field(default_factory=OptionalState.nop)
    target: OptionalState[str] = field(default_factory=OptionalState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.alias.update_dict(to_update, "alias")
        self.target.update_dict(to_update, "target")
        return to_update