"""Test fixtures and helpers for agent selector tests.

The parent-level scheduler conftest targets other scheduler layers, so the
selector tests build every value locally from the current view types
(``ai.backend.manager.views.sokovan``).
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.views.sokovan.agent import AgentInfo, AgentResource, SlotResource

AgentInfoFactory = Callable[..., AgentInfo]


def _create_agent_info(
    agent_id: str = "agent-1",
    agent_addr: str | None = None,
    architecture: str = "x86_64",
    available_slots: Mapping[str, Decimal] | None = None,
    occupied_slots: Mapping[str, Decimal] | None = None,
    container_count: int = 0,
) -> AgentInfo:
    """Build an AgentInfo whose slots have ``capacity=available_slots`` and
    ``used=occupied_slots`` (reserved is always zero)."""
    if agent_addr is None:
        agent_addr = f"{agent_id}:6001"
    if available_slots is None:
        available_slots = {
            "cpu": Decimal("8"),
            "mem": Decimal("16384"),
        }
    if occupied_slots is None:
        occupied_slots = {}
    slots = {
        ResourceSlotName(slot_name): SlotResource(
            capacity=capacity,
            reserved=Decimal(0),
            used=occupied_slots.get(slot_name, Decimal(0)),
        )
        for slot_name, capacity in available_slots.items()
    }
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=agent_addr,
        architecture=ArchName(architecture),
        resources=AgentResource(slots=slots),
        container_count=container_count,
    )


@pytest.fixture
def agent_info_factory() -> AgentInfoFactory:
    """Factory fixture for creating AgentInfo instances with custom configurations."""
    return _create_agent_info


@pytest.fixture
def agents_with_varied_occupancy() -> list[AgentInfo]:
    """
    Agents with same capacity but different occupancy levels.

    Remaining resources:
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
    GPU agent vs CPU-only agent with identical remaining CPU/mem.
    agent-gpu has an unutilized cuda.shares capability.
    """
    return [
        _create_agent_info(
            agent_id="agent-gpu",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
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

    Remaining resources:
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
    """Agents with identical remaining resources for tie-breaking tests."""
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

    Remaining resources:
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
def agents_for_gpu_priority() -> list[AgentInfo]:
    """
    Agents for testing GPU-first resource priority.

    Remaining resources:
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
    Agents with identical remaining CPU/mem but different GPU utilization.

    - gpu-partially-used: 2 GPU remaining (partially used)
    - gpu-unused: 4 GPU remaining (completely unused)
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
            occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        ),
    ]


