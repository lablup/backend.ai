from __future__ import annotations

import uuid
from ipaddress import IPv4Network

import pytest

from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelId, SessionId

from .fakes import FakeCommandRunner, FakeContainerd


@pytest.fixture
def ownership_data() -> KernelOwnershipData:
    return KernelOwnershipData(
        KernelId(uuid.uuid4()),
        SessionId(uuid.uuid4()),
        AgentId("i-test"),
    )


@pytest.fixture
def fake() -> FakeContainerd:
    return FakeContainerd()


@pytest.fixture
def runner() -> FakeCommandRunner:
    return FakeCommandRunner()


@pytest.fixture
def network(runner: FakeCommandRunner) -> KernelNetwork:
    return KernelNetwork(
        "bai0", IPv4Network("172.30.0.0/24"), "10.0.0.5", (30000, 30999), run=runner
    )
