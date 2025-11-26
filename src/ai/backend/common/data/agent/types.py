from __future__ import annotations

from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import DeviceName, ResourceSlot, SlotName, SlotTypes


class ImageOpts(BaseModel):
    compression: str


class AgentInfo(BaseModel):
    ip: str
    region: Optional[str]
    scaling_group: str
    addr: str
    public_key: Optional[PublicKey]
    public_host: str
    available_resource_slots: ResourceSlot
    slot_key_and_units: dict[SlotName, SlotTypes]
    version: str
    compute_plugins: dict[DeviceName, dict[str, Any]]
    images: bytes
    architecture: str
    auto_terminate_abusing_kernel: bool
    images_opts: ImageOpts = Field(
        default_factory=lambda: ImageOpts(compression="zlib"),
        validation_alias=AliasChoices("images.opts", "images_opts", "imagesOpts"),
    )

    # Pydantic model configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("slot_key_and_units", mode="before")
    @classmethod
    def normalize_slot_keys(
        cls, value: dict[str | SlotName, SlotTypes]
    ) -> dict[SlotName, SlotTypes]:
        """Convert string keys to SlotName instances for backward compatibility with older agent versions."""
        if not isinstance(value, dict):
            raise ValueError("slot_key_and_units must be a dictionary")
        normalized = {}
        for key, val in value.items():
            normalized[SlotName(key)] = val
        return normalized
