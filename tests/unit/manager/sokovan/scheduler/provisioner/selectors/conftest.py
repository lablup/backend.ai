"""Test fixtures and helpers for agent selector tests."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentInfo


def _create_agent_info(
    agent_id: str | None = None,
    agent_addr: str | None = None,
    architecture: str = "x86_64",
    available_slots: dict[str, Decimal] | None = None,
    occupied_slots: dict[str, Decimal] | None = None,
    scaling_group: str = "default",
    container_count: int = 0,
) -> AgentInfo:
    """Internal helper for creating AgentInfo instances."""
    if agent_id is None:
        agent_id = "agent-1"

    if agent_addr is None:
        agent_addr = f"{agent_id}:6001"

    if available_slots is None:
        available_slots = {
            "cpu": Decimal("8.0"),
            "mem": Decimal("16384"),
            "cuda.shares": Decimal("0"),
        }

    if occupied_slots is None:
        occupied_slots = {
            "cpu": Decimal("0"),
            "mem": Decimal("0"),
            "cuda.shares": Decimal("0"),
        }

    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=agent_addr,
        architecture=architecture,
        available_slots=ResourceSlot(available_slots),
        occupied_slots=ResourceSlot(occupied_slots),
        scaling_group=scaling_group,
        container_count=container_count,
    )


# ============================================================================
# Factory fixture for tests requiring custom agent configurations
# ============================================================================


@pytest.fixture
def agent_info_factory() -> Callable[..., AgentInfo]:
    """Factory fixture for creating AgentInfo instances with custom configurations."""
    return _create_agent_info


# ============================================================================
# Situation-specific agent fixtures
# ============================================================================


@pytest.fixture
def agents_with_varied_occupancy() -> list[AgentInfo]:
    """
    Agents with same capacity but different occupancy levels.
    Used for testing concentrated (prefers high occupancy) vs dispersed (prefers low occupancy).

    Available resources:
    - agent-low: 2 CPU, 4096 mem (high occupancy)
    - agent-medium: 4 CPU, 8192 mem
    - agent-high: 6 CPU, 12288 mem (low occupancy)
    """
    return [
        _create_agent_info(
            agent_id="agent-low",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("6"), "mem": Decimal("12288")},
        ),
        _create_agent_info(
            agent_id="agent-medium",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-high",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_gpu_vs_cpu_only() -> list[AgentInfo]:
    """
    GPU agent vs CPU-only agent with same CPU/mem occupancy.
    Used for testing unutilized capability preference.

    Both have same available CPU/mem (4 CPU, 8192 mem).
    agent-gpu has unutilized cuda.shares.
    """
    return [
        _create_agent_info(
            agent_id="agent-gpu",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="agent-cpu-only",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
    ]


@pytest.fixture
def agents_for_memory_priority() -> list[AgentInfo]:
    """
    Agents for testing memory-first resource priority.

    Available resources:
    - low-mem-high-cpu: 14 CPU, 2048 mem
    - high-mem-low-cpu: 2 CPU, 12288 mem
    """
    return [
        _create_agent_info(
            agent_id="low-mem-high-cpu",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("8192")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("6144")},
        ),
        _create_agent_info(
            agent_id="high-mem-low-cpu",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("6"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_with_identical_resources() -> list[AgentInfo]:
    """
    Agents with identical available resources for tie-breaking tests.
    All have 4 CPU, 8192 mem available.
    """
    return [
        _create_agent_info(
            agent_id="agent-b",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-a",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-c",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
    ]


@pytest.fixture
def agents_with_gpu_resources() -> list[AgentInfo]:
    """
    GPU agents with different GPU occupancy.

    Available resources:
    - gpu-busy: 8 CPU, 16384 mem, 2 GPU
    - gpu-free: 12 CPU, 24576 mem, 6 GPU
    """
    return [
        _create_agent_info(
            agent_id="gpu-busy",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("8"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("6"),
            },
        ),
        _create_agent_info(
            agent_id="gpu-free",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("8"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("2"),
            },
        ),
    ]


@pytest.fixture
def agents_for_inference_spreading() -> list[AgentInfo]:
    """
    Agents for testing inference session endpoint replica spreading.
    All have same resources (4 CPU, 8192 mem available).
    """
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-3",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
    ]


@pytest.fixture
def agents_full_vs_available() -> list[AgentInfo]:
    """
    One fully occupied agent and one with available resources.

    Available resources:
    - agent-full: 0 CPU, 0 mem
    - agent-available: 4 CPU, 8192 mem
    """
    return [
        _create_agent_info(
            agent_id="agent-full",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        ),
        _create_agent_info(
            agent_id="agent-available",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
    ]


@pytest.fixture
def agents_mixed_resource_types() -> list[AgentInfo]:
    """
    Agents with heterogeneous resource types (GPU, TPU, CPU-only).

    Available resources:
    - gpu-agent: 8 CPU, 16384 mem, 4 GPU (has unutilized GPU)
    - tpu-agent: 12 CPU, 24576 mem, 3 TPU (has unutilized TPU)
    - cpu-agent: 16 CPU, 32768 mem (no accelerators)
    """
    return [
        _create_agent_info(
            agent_id="gpu-agent",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("8"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
        ),
        _create_agent_info(
            agent_id="tpu-agent",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "tpu": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "tpu": Decimal("1"),
            },
        ),
        _create_agent_info(
            agent_id="cpu-agent",
            available_slots={
                "cpu": Decimal("32"),
                "mem": Decimal("65536"),
            },
            occupied_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
            },
        ),
    ]


@pytest.fixture
def agents_for_unutilized_capability_test() -> list[AgentInfo]:
    """
    Agents for testing unutilized capability count.

    - agent-gpu-unutilized: 2 unutilized capabilities (cuda.shares, tpu)
    - agent-minimal: 0 unutilized capabilities
    """
    return [
        _create_agent_info(
            agent_id="agent-gpu-unutilized",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
                "tpu": Decimal("2"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("0"),
                "tpu": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="agent-minimal",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
            },
        ),
    ]


@pytest.fixture
def agents_for_resource_tie_breaking() -> list[AgentInfo]:
    """
    Agents for testing resource-based tie-breaking when unutilized capabilities are equal.

    Both have 0 unutilized capabilities:
    - agent-low-resources: 2 CPU, 4096 mem available
    - agent-high-resources: 12 CPU, 24576 mem available
    """
    return [
        _create_agent_info(
            agent_id="agent-low-resources",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("6"), "mem": Decimal("12288")},
        ),
        _create_agent_info(
            agent_id="agent-high-resources",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
    ]


@pytest.fixture
def agents_specialized_vs_general() -> list[AgentInfo]:
    """
    Specialized agent (with GPU) vs general agent (CPU only).
    Used for testing legacy vs concentrated vs dispersed behavior differences.

    - agent-specialized: 2 CPU, 4096 mem available, has unutilized GPU
    - agent-general: 6 CPU, 12288 mem available, no accelerators
    """
    return [
        _create_agent_info(
            agent_id="agent-specialized",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("6"),
                "mem": Decimal("12288"),
                "cuda.shares": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="agent-general",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            },
            occupied_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
            },
        ),
    ]


@pytest.fixture
def agents_with_custom_accelerator() -> list[AgentInfo]:
    """
    Agents with custom accelerator resource type.

    Available resources:
    - custom-rich: 4 CPU, 8192 mem, 8 custom.accelerator
    - custom-poor: 12 CPU, 24576 mem, 1 custom.accelerator
    """
    return [
        _create_agent_info(
            agent_id="custom-rich",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "custom.accelerator": Decimal("10"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "custom.accelerator": Decimal("2"),
            },
        ),
        _create_agent_info(
            agent_id="custom-poor",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "custom.accelerator": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "custom.accelerator": Decimal("3"),
            },
        ),
    ]


@pytest.fixture
def agents_for_gpu_priority() -> list[AgentInfo]:
    """
    Agents for testing GPU-first resource priority.

    Available resources:
    - low-gpu: 14 CPU, 28672 mem, 1 GPU
    - high-gpu: 2 CPU, 4096 mem, 3 GPU
    """
    return [
        _create_agent_info(
            agent_id="low-gpu",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("3"),
            },
        ),
        _create_agent_info(
            agent_id="high-gpu",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("6"),
                "mem": Decimal("12288"),
                "cuda.shares": Decimal("1"),
            },
        ),
    ]


@pytest.fixture
def agents_gpu_partially_used() -> list[AgentInfo]:
    """
    Agents for testing partially utilized GPU resources.

    Both have same CPU/mem available (8 CPU, 16384 mem):
    - gpu-partially-used: 2 GPU available (partially used)
    - gpu-unused: 4 GPU available (completely unused)
    """
    return [
        _create_agent_info(
            agent_id="gpu-partially-used",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("2"),
            },
        ),
        _create_agent_info(
            agent_id="gpu-unused",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("0"),
            },
        ),
    ]


@pytest.fixture
def agents_dispersed_gpu_vs_cpu() -> list[AgentInfo]:
    """
    Agents for dispersed selector unutilized capability test.

    Both have same available CPU/mem (14 CPU, 28672 mem):
    - agent-gpu: has unutilized cuda.shares
    - agent-cpu-only: no unutilized capabilities
    """
    return [
        _create_agent_info(
            agent_id="agent-gpu",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="agent-cpu-only",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_concentrated_vs_dispersed() -> list[AgentInfo]:
    """
    Agents for comparing concentrated vs dispersed selection.

    - agent-1: 1 CPU, 2048 mem available (high occupancy)
    - agent-2: 7 CPU, 14336 mem available (low occupancy)
    """
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("7"), "mem": Decimal("14336")},
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
        ),
    ]


# ============================================================================
# Round-robin selector fixtures
# ============================================================================


@pytest.fixture
def agents_for_roundrobin_sequential() -> list[AgentInfo]:
    """
    Three agents for testing sequential round-robin selection.
    Sorted order by agent_id: agent-a, agent-b, agent-c
    """
    return [
        _create_agent_info(agent_id="agent-a"),
        _create_agent_info(agent_id="agent-b"),
        _create_agent_info(agent_id="agent-c"),
    ]


@pytest.fixture
def agents_for_roundrobin_unsorted() -> list[AgentInfo]:
    """
    Three agents in non-alphabetical order for testing sorting.
    Input order: zebra, alpha, beta
    Sorted order: alpha, beta, zebra
    """
    return [
        _create_agent_info(agent_id="zebra"),
        _create_agent_info(agent_id="alpha"),
        _create_agent_info(agent_id="beta"),
    ]


@pytest.fixture
def agents_for_roundrobin_non_sequential_ids() -> list[AgentInfo]:
    """
    Agents with non-sequential numeric IDs for lexicographic sorting test.
    Sorted order: agent-100, agent-42, agent-5 (lexicographic)
    """
    return [
        _create_agent_info(agent_id="agent-100"),
        _create_agent_info(agent_id="agent-5"),
        _create_agent_info(agent_id="agent-42"),
    ]


@pytest.fixture
def agents_for_roundrobin_varied_resources() -> list[AgentInfo]:
    """
    Agents with different resources to test that roundrobin ignores resource availability.
    """
    return [
        _create_agent_info(
            agent_id="agent-empty",
            available_slots={"cpu": Decimal("1"), "mem": Decimal("1024")},
            occupied_slots={"cpu": Decimal("0.9"), "mem": Decimal("1000")},
        ),
        _create_agent_info(
            agent_id="agent-full",
            available_slots={"cpu": Decimal("100"), "mem": Decimal("204800")},
            occupied_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
        ),
    ]


@pytest.fixture
def agents_for_roundrobin_fairness() -> list[AgentInfo]:
    """Five agents for testing fair distribution over multiple selections."""
    return [_create_agent_info(agent_id=f"agent-{i}") for i in range(5)]


@pytest.fixture
def agents_for_roundrobin_large_scale() -> list[AgentInfo]:
    """Ten agents for testing deterministic selection."""
    return [_create_agent_info(agent_id=f"agent-{i}") for i in range(10)]


@pytest.fixture
def single_agent() -> list[AgentInfo]:
    """Single agent for testing edge case with only one agent."""
    return [_create_agent_info(agent_id="lonely-agent")]


# ============================================================================
# Edge case fixtures
# ============================================================================


@pytest.fixture
def agents_for_edge_case_empty_request() -> list[AgentInfo]:
    """Two agents for testing empty resource request handling."""
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_cpu_only_vs_gpu() -> list[AgentInfo]:
    """CPU-only agent and GPU agent for testing missing resource types."""
    return [
        _create_agent_info(
            agent_id="cpu-only",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        ),
        _create_agent_info(
            agent_id="gpu-agent",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
        ),
    ]


@pytest.fixture
def agents_normal_vs_huge() -> list[AgentInfo]:
    """Normal and huge capacity agents for testing large resource values."""
    import sys

    return [
        _create_agent_info(
            agent_id="normal",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            },
        ),
        _create_agent_info(
            agent_id="huge",
            available_slots={
                "cpu": Decimal(str(sys.maxsize)),
                "mem": Decimal(str(sys.maxsize)),
            },
            occupied_slots={
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
            },
        ),
    ]


@pytest.fixture
def agents_decimal_precision() -> list[AgentInfo]:
    """Agents with high-precision decimal values for testing decimal handling."""
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={
                "cpu": Decimal("8.123456789012345678901234567890"),
                "mem": Decimal("16384.99999999999999999999"),
            },
            occupied_slots={
                "cpu": Decimal("4.000000000000000000000001"),
                "mem": Decimal("8192.000000000000000000001"),
            },
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={
                "cpu": Decimal("8.123456789012345678901234567891"),
                "mem": Decimal("16385.00000000000000000001"),
            },
            occupied_slots={
                "cpu": Decimal("4.0"),
                "mem": Decimal("8192.0"),
            },
        ),
    ]


@pytest.fixture
def agents_all_fully_occupied() -> list[AgentInfo]:
    """Three agents all fully occupied."""
    return [
        _create_agent_info(
            agent_id=f"full-{i}",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        )
        for i in range(3)
    ]


@pytest.fixture
def agents_with_special_resource_names() -> list[AgentInfo]:
    """Agent with special characters in resource names."""
    return [
        _create_agent_info(
            agent_id="special",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "custom.resource-name_123": Decimal("100"),
                "another/special@resource": Decimal("50"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "custom.resource-name_123": Decimal("20"),
                "another/special@resource": Decimal("10"),
            },
        ),
    ]


# ============================================================================
# Agent selection with resources test fixtures
# ============================================================================


@pytest.fixture
def agents_for_resource_requirements_test() -> list[AgentInfo]:
    """
    Agents with varied resource availability for resource requirements tests.

    Available resources:
    - agent-low: 1 CPU, 2048 mem available (3 containers)
    - agent-medium: 4 CPU, 8192 mem available (2 containers)
    - agent-high: 14 CPU, 28672 mem available (1 container)
    """
    return [
        _create_agent_info(
            agent_id="agent-low",
            available_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
            },
            occupied_slots={
                "cpu": Decimal("3"),
                "mem": Decimal("6144"),
            },
            container_count=3,
        ),
        _create_agent_info(
            agent_id="agent-medium",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
            },
            container_count=2,
        ),
        _create_agent_info(
            agent_id="agent-high",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
            },
            occupied_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
            },
            container_count=1,
        ),
    ]


@pytest.fixture
def agents_for_designated_agent_test() -> list[AgentInfo]:
    """
    Agents for testing designated agent selection with resource requirements.

    - designated: 2 CPU, 4096 mem available (insufficient for large workloads)
    - other: 16 CPU, 32768 mem available (sufficient)
    """
    return [
        _create_agent_info(
            agent_id="designated",
            available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
        ),
        _create_agent_info(
            agent_id="other",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
        ),
    ]


@pytest.fixture
def agents_for_container_limit_test() -> list[AgentInfo]:
    """
    Agents for testing container count limits.

    - busy: 10 containers (at limit), 16 CPU, 32768 mem
    - available: 5 containers, 8 CPU, 16384 mem
    """
    return [
        _create_agent_info(
            agent_id="busy",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
            container_count=10,  # At limit
        ),
        _create_agent_info(
            agent_id="available",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
            container_count=5,
        ),
    ]


@pytest.fixture
def agents_for_architecture_test() -> list[AgentInfo]:
    """
    Agents with different architectures for testing architecture requirements.

    - x86: x86_64 architecture
    - arm: aarch64 architecture
    """
    return [
        _create_agent_info(
            agent_id="x86",
            architecture="x86_64",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
        ),
        _create_agent_info(
            agent_id="arm",
            architecture="aarch64",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
        ),
    ]


# ============================================================================
# Utility function test fixtures
# ============================================================================


@pytest.fixture
def agent_with_all_resources_utilized() -> AgentInfo:
    """Agent where all available resource types are utilized."""
    return _create_agent_info(
        agent_id="all-utilized",
        available_slots={
            "cpu": Decimal("8"),
            "mem": Decimal("16384"),
            "cuda.shares": Decimal("4"),
        },
    )


@pytest.fixture
def agent_with_unutilized_accelerators() -> AgentInfo:
    """Agent with unutilized GPU and TPU capabilities."""
    return _create_agent_info(
        agent_id="unutilized-accelerators",
        available_slots={
            "cpu": Decimal("8"),
            "mem": Decimal("16384"),
            "cuda.shares": Decimal("4"),
            "tpu": Decimal("2"),
        },
    )


@pytest.fixture
def agent_with_fully_occupied_gpu() -> AgentInfo:
    """Agent where GPU is fully occupied (not available for new workloads)."""
    return _create_agent_info(
        agent_id="gpu-fully-occupied",
        available_slots={
            "cpu": Decimal("8"),
            "mem": Decimal("16384"),
            "cuda.shares": Decimal("4"),
        },
        occupied_slots={
            "cpu": Decimal("0"),
            "mem": Decimal("0"),
            "cuda.shares": Decimal("4"),  # Fully occupied
        },
    )


@pytest.fixture
def agent_for_resource_calculation() -> AgentInfo:
    """Agent for testing available resource calculations."""
    return _create_agent_info(
        agent_id="calc-test",
        available_slots={
            "cpu": Decimal("16"),
            "mem": Decimal("32768"),
        },
        occupied_slots={
            "cpu": Decimal("10"),
            "mem": Decimal("20480"),
        },
    )


# ============================================================================
# Integration test fixtures
# ============================================================================


@pytest.fixture
def agents_for_strategy_comparison() -> list[AgentInfo]:
    """
    Agents with different occupancy levels for comparing selector strategies.

    Available resources:
    - agent-1: 2 CPU, 4096 mem (highest occupancy)
    - agent-2: 8 CPU, 16384 mem (medium occupancy)
    - agent-3: 14 CPU, 28672 mem (lowest occupancy)
    """
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("14"), "mem": Decimal("28672")},
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        ),
        _create_agent_info(
            agent_id="agent-3",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_mixed_accelerators() -> list[AgentInfo]:
    """
    Agents with different accelerator types for testing mixed resource scenarios.

    - gpu-specialist: 4 CPU, 8192 mem, 8 GPU available
    - tpu-specialist: 4 CPU, 8192 mem, 4 TPU available
    - cpu-generalist: 8 CPU, 16384 mem, no accelerators
    """
    return [
        _create_agent_info(
            agent_id="gpu-specialist",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("8"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="tpu-specialist",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "tpu": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "tpu": Decimal("0"),
            },
        ),
        _create_agent_info(
            agent_id="cpu-generalist",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            },
        ),
    ]


@pytest.fixture
def agents_for_large_scale_performance() -> list[AgentInfo]:
    """
    100 agents with varying resource levels for performance testing.

    Agents 0-15 repeat occupancy pattern:
    - agent-000: 0 CPU, 0 mem occupied
    - agent-001: 1 CPU, 2048 mem occupied
    - ...
    - agent-015: 15 CPU, 30720 mem occupied

    Every 3rd agent (0, 3, 6, ...) has GPU capability.
    """
    agents = []
    for i in range(100):
        occupied_cpu = Decimal(str(i % 16))
        occupied_mem = Decimal(str((i % 16) * 2048))
        agents.append(
            _create_agent_info(
                agent_id=f"agent-{i:03d}",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("4") if i % 3 == 0 else Decimal("0"),
                },
                occupied_slots={
                    "cpu": occupied_cpu,
                    "mem": occupied_mem,
                    "cuda.shares": Decimal("0"),
                },
            )
        )
    return agents


# ============================================================================
# Legacy fixtures (for backward compatibility)
# ============================================================================


@pytest.fixture
def sample_agents() -> list[AgentInfo]:
    """Create a list of sample agents for testing."""
    return [
        _create_agent_info(
            agent_id="agent-1",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("0"),
            },
            occupied_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),
            },
            container_count=2,
        ),
        _create_agent_info(
            agent_id="agent-2",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("0"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("0"),
            },
            container_count=4,
        ),
        _create_agent_info(
            agent_id="agent-3",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("0"),
            },
            occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0"), "cuda.shares": Decimal("0")},
            container_count=0,
        ),
    ]


@pytest.fixture
def gpu_agents() -> list[AgentInfo]:
    """Create a list of GPU-enabled agents for testing."""
    return [
        _create_agent_info(
            agent_id="gpu-agent-1",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("1"),
            },
            container_count=1,
        ),
        _create_agent_info(
            agent_id="gpu-agent-2",
            available_slots={
                "cpu": Decimal("16"),
                "mem": Decimal("32768"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("2"),
            },
            container_count=2,
        ),
    ]
