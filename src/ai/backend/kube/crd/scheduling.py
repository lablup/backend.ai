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
from ai.backend.kube.crd.session import Condition


class SokovanBindMode(enum.StrEnum):
    """How sokovan starts a placed Pod (suggestion 3.1)."""

    GATE = "gate"  # Kueue form: release the gate, pin the node, kube-scheduler binds
    BINDER = "binder"  # KAI form: a BindRequest, the binder records claims and binds


class PodGroupPhase(enum.StrEnum):
    PENDING = "Pending"
    ADMITTED = "Admitted"
    SCHEDULED = "Scheduled"
    RUNNING = "Running"
    FAILED = "Failed"


class TopologyConstraint(CRDModel):
    required_levels: list[str] = Field(default_factory=list)
    preferred_levels: list[str] = Field(default_factory=list)


class SubGroup(CRDModel):
    name: str
    min_member: int = Field(ge=1)


class PodGroupSpec(CRDModel):
    min_member: int = Field(ge=1)
    queue: str
    priority: int = 0
    session_id: str | None = None
    topology: TopologyConstraint | None = None
    sub_groups: list[SubGroup] = Field(default_factory=list)


class PodGroupStatus(CRDModel):
    phase: PodGroupPhase = PodGroupPhase.PENDING
    scheduled: int = 0
    running: int = 0
    failed: int = 0
    last_scheduling_attempt: str | None = None
    conditions: list[Condition] = Field(default_factory=list)


class PodGroup(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=SCHEDULING_GROUP,
        kind="PodGroup",
        plural="podgroups",
        scope=CRDScope.NAMESPACED,
        short_names=("pg",),
        printer_columns=(
            PrinterColumn("Queue", ".spec.queue"),
            PrinterColumn("MinMember", ".spec.minMember", "integer"),
            PrinterColumn("Phase", ".status.phase"),
            PrinterColumn("Age", ".metadata.creationTimestamp", "date"),
        ),
    )

    spec: PodGroupSpec
    status: PodGroupStatus | None = None


class QueueResource(CRDModel):
    quota: str | None = Field(default=None, description="Guaranteed amount (slot value)")
    limit: str | None = Field(default=None, description="Hard cap (slot value)")
    over_quota_weight: float = 1.0


class QueueSpec(CRDModel):
    parent_queue: str | None = None
    display_name: str | None = None
    priority: int = 0
    resources: dict[str, QueueResource] = Field(default_factory=dict)


class QueueStatus(CRDModel):
    fair_share_factor: float | None = None
    allocated: dict[str, str] = Field(default_factory=dict)
    requested: dict[str, str] = Field(default_factory=dict)
    child_queues: list[str] = Field(default_factory=list)
    last_synced_at: str | None = None


class Queue(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=SCHEDULING_GROUP,
        kind="Queue",
        plural="queues",
        scope=CRDScope.CLUSTER,
        printer_columns=(
            PrinterColumn("Parent", ".spec.parentQueue"),
            PrinterColumn("FairShare", ".status.fairShareFactor", "number"),
            PrinterColumn("Age", ".metadata.creationTimestamp", "date"),
        ),
    )

    spec: QueueSpec
    status: QueueStatus | None = None


class BindRequestPhase(enum.StrEnum):
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


class ClaimAllocation(CRDModel):
    name: str
    allocation: dict[str, Any] = Field(description="resource.k8s.io/v1 AllocationResult")


class BindRequestSpec(CRDModel):
    pod_name: str
    pod_uid: str
    selected_node: str
    pod_group: str | None = None
    resource_claim_allocations: list[ClaimAllocation] = Field(default_factory=list)
    backoff_limit: int = 3


class BindRequestStatus(CRDModel):
    phase: BindRequestPhase = BindRequestPhase.PENDING
    failed_attempts: int = 0
    reason: str | None = None


class BindRequest(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=SCHEDULING_GROUP,
        kind="BindRequest",
        plural="bindrequests",
        scope=CRDScope.NAMESPACED,
        short_names=("br",),
        printer_columns=(
            PrinterColumn("Pod", ".spec.podName"),
            PrinterColumn("Node", ".spec.selectedNode"),
            PrinterColumn("Phase", ".status.phase"),
        ),
    )

    spec: BindRequestSpec
    status: BindRequestStatus | None = None
