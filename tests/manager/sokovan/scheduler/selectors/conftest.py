"""Test fixtures and helpers for agent selector tests."""

from decimal import Decimal
from typing import Optional

import pytest

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentInfo,
    AgentSelectionCriteria,
)


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


def create_selection_criteria(
    requested_slots: Optional[dict] = None,
    architecture: str = "x86_64",
    scaling_group: str = "default",
    max_container_count: Optional[int] = None,
    designated_agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    session_type: Optional[str] = None,
    enforce_spreading_endpoint_replica: bool = False,
    kernel_counts_at_endpoint: Optional[dict[str, int]] = None,
) -> AgentSelectionCriteria:
    """Create an AgentSelectionCriteria instance for testing."""
    if requested_slots is None:
        requested_slots = {
            "cpu": Decimal("1.0"),
            "mem": Decimal("1024"),  # 1GB
            "cuda.shares": Decimal("0"),
        }

    from ai.backend.common.types import SessionId, SessionTypes

    return AgentSelectionCriteria(
        requested_slots=ResourceSlot(requested_slots),
        required_architecture=architecture,
        scaling_group=scaling_group,
        max_container_count=max_container_count,
        designated_agent_id=AgentId(designated_agent_id) if designated_agent_id else None,
        session_id=SessionId(session_id) if session_id else None,
        session_type=SessionTypes(session_type) if session_type else None,
        enforce_spreading_endpoint_replica=enforce_spreading_endpoint_replica,
        kernel_counts_at_endpoint={AgentId(k): v for k, v in kernel_counts_at_endpoint.items()}
        if kernel_counts_at_endpoint
        else None,
    )


@pytest.fixture
def sample_agents():
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
def gpu_agents():
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
