import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RescannedImagesMeta:
    rescanned_images: dict[str, list[uuid.UUID]]
