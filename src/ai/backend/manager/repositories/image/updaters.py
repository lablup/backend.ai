"""UpdaterSpec implementations for image repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.image import ImageRow, ImageType
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ImageUpdaterSpec(UpdaterSpec[ImageRow]):
    """UpdaterSpec for image updates.

    Note: Image updates use a composite key lookup (target + architecture) with alias fallback,
    so this spec is used with custom db_source logic rather than execute_updater.
    """

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    registry: OptionalState[str] = field(default_factory=OptionalState.nop)
    image: OptionalState[str] = field(default_factory=OptionalState.nop)
    tag: OptionalState[str] = field(default_factory=OptionalState.nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState.nop)
    is_local: OptionalState[bool] = field(default_factory=OptionalState.nop)
    size_bytes: OptionalState[int] = field(default_factory=OptionalState.nop)
    image_type: OptionalState[ImageType] = field(default_factory=OptionalState.nop)
    config_digest: OptionalState[str] = field(default_factory=OptionalState.nop)
    labels: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)
    accelerators: TriState[str] = field(default_factory=TriState.nop)
    resources: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ImageRow]:
        return ImageRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.registry.update_dict(to_update, "registry")
        self.image.update_dict(to_update, "image")
        self.tag.update_dict(to_update, "tag")
        self.architecture.update_dict(to_update, "architecture")
        self.is_local.update_dict(to_update, "is_local")
        self.size_bytes.update_dict(to_update, "size_bytes")
        self.image_type.update_dict(to_update, "type")
        self.config_digest.update_dict(to_update, "config_digest")
        self.labels.update_dict(to_update, "labels")
        self.accelerators.update_dict(to_update, "accelerators")
        self.resources.update_dict(to_update, "resources")
        return to_update
