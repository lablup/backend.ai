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


class CapacityConversion(CRDModel):
    capacity: str = Field(description="DRA capacity name, e.g. dra.backend.ai/shares")
    factor: float = Field(description="DRA quantity per one slot unit")


class DeviceProfileSpec(CRDModel):
    slot_name: str
    sharing_mode: SharingMode
    driver_kind: DriverKind = DriverKind.BAI
    driver_name: str
    device_class_name: str
    capacity_conversions: list[CapacityConversion] = Field(default_factory=list)
    attribute_map: dict[str, str] = Field(default_factory=dict)
    isolation_provider: str | None = None
    opaque_config: dict[str, Any] = Field(default_factory=dict)
    match_attributes: list[str] = Field(default_factory=list)


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
