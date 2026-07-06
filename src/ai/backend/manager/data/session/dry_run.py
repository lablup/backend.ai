from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import KernelId, ResourceSlotEntry
from ai.backend.manager.data.session.draft import KernelResourceDraft


@dataclass(frozen=True)
class KernelDryRunSpec:
    """Per-kernel request for a scheduler dry-run (one spec = one kernel).

    ``kernel_id`` is a caller-supplied correlation handle (a dry-run does not
    enqueue, so there is no persisted ``KernelRow.id``) used to match the result.
    ``resource`` is the pre-resolution request; the service resolves it to the
    selector's requested_slots and architecture.
    """

    kernel_id: KernelId
    resource: KernelResourceDraft


@dataclass(frozen=True)
class UnschedulableReasonHint:
    """What the caller could change so an unschedulable kernel would fit.

    Surfaces only the user-actionable subset of the selector's
    ``RemediationHint``.

    - ``required_reduction`` — subtract these slots to fit the best-fitting node.
    - ``required_container_reduction`` — free this many containers.
    - ``available_archs`` — architectures that actually exist.
    """

    required_reduction: tuple[ResourceSlotEntry, ...] | None = None
    required_container_reduction: int | None = None
    available_archs: list[str] | None = None


@dataclass(frozen=True)
class KernelDryRunResult:
    """Dry-run outcome for a single kernel.

    ``remediation`` is populated only when ``schedulable`` is False; it
    describes what to change so the kernel would fit on one of the
    scheduling-target nodes.
    """

    spec: KernelDryRunSpec
    resolved_slots: tuple[ResourceSlotEntry, ...]
    resolved_architecture: str
    schedulable: bool
    remediation: UnschedulableReasonHint | None = None
