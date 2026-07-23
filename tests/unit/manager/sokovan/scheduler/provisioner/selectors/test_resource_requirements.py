"""Tests for PlacementPlan grouping of per-kernel requirements."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import ClusterMode, KernelId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import PlacementPlan
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.workload import (
    KernelWorkload,
    ResourceRequest,
    SessionPlacement,
)


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _item(slots: Mapping[str, str], arch: str = "x86_64") -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(slots=_slots(slots)),
        required_architecture=ArchName(arch),
        container_count=1,
    )


class TestPlacementPlanFromItems:
    """Grouping semantics of PlacementPlan.from_items."""

    def test_single_node_aggregation(self) -> None:
        """Single-node sessions merge every item into one requirement."""
        plan = PlacementPlan.from_items(
            [
                _item({"cpu": "4", "mem": "8192"}),
                _item({"cpu": "2", "mem": "4096"}),
            ],
            ClusterMode.SINGLE_NODE,
        )

        assert len(plan.groups) == 1
        group = plan.groups[0]
        assert group.indices == [0, 1]
        assert group.requirement.requested_slots.slots == _slots({
            "cpu": "6",
            "mem": "12288",
        })
        assert group.requirement.required_architecture == ArchName("x86_64")
        assert group.requirement.container_count == 2

    def test_single_node_mixed_architecture_error(self) -> None:
        """A single-node session mixing architectures is rejected."""
        with pytest.raises(ValueError, match="different architectures"):
            PlacementPlan.from_items(
                [
                    _item({"cpu": "1"}, arch="x86_64"),
                    _item({"cpu": "1"}, arch="aarch64"),
                ],
                ClusterMode.SINGLE_NODE,
            )

    def test_multi_node_individual_resources(self) -> None:
        """Multi-node sessions keep one group per item."""
        plan = PlacementPlan.from_items(
            [
                _item({"cpu": "1", "mem": "2048"}),
                _item({"cpu": "3", "mem": "6144"}, arch="aarch64"),
            ],
            ClusterMode.MULTI_NODE,
        )

        assert len(plan.groups) == 2
        assert plan.groups[0].indices == [0]
        assert plan.groups[1].indices == [1]
        assert plan.groups[0].requirement.requested_slots.slots == _slots({
            "cpu": "1",
            "mem": "2048",
        })
        assert plan.groups[1].requirement.required_architecture == ArchName("aarch64")
        assert all(group.requirement.container_count == 1 for group in plan.groups)

    def test_empty_items(self) -> None:
        """No items produce an empty plan."""
        plan = PlacementPlan.from_items([], ClusterMode.SINGLE_NODE)
        assert plan.groups == []
        assert plan.requirements() == []

    def test_single_node_disjoint_slot_names(self) -> None:
        """Aggregation sums per-slot even when the items' slot sets differ."""
        plan = PlacementPlan.from_items(
            [
                _item({"cpu": "2", "cuda.shares": "1"}),
                _item({"cpu": "1", "mem": "2048"}),
            ],
            ClusterMode.SINGLE_NODE,
        )

        assert plan.groups[0].requirement.requested_slots.slots == _slots({
            "cpu": "3",
            "cuda.shares": "1",
            "mem": "2048",
        })


class TestPlacementPlanFromPlacement:
    """Projection from a SessionPlacement (kernel workloads)."""

    def test_indices_refer_to_kernel_positions(self) -> None:
        kernels = [
            KernelWorkload(
                kernel_id=KernelId(uuid4()),
                architecture=ArchName("x86_64"),
                requested_slots=ResourceRequest(slots=_slots({"cpu": "1"})),
            ),
            KernelWorkload(
                kernel_id=KernelId(uuid4()),
                architecture=ArchName("x86_64"),
                requested_slots=ResourceRequest(slots=_slots({"cpu": "2"})),
            ),
        ]
        placement = SessionPlacement(
            cluster_mode=ClusterMode.MULTI_NODE,
            kernels=kernels,
            agent_selection_policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=None,
        )

        plan = PlacementPlan.from_placement(placement)

        assert [group.indices for group in plan.groups] == [[0], [1]]
        assert plan.groups[1].requirement.requested_slots.slots == _slots({"cpu": "2"})
