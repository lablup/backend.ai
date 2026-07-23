"""
Request DTOs for the compute-schedule v2 API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.types import AgentSelectionPolicyEnum
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId

__all__ = (
    "ComputeScheduleInput",
    "ComputeScheduleKernelResourceInput",
)


class ComputeScheduleKernelResourceInput(BaseRequestModel):
    """Per-kernel resource inputs for a compute-schedule request.

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


class ComputeScheduleInput(BaseRequestModel):
    """Compute a session's scheduling against a resource group without provisioning.

    ``cluster_mode`` decides whether kernel slots are summed onto a single
    node (SINGLE_NODE) or placed individually (MULTI_NODE).
    """

    kernels: list[ComputeScheduleKernelResourceInput] = Field(
        description="Per-kernel resource requests to test against the resource group.",
    )
    cluster_mode: ClusterModeEnum = Field(
        description="Cluster networking mode governing how kernel slots are placed.",
    )
    resource_group_id: ResourceGroupID = Field(
        description="Target resource group to compute the scheduling against.",
    )
    designated_agent_ids: list[AgentId] | None = Field(
        default=None,
        description=(
            "Restrict the fitting check to these agents, with the same "
            "semantics as the scheduling path. Null means no restriction."
        ),
    )
    agent_selection_policy: AgentSelectionPolicyEnum | None = Field(
        default=None,
        description=(
            "How `designated_agent_ids` is enforced (STRICT fails without "
            "capacity, PREFERRED falls back). Null inherits the resource "
            "group default."
        ),
    )
