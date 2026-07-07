"""
Request DTOs for the dry-run schedule v2 API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID

__all__ = (
    "DryRunKernelResourceInput",
    "DryRunScheduleInput",
)


class DryRunKernelResourceInput(BaseRequestModel):
    """Per-kernel resource inputs for a scheduling dry-run.

    Mirrors the scheduler's ``KernelResourceInput``: the requested resource
    slots plus an optional image whose architecture and resource-group
    defaults are resolved downstream. Results are correlated to kernels by
    list index, so no identifier is carried here.
    """

    image_id: ImageID | None = Field(
        default=None,
        description=(
            "Image to schedule this kernel against. May be null when a "
            "resource-group default supplies the image downstream."
        ),
    )
    resources: list[ResourceSlotEntryInput] = Field(
        default_factory=list,
        description="Requested resource slots (cpu, mem, accelerators) for this kernel.",
    )


class DryRunScheduleInput(BaseRequestModel):
    """Dry-run a session's scheduling against a resource group without provisioning.

    ``cluster_mode`` decides whether kernel slots are summed onto a single
    node (SINGLE_NODE) or placed individually (MULTI_NODE).
    """

    kernels: list[DryRunKernelResourceInput] = Field(
        description="Per-kernel resource requests to test against the resource group.",
    )
    cluster_mode: ClusterModeEnum = Field(
        description="Cluster networking mode governing how kernel slots are placed.",
    )
    resource_group_id: ResourceGroupID = Field(
        description="Target resource group to dry-run the scheduling against.",
    )
