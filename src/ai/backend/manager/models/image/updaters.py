"""Update specs for images."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.image import ImageID
from ai.backend.manager.data.image.types import ImageData, ImageType
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ImageUpdate:
    """The image columns an edit sets.

    Carried apart from the updater because the row an edit names is resolved from a
    canonical name or an alias, which is not known where the values are built.
    """

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    registry: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    image: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    tag: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    is_local: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    size_bytes: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    image_type: OptionalState[ImageType] = field(default_factory=OptionalState[ImageType].nop)
    config_digest: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    labels: OptionalState[dict[str, Any]] = field(default_factory=OptionalState[dict[str, Any]].nop)
    accelerators: TriState[str] = field(default_factory=TriState[str].nop)
    resources: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

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


@dataclass
class ImageUpdater(DataUpdater[ImageRow, ImageData]):
    """Edit the image the id names."""

    image_id: ImageID
    update: ImageUpdate = field(default_factory=ImageUpdate)

    @property
    @override
    def row_class(self) -> type[ImageRow]:
        return ImageRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ImageRow.id

    @override
    def target_id_value(self) -> ImageID:
        return self.image_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return self.update.build_values()

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()
