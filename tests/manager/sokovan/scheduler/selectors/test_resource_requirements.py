"""Test resource requirements and aggregation logic."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    KernelResourceSpec,
    SessionMetadata,
)


class TestResourceRequirements:
    """Test ResourceRequirements functionality."""

    def test_single_node_aggregation(self) -> None:
        """Test that single-node sessions aggregate resource requirements."""
        # Create session metadata for single-node
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with same architecture
        kernel_reqs = {
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("8192"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get aggregated requirements
        resource_reqs = criteria.get_resource_requirements()

        # Should return single aggregated requirement
        assert len(resource_reqs) == 1

        # Check aggregated values
        agg_req = resource_reqs[0]
        # For single-node, kernel_ids should include all kernels
        assert len(agg_req.kernel_ids) == 3
        assert agg_req.requested_slots["cpu"] == Decimal("6")  # 2+1+3
        assert agg_req.requested_slots["mem"] == Decimal("14336")  # 4096+2048+8192
        assert agg_req.required_architecture == "x86_64"

    def test_single_node_mixed_architecture_error(self) -> None:
        """Test that single-node sessions with mixed architectures raise error."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with different architectures
        kernel_reqs = {
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="aarch64",  # Different architecture
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            criteria.get_resource_requirements()

        assert "different architectures" in str(exc_info.value)

    def test_multi_node_individual_resources(self) -> None:
        """Test that multi-node sessions return individual kernel resources."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.MULTI_NODE,
        )

        # Create kernel requirements
        kernel_ids = [uuid.uuid4() for _ in range(3)]
        kernel_reqs = {
            kernel_ids[0]: KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            kernel_ids[1]: KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="x86_64",
            ),
            kernel_ids[2]: KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("8192"),
                }),
                required_architecture="aarch64",  # Different architecture is OK for multi-node
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()

        # Should return individual requirements
        assert len(resource_reqs) == 3

        # Verify each requirement matches original
        for req in resource_reqs:
            # Each multi-node requirement should have exactly one kernel ID
            assert len(req.kernel_ids) == 1
            kernel_id = req.kernel_ids[0]
            # Find matching kernel requirement
            original_req = kernel_reqs[kernel_id]
            assert req.requested_slots == original_req.requested_slots
            assert req.required_architecture == original_req.required_architecture

    def test_empty_kernel_requirements(self) -> None:
        """Test handling of empty kernel requirements."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INFERENCE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements={},  # Empty
        )

        # Should return empty list for empty kernel requirements
        resource_reqs = criteria.get_resource_requirements()
        assert resource_reqs == []

    def test_single_node_gpu_aggregation(self) -> None:
        """Test GPU resource aggregation for single-node sessions."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="gpu-group",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with GPU resources
        kernel_reqs = {
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("1"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("0.5"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get aggregated requirements
        resource_reqs = criteria.get_resource_requirements()

        # Check aggregated GPU resources
        assert len(resource_reqs) == 1
        agg_req = resource_reqs[0]
        assert len(agg_req.kernel_ids) == 2
        assert agg_req.requested_slots["cpu"] == Decimal("6")
        assert agg_req.requested_slots["mem"] == Decimal("24576")
        assert agg_req.requested_slots["cuda.shares"] == Decimal("1.5")

    def test_resource_slot_addition(self) -> None:
        """Test that ResourceSlot addition works correctly."""
        slot1 = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("1"),
        })

        slot2 = ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("8192"),
            "cuda.shares": Decimal("2"),
            "special": Decimal("5"),  # Additional resource type
        })

        # Add slots
        result = slot1 + slot2

        # Check result
        assert result["cpu"] == Decimal("5")
        assert result["mem"] == Decimal("12288")
        assert result["cuda.shares"] == Decimal("3")
        assert result["special"] == Decimal("5")  # New resource type included
