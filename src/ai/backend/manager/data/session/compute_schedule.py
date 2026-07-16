from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import ResourceSlotEntry


@dataclass(frozen=True)
class UnschedulableReasonHint:
    """What the caller could change so an unschedulable kernel would fit.

    Surfaces only the user-actionable subset of the selector's
    ``RemediationHint``.

    - ``required_reduction`` — subtract these slots to fit the best-fitting node.
    """

    required_reduction: tuple[ResourceSlotEntry, ...] | None = None


@dataclass(frozen=True)
class ComputeScheduleKernelResult:
    """Compute-schedule outcome for a single kernel.

    Results correspond positionally to the requested kernels: the caller
    matches each result to its input by list index, so no correlation handle
    is carried here.

    ``reason_hint`` is populated only when ``success`` is False; it
    describes what to change so the kernel would fit on one of the
    scheduling-target nodes.
    """

    requested_slots: tuple[ResourceSlotEntry, ...]
    requested_architecture: str
    success: bool
    reason_hint: UnschedulableReasonHint | None = None


@dataclass(frozen=True)
class ComputeScheduleResult:
    kernel_results: list[ComputeScheduleKernelResult]
