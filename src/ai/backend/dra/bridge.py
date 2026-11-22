"""The bridge API between the bai-dra Go driver and the Python plugin host.

JSON over HTTP on a Unix socket in the node's plugin directory. The Go side mirrors these
models in `go/bai-dra-driver/bridge.go`; change both together.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, Field

BRIDGE_VERSION: Final = "v1"
SHARES_CAPACITY: Final = "shares"  # a shared device's capacity; one device is SHARES_PER_DEVICE
SHARES_PER_DEVICE: Final = 100


class CapacityPolicy(BaseModel):
    """How a shared allocation consumes one capacity (ResourceSlice `requestPolicy`)."""

    default: str
    min: str
    max: str
    step: str


class DeviceInfo(BaseModel):
    """One device as a ResourceSlice lists it."""

    name: str = Field(description="DNS label, unique on the node")
    attributes: dict[str, str | int | bool] = Field(default_factory=dict)
    capacity: dict[str, str] = Field(default_factory=dict, description="Kubernetes quantities")
    allow_multiple_allocations: bool = False
    request_policies: dict[str, CapacityPolicy] = Field(default_factory=dict)


class DevicesResponse(BaseModel):
    slot_name: str = Field(description="Backend.AI device name, e.g. `cuda`")
    devices: list[DeviceInfo]


class PrepareRequest(BaseModel):
    claim_uid: str
    devices: list[str] = Field(description="Names of the allocated devices of this driver")
    consumed: dict[str, dict[str, str]] = Field(
        default_factory=dict, description="Device name → capacity → quantity of a shared allocation"
    )


class DeviceNode(BaseModel):
    path: str
    host_path: str | None = None
    permissions: str | None = None


class Mount(BaseModel):
    host_path: str
    container_path: str
    options: list[str] = Field(default_factory=list)


class ContainerEdits(BaseModel):
    """What a CDI device adds to the container."""

    env: list[str] = Field(default_factory=list)
    device_nodes: list[DeviceNode] = Field(default_factory=list)
    mounts: list[Mount] = Field(default_factory=list)
    cdi_devices: list[str] = Field(
        default_factory=list, description="Fully qualified CDI devices of other specs on the node"
    )


class PrepareResponse(BaseModel):
    edits: ContainerEdits


class UnprepareRequest(BaseModel):
    claim_uid: str
