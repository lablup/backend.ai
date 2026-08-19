"""Value types shared by the agent-selection pipeline.

Kept separate from ``selector.py`` (selection logic) and ``exceptions.py``
(error classes) so both can share these without importing each other.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.manager.views.sokovan.workload import ResourceRequest


@dataclass
class ResourceRequirements:
    """One placement requirement: the slots, architecture, and container
    count a single agent must be able to host.

    For single-node sessions this is the whole session aggregated; for
    multi-node sessions there is one requirement per container.
    """

    # Resource slots required
    requested_slots: ResourceRequest
    # Architecture required
    required_architecture: ArchName
    # Number of containers this requirement puts on the selected agent
    container_count: int


@dataclass
class PlacementFailure:
    """A computed "this requirement cannot be placed right now" outcome.

    Built only from stateful-filter failures (exclusion failures are
    absolute and propagate as errors). ``requirement_index`` maps the
    failure back to its position in the criteria; ``filter_name`` names the
    filter that left no candidates; ``missing_slots`` is the per-slot
    shortfall against the best-fitting candidate (empty when no slot is
    short); ``missing_containers`` is how many containers the best
    candidate must free to admit one more (0 when the limit is not the
    problem).
    """

    requirement_index: int
    resource_requirement: ResourceRequirements
    filter_name: str
    missing_slots: Mapping[ResourceSlotName, Decimal]
    missing_containers: int
