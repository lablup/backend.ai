from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Self

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import DeviceName, ResourceSlot, SlotName, SlotTypes


@dataclass
class ImageOpts:
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        images_opts_data = data.get("images_opts", {"compression": "zlib"})
        return cls(
            ip=data["ip"],
            region=data["region"],
            scaling_group=data.get("scaling_group", "default"),
            addr=data["addr"],
            public_key=data["public_key"],
            public_host=data["public_host"],
            available_resource_slots=data["available_resource_slots"],
            slot_key_and_units=data["slot_key_and_units"],
            version=data["version"],
            compute_plugins=data["compute_plugins"],
            images=data["images"],
            architecture=data.get("architecture", "x86_64"),
            auto_terminate_abusing_kernel=data.get("auto_terminate_abusing_kernel", False),
            images_opts=ImageOpts(**images_opts_data),
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "ip": self.ip,
            "region": self.region,
            "scaling_group": self.scaling_group,
            "addr": self.addr,
            "public_key": self.public_key,
            "public_host": self.public_host,
            "available_resource_slots": self.available_resource_slots,
            "slot_key_and_units": self.slot_key_and_units,
            "version": self.version,
            "compute_plugins": self.compute_plugins,
            "images": self.images,
            "architecture": self.architecture,
            "auto_terminate_abusing_kernel": self.auto_terminate_abusing_kernel,
            "images_opts": {
                "compression": self.images_opts.compression,
            },
        }
