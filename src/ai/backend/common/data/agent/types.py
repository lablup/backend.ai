from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, Self

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import DeviceName


@dataclass
class ImageOpts:
    compression: str


@dataclass
class AgentInfo:
    ip: str
    region: Optional[str]
    scaling_group: str
    addr: str
    public_key: Optional[PublicKey]
    public_host: str
    resource_slots: dict[Any, Any]
    version: str
    compute_plugins: dict[DeviceName, dict[str, str]]
    images: bytes
    architecture: str
    auto_terminate_abusing_kernel: bool
    images_opts: ImageOpts = field(default_factory=lambda: ImageOpts(compression="zlib"))

    @classmethod
    def from_dict(cls, data: Mapping[Any, Any]) -> Self:
        images_opts_data = data.get("images.opts", {"compression": "zlib"})
        return cls(
            ip=data["ip"],
            region=data["region"],
            scaling_group=data.get("scaling_group", "default"),
            addr=data["addr"],
            public_key=data["public_key"],
            public_host=data["public_host"],
            resource_slots=data["resource_slots"],
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
            "resource_slots": self.resource_slots,
            "version": self.version,
            "compute_plugins": self.compute_plugins,
            "images": self.images,
            "architecture": self.architecture,
            "auto_terminate_abusing_kernel": self.auto_terminate_abusing_kernel,
            "images.opts": {
                "compression": self.images_opts.compression,
            },
        }
