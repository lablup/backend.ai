"""Test fixtures and helpers for agent selector tests."""

from decimal import Decimal
from typing import Optional

import pytest

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentInfo


def create_agent_info(
    agent_id: Optional[str] = None,
    agent_addr: Optional[str] = None,
    architecture: str = "x86_64",
    available_slots: Optional[dict] = None,
    occupied_slots: Optional[dict] = None,
    scaling_group: str = "default",
    container_count: int = 0,
) -> AgentInfo:
    """Create an AgentInfo instance for testing."""
    if agent_id is None:
        agent_id = "agent-1"

    if agent_addr is None:
        agent_addr = f"{agent_id}:6001"

    if available_slots is None:
        available_slots = {
            "cpu": Decimal("8.0"),
            "mem": Decimal("16384"),  # 16GB
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


@pytest.fixture
def sample_agents() -> list[AgentInfo]:
    """Create a list of sample agents for testing."""
    return [
        create_agent_info(
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
        create_agent_info(
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
        create_agent_info(
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
        create_agent_info(
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
        create_agent_info(
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
