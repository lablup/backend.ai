from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from ai.backend.kube.crd.base import (
    BACKEND_AI_GROUP,
    CRDInfo,
    CRDModel,
    CRDScope,
    CustomResource,
    PrinterColumn,
)


class CSIVolumeSource(CRDModel):
    driver: str
    volume_handle: str
    volume_attributes: dict[str, str] = Field(default_factory=dict)
    fs_type: str | None = None


class PersistentVolumeTemplate(CRDModel):
    csi: CSIVolumeSource
    capacity: str = "1Ti"
    mount_options: list[str] = Field(default_factory=list)
    storage_class_name: str = ""


class StorageBindingSpec(CRDModel):
    storage_host: str = Field(description="storage-proxy volume name, e.g. local:volume1")
    mount_base_path: str = Field(description="Path the storage-proxy reports for the volume")
    pv: PersistentVolumeTemplate
    node_selector: dict[str, str] = Field(default_factory=dict)


class StorageBindingStatus(CRDModel):
    pv_name: str | None = None
    bound_namespaces: list[str] = Field(default_factory=list)


class StorageBinding(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=BACKEND_AI_GROUP,
        kind="StorageBinding",
        plural="storagebindings",
        scope=CRDScope.CLUSTER,
        short_names=("sb",),
        printer_columns=(
            PrinterColumn("Host", ".spec.storageHost"),
            PrinterColumn("Driver", ".spec.pv.csi.driver"),
            PrinterColumn("PV", ".status.pvName"),
        ),
    )

    spec: StorageBindingSpec
    status: StorageBindingStatus | None = None
