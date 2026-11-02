from __future__ import annotations

import uuid
from typing import cast

import pytest

from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelCreationConfig, KernelId, SessionId

from .fakes import FakeContainerd


@pytest.fixture
def kernel_config() -> KernelCreationConfig:
    return cast(
        KernelCreationConfig,
        {
            "image": {
                "canonical": "cr.example.com/stable/python:3.11",
                "labels": {"ai.backend.base-distro": "ubuntu22.04"},
            },
            "resource_slots": {"cpu": "1", "mem": "1073741824"},
            "uid": None,
            "main_gid": None,
            "supplementary_gids": [],
            "internal_data": None,
            "network_id": "net-1",
            "environ": {},
            "mounts": [],
        },
    )


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
