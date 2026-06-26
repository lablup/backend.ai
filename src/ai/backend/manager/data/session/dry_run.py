from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import ResourceSlot


@dataclass(frozen=True)
class KernelDryRunSpec:
    """Per-kernel resource requirement for a scheduler dry-run.

    One spec corresponds to exactly one kernel; kernel count is not aggregated.
    ``architecture`` is used as a pre-filter so that architecture-incompatible
    nodes are not miscounted as a slot shortage.
    """

    requested_slots: ResourceSlot
    architecture: str


@dataclass(frozen=True)
class KernelDryRunResult:
    """Dry-run outcome for a single kernel.

    ``required_reduction`` is the per-slot amount to reduce so this kernel becomes
    schedulable on its best-fitting node, i.e. the candidate node that requires the
    smallest reduction. It is selected by comparing candidate nodes as whole deficit
    vectors (NOT a per-slot min across different nodes) and reporting that node's
    deficit. It is an empty ``ResourceSlot`` when ``schedulable`` is True.
    """

    spec: KernelDryRunSpec
    schedulable: bool
    required_reduction: ResourceSlot
