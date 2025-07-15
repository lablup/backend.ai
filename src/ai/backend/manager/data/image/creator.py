from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.types import Creator


@dataclass
class ImageCreator(Creator):
    """Creator for image operations."""

    name: str
    registry: str
    tag: str
    image_type: ImageType
    status: ImageStatus = ImageStatus.ALIVE
    architecture: str = "x86_64"
    size_bytes: int = 0
    labels: Optional[dict[str, str]] = None
    resources: Optional[dict[str, Any]] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "name": self.name,
            "registry": self.registry,
            "tag": self.tag,
            "image_type": self.image_type,
            "status": self.status,
            "architecture": self.architecture,
            "size_bytes": self.size_bytes,
        }
        if self.labels is not None:
            to_store["labels"] = self.labels
        if self.resources is not None:
            to_store["resources"] = self.resources
        return to_store


@dataclass
class ImageAliasCreator(Creator):
    """Creator for image alias operations."""

    alias: str
    target: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "target": self.target,
        }
