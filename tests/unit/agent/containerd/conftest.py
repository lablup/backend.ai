from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal
from typing import cast, override

import pytest

from ai.backend.agent.containerd.profile.base import (
    GeneratedMountKind,
    KernelLaunch,
    KernelRunnerReadiness,
    LaunchPlan,
    RuntimeProfile,
    StdioMode,
)
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelCreationConfig, KernelId, SessionId, SlotName


class FakeProfile(RuntimeProfile):
    accepts_calls: list[Mapping[SlotName, Decimal]]
    plan_calls: list[KernelLaunch]
    _name: str
    _accepts: bool
    _plan_result: LaunchPlan | None
    _plan_error: Exception | None

    def __init__(
        self,
        name: str,
        *,
        accepts: bool,
        plan_result: LaunchPlan | None = None,
        plan_error: Exception | None = None,
    ) -> None:
        self._name = name
        self._accepts = accepts
        self._plan_result = plan_result
        self._plan_error = plan_error
        self.accepts_calls = []
        self.plan_calls = []

    @property
    @override
    def name(self) -> str:
        return self._name

    @override
    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
        self.accepts_calls.append(slots)
        return self._accepts

    @override
    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        self.plan_calls.append(kernel)
        if self._plan_error is not None:
            raise self._plan_error
        assert self._plan_result is not None
        return self._plan_result


@pytest.fixture
def launch_plan() -> LaunchPlan:
    return LaunchPlan(
        runtime_handler="io.containerd.runc.v2",
        rootfs_image="cr.example.com/stable/python:3.11",
        spec_patch={},
        allowed_mount_kinds=frozenset(GeneratedMountKind),
        stdio=StdioMode.LOG_FILE,
        readiness=KernelRunnerReadiness(timeout_s=10.0),
    )


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
def builtin() -> FakeProfile:
    return FakeProfile("runc", accepts=True)
