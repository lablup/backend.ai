"""The bridge API between the bai-dra Go driver and the Python plugin host.

JSON over HTTP on a Unix socket in the node's plugin directory. The Go side mirrors these
models in `go/bai-dra-driver/bridge.go`; change both together.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final

from pydantic import BaseModel, Field

from ai.backend.dra.errors import InvalidQuantityError

BRIDGE_VERSION: Final = "v1"
# A shared device's capacity in 0.01-share units (suggestion-1122 5.3). Consumers name it with
# or without the domain.
SHARES_CAPACITY: Final = "shares"
SHARES_CAPACITY_QUALIFIED: Final = "dra.backend.ai/shares"
SHARE_SCALE: Final = 100

_QUANTITY_SUFFIXES: Final[dict[str, Decimal]] = {
    "": Decimal(1),
    "m": Decimal("0.001"),
    "k": Decimal(10) ** 3,
    "M": Decimal(10) ** 6,
    "G": Decimal(10) ** 9,
    "T": Decimal(10) ** 12,
    "P": Decimal(10) ** 15,
    "E": Decimal(10) ** 18,
    "Ki": Decimal(2) ** 10,
    "Mi": Decimal(2) ** 20,
    "Gi": Decimal(2) ** 30,
    "Ti": Decimal(2) ** 40,
    "Pi": Decimal(2) ** 50,
    "Ei": Decimal(2) ** 60,
}


def parse_quantity(value: str) -> Decimal:
    """A Kubernetes quantity (`150`, `1.5k`, `2Gi`, `1e3`) as a number."""
    text = value.strip()
    for suffix in sorted(_QUANTITY_SUFFIXES, key=len, reverse=True):
        if suffix and text.endswith(suffix):
            number, multiplier = text[: -len(suffix)], _QUANTITY_SUFFIXES[suffix]
            break
    else:
        number, multiplier = text, Decimal(1)
    try:
        parsed = Decimal(number) * multiplier
    except InvalidOperation as e:
        raise InvalidQuantityError(f"not a quantity: {value!r}") from e
    if not parsed.is_finite():
        raise InvalidQuantityError(f"not a quantity: {value!r}")
    return parsed


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
    uuid: str | None = Field(
        default=None, description="NVML UUID of a GPU (`GPU-...`); dynamic MIG attaches by it"
    )


class DevicesResponse(BaseModel):
    slot_name: str = Field(description="Backend.AI device name, e.g. `cuda`")
    host_id: str = Field(description="Changes when the plugin host restarts")
    generation: int = Field(description="Changes when the device list changes")
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
    edits: ContainerEdits = Field(
        description="Edits of the whole claim; `cdi_devices` not per device"
    )
    device_cdi_devices: dict[str, list[str]] = Field(
        default_factory=dict, description="Device name → CDI devices of other specs for it alone"
    )


class UnprepareRequest(BaseModel):
    claim_uid: str
