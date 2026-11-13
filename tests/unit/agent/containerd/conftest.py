from __future__ import annotations

import uuid

import pytest

from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelId, SessionId


@pytest.fixture
def ownership_data() -> KernelOwnershipData:
    return KernelOwnershipData(
        KernelId(uuid.uuid4()),
        SessionId(uuid.uuid4()),
        AgentId("i-test"),
    )
