from __future__ import annotations

import enum
from typing import Any, ClassVar

from pydantic import Field

from ai.backend.kube.crd.base import (
    SCHEDULING_GROUP,
    CRDInfo,
    CRDModel,
    CRDScope,
    CustomResource,
    PrinterColumn,
)


class SharingMode(enum.StrEnum):
    """Device sharing modes (suggestion 5.3)."""

    EXCLUSIVE = "exclusive"
    FRACTION = "fraction"
    PARTITION = "partition"
    TIMESLICE = "timeslice"
    SPATIAL = "spatial"


class DriverKind(enum.StrEnum):
    BAI = "bai"
    EXTERNAL = "external"


class GPUAllocationPolicy(enum.StrEnum):
    """Who allocates NVIDIA GPUs in the cluster (suggestion 4.11)."""

    DRA = "dra"  # ResourceClaims only
    DEVICE_PLUGIN = "device-plugin"  # the extended resource of the device plugin


class FractionStrategy(enum.StrEnum):
    """How a fraction request larger than one device is split across devices (suggestion 5.4)."""

    FILL = "fill"  # the largest devices first
    EVENLY = "evenly"  # equal parts on the fewest devices


class DeviceProfileSpec(CRDModel):
    slot_name: str
    sharing_mode: SharingMode
    driver_kind: DriverKind = DriverKind.BAI
    driver_name: str
    device_class_name: str
    extended_resource_name: str | None = Field(
        default=None,
        description=(
            "Device plugin resource, e.g. nvidia.com/gpu. Under the device-plugin GPU allocation"
            " policy the kernel container requests it instead of a ResourceClaim. Exclusive"
            " profiles only"
        ),
    )
    fraction_strategy: FractionStrategy = Field(
        default=FractionStrategy.FILL,
        description="How a fraction request larger than any one device is split",
    )
    attribute_map: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Backend.AI attribute name (slotName, model, ...) → the driver's attribute, e.g."
            " model: gpu.nvidia.com/productName. A name without a domain is in the driver's"
            " domain. Unmapped names are used as they are"
        ),
    )
    isolation_provider: str | None = Field(
        default=None,
        description=(
            "Informational: the isolation the driver applies (hami-core, bai-hook, none). The"
            " bai-dra driver entry selects it; the controller does not read it"
        ),
    )
    opaque_config: dict[str, Any] = Field(default_factory=dict)
    match_attributes: list[str] = Field(
        default_factory=list,
        description=(
            "Attributes (Backend.AI names, mapped by attributeMap) every device of a"
            " multi-device claim shares"
        ),
    )
    compute_domain: bool = Field(
        default=False,
        description=(
            "NVIDIA DRA driver: a session of several kernels using this profile gets a"
            " ComputeDomain (resource.nvidia.com/v1beta1) and its channel claim on every"
            " kernel Pod"
        ),
    )


class DeviceProfileStatus(CRDModel):
    controls: list[dict[str, Any]] = Field(default_factory=list)
    available: bool = False
    message: str | None = None


class DeviceProfile(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=SCHEDULING_GROUP,
        kind="DeviceProfile",
        plural="deviceprofiles",
        scope=CRDScope.CLUSTER,
        short_names=("dp",),
        printer_columns=(
            PrinterColumn("Slot", ".spec.slotName"),
            PrinterColumn("Mode", ".spec.sharingMode"),
            PrinterColumn("DeviceClass", ".spec.deviceClassName"),
        ),
    )

    spec: DeviceProfileSpec
    status: DeviceProfileStatus | None = None
