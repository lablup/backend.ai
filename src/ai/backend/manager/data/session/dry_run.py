from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import ResourceSlotEntry


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

    Results correspond positionally to the requested kernels: the caller
    matches each result to its input by list index, so no correlation handle
    is carried here.

    ``remediation`` is populated only when ``schedulable`` is False; it
    describes what to change so the kernel would fit on one of the
    scheduling-target nodes.
    """

    resolved_slots: tuple[ResourceSlotEntry, ...]
    resolved_architecture: str
    schedulable: bool
    remediation: UnschedulableReasonHint | None = None