@pytest.fixture
def agents_dispersed_gpu_vs_cpu() -> list[AgentInfo]:
    """
    Agents with identical remaining CPU/mem for the dispersed capability test.

    - agent-gpu: has an unutilized cuda.shares capability
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
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
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
    - agent-1: 1 CPU, 2048 mem remaining (high occupancy)
    - agent-2: 7 CPU, 14336 mem remaining (low occupancy)
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


@pytest.fixture
def agents_for_resource_tie_breaking() -> list[AgentInfo]:
    """
    Agents with equal unutilized capabilities (zero) but different remaining
    resources.

    - agent-low-resources: 2 CPU, 4096 mem remaining
    - agent-high-resources: 12 CPU, 24576 mem remaining
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
    Specialized agent (with unutilized GPU) vs general agent (CPU-only).

    - agent-specialized: 2 CPU, 4096 mem remaining, unutilized GPU
    - agent-general: 6 CPU, 12288 mem remaining, no accelerators
    """
    return [
        _create_agent_info(
            agent_id="agent-specialized",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={"cpu": Decimal("6"), "mem": Decimal("12288")},
        ),
        _create_agent_info(
            agent_id="agent-general",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
    ]


@pytest.fixture
def agents_with_custom_accelerator() -> list[AgentInfo]:
    """
    Agents with a custom accelerator resource type.

    Remaining resources:
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
def agents_mixed_resource_types() -> list[AgentInfo]:
    """
    Agents with heterogeneous resource types (GPU, TPU, CPU-only).

    Remaining resources:
    - gpu-agent: 8 CPU, 16384 mem, 4 GPU
    - tpu-agent: 12 CPU, 24576 mem, 3 TPU
    - cpu-agent: 16 CPU, 32768 mem
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
            available_slots={"cpu": Decimal("32"), "mem": Decimal("65536")},
            occupied_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
        ),
    ]


@pytest.fixture
def agents_for_roundrobin_sequential() -> list[AgentInfo]:
    """Three agents; sorted order by agent_id: agent-a, agent-b, agent-c."""
    return [
        _create_agent_info(agent_id="agent-a"),
        _create_agent_info(agent_id="agent-b"),
        _create_agent_info(agent_id="agent-c"),
    ]


@pytest.fixture
def agents_for_roundrobin_unsorted() -> list[AgentInfo]:
    """Three agents in non-alphabetical order (zebra, alpha, beta)."""
    return [
        _create_agent_info(agent_id="zebra"),
        _create_agent_info(agent_id="alpha"),
        _create_agent_info(agent_id="beta"),
    ]


@pytest.fixture
def agents_for_roundrobin_varied_resources() -> list[AgentInfo]:
    """Agents with different resources; roundrobin must ignore availability."""
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
def single_agent() -> list[AgentInfo]:
    """Single agent for testing edge case with only one agent."""
    return [_create_agent_info(agent_id="lonely-agent")]


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
def agents_normal_vs_huge() -> list[AgentInfo]:
    """Normal and huge capacity agents for testing large resource values."""
    return [
        _create_agent_info(
            agent_id="normal",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        ),
        _create_agent_info(
            agent_id="huge",
            available_slots={
                "cpu": Decimal(str(sys.maxsize)),
                "mem": Decimal(str(sys.maxsize)),
            },
        ),
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


@pytest.fixture
def agents_for_resource_requirements_test() -> list[AgentInfo]:
    """
    Agents with varied remaining resources.

    - agent-low: 1 CPU, 2048 mem remaining (3 containers)
    - agent-medium: 4 CPU, 8192 mem remaining (2 containers)
    - agent-high: 14 CPU, 28672 mem remaining (1 container)
    """
    return [
        _create_agent_info(
            agent_id="agent-low",
            available_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            occupied_slots={"cpu": Decimal("3"), "mem": Decimal("6144")},
            container_count=3,
        ),
        _create_agent_info(
            agent_id="agent-medium",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            container_count=2,
        ),
        _create_agent_info(
            agent_id="agent-high",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            container_count=1,
        ),
    ]


@pytest.fixture
def agents_for_designated_agent_test() -> list[AgentInfo]:
    """
    - designated: 2 CPU, 4096 mem remaining (insufficient for large workloads)
    - other: 16 CPU, 32768 mem remaining (sufficient)
    """
    return [
        _create_agent_info(
            agent_id="designated",
            available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        ),
        _create_agent_info(
            agent_id="other",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
        ),
    ]


@pytest.fixture
def agents_for_container_limit_test() -> list[AgentInfo]:
    """
    - busy: 10 containers (at limit), plenty of slots
    - available: 5 containers
    """
    return [
        _create_agent_info(
            agent_id="busy",
            available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            container_count=10,
        ),
        _create_agent_info(
            agent_id="available",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            container_count=5,
        ),
    ]


@pytest.fixture
def agents_for_architecture_test() -> list[AgentInfo]:
    """Agents with different architectures (x86_64 vs aarch64)."""
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


@pytest.fixture
def agents_for_strategy_comparison() -> list[AgentInfo]:
    """
    Remaining resources:
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
def agents_for_large_scale_performance() -> list[AgentInfo]:
    """100 agents with a repeating occupancy pattern; every 3rd has GPU."""
    agents: list[AgentInfo] = []
    for i in range(100):
        agents.append(
            _create_agent_info(
                agent_id=f"agent-{i:03d}",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("4") if i % 3 == 0 else Decimal("0"),
                },
                occupied_slots={
                    "cpu": Decimal(str(i % 16)),
                    "mem": Decimal(str((i % 16) * 2048)),
                },
            )
        )
    return agents
