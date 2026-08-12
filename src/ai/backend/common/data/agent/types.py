from __future__ import annotations

import base64
from typing import Annotated, Any

from pydantic import AliasChoices, BeforeValidator, Field, PlainSerializer, field_validator

from ai.backend.common.auth import PublicKey
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    BackendAISchema,
    DeviceName,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
)


def _decode_images(value: Any) -> Any:
    """Turn the JSON form of `images` back into bytes, passing bytes through untouched."""
    if isinstance(value, str):
        return base64.b64decode(value, validate=True)
    return value


# zlib-compressed msgpack, so not valid UTF-8: JSON carries it as base64, and only JSON,
# leaving the msgpack path to pack the raw bytes as before.
PackedImages = Annotated[
    bytes,
    BeforeValidator(_decode_images),
    PlainSerializer(
        lambda value: base64.b64encode(value).decode("ascii"),
        return_type=str,
        when_used="json",
    ),
]


class ImageOpts(BackendAISchema):
    compression: str


class AgentInfo(BackendAISchema):
    ip: str
    region: str | None
    scaling_group: str | None
    addr: str
    public_key: PublicKey | None
    public_host: str
    available_resource_slots: list[ResourceSlotEntry]
    slot_key_and_units: dict[ResourceSlotName, SlotTypes]
    version: str
    compute_plugins: dict[DeviceName, dict[str, Any]]
    images: PackedImages
    architecture: str
    auto_terminate_abusing_kernel: bool
    images_opts: ImageOpts = Field(
        default_factory=lambda: ImageOpts(compression="zlib"),
        validation_alias=AliasChoices("images.opts", "images_opts", "imagesOpts"),
    )

    @field_validator("slot_key_and_units", mode="before")
    @classmethod
    def normalize_slot_keys(
        cls, value: dict[str | SlotName, SlotTypes]
    ) -> dict[ResourceSlotName, SlotTypes]:
        """Accept `SlotName` keys from older agent versions, which sent the legacy form."""
        if not isinstance(value, dict):
            raise ValueError("slot_key_and_units must be a dictionary")
        return {ResourceSlotName(str(key)): val for key, val in value.items()}
