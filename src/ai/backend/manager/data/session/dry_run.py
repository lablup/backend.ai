from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import AgentId, KernelId, ResourceSlot
from ai.backend.manager.data.session.draft import KernelResourceDraft


@dataclass(frozen=True)
class KernelDryRunSpec:
    """Per-kernel request for a scheduler dry-run.

    One spec corresponds to exactly one kernel; kernel count is not aggregated.
    ``kernel_id`` is a caller-supplied correlation handle (a dry-run does not
    enqueue, so there is no persisted ``KernelRow.id``); it matches the input
    spec to its result through the selector's ``kernel_ids``.
    ``resource`` carries the request in its pre-resolution form (image + partial
    slots + shmem); the service resolves it to the selector's requested_slots
    and architecture from image minimums and resource-group defaults, so a
    dry-run reflects what a real enqueue would actually schedule.
    """

    kernel_id: KernelId
    resource: KernelResourceDraft


@dataclass(frozen=True)
class KernelDryRunRemediation:
    """What the caller could change so an unschedulable kernel would fit.

    Data-layer mirror of the scheduler selector's ``RemediationHint`` (mirrored
    here rather than imported, so the data layer stays free of a sokovan
    dependency and can be converted to a DTO). There is no discriminator: any
    subset of fields may be populated, and each non-None field is an
    independently actionable remediation.

    - ``required_reduction`` — subtract these slots to fit the best-fitting node,
      i.e. the candidate node needing the smallest reduction, compared as whole
      deficit vectors (NOT a per-slot min across different nodes).
    - ``required_container_reduction`` — free this many containers to admit the kernel.
    - ``available_archs`` — architectures that actually exist (change the request arch).
    - ``available_agent_ids`` — agents that are actually available (revise designation).
    """

    required_reduction: ResourceSlot | None = None
    required_container_reduction: int | None = None
    available_archs: list[str] | None = None
    available_agent_ids: list[AgentId] | None = None


@dataclass(frozen=True)
class KernelDryRunResult:
    """Dry-run outcome for a single kernel.

    ``remediation`` is populated only when ``schedulable`` is False; it
    describes what to change so the kernel would fit on one of the
    scheduling-target nodes.
    """

    spec: KernelDryRunSpec
    resolved_slots: ResourceSlot
    resolved_architecture: str
    schedulable: bool
    remediation: KernelDryRunRemediation | None = None
