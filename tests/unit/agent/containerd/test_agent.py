from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ContainerId,
    KernelId,
)


@pytest.fixture
def agent() -> ContainerdAgent:
    """A bare agent carrying only the attributes the tested methods touch."""
    instance = object.__new__(ContainerdAgent)
    instance.local_config = MagicMock()
    instance.id = AgentId("i-test")
    return instance


_RAISING: list[tuple[str, tuple[Any, ...]]] = [
    ("pull_image", (MagicMock(), MagicMock())),
    ("push_image", (MagicMock(), MagicMock())),
    ("purge_images", (MagicMock(),)),
    ("restart_kernel__load_config", (KernelId(uuid.uuid4()), "cfg")),
    ("create_local_network", ("net",)),
    ("destroy_local_network", ("net",)),
    ("get_cgroup_path", (MagicMock(), ContainerId("c"))),
    ("extract_image_command", ("img",)),
    ("resolve_image_distro", (MagicMock(),)),
    ("check_image", (MagicMock(), "id", AutoPullBehavior.DIGEST)),
    ("init_kernel_context", (MagicMock(), MagicMock(), MagicMock())),
    ("destroy_kernel", (KernelId(uuid.uuid4()), ContainerId("c"))),
    ("clean_kernel", (KernelId(uuid.uuid4()), ContainerId("c"), False)),
    ("restart_kernel__store_config", (KernelId(uuid.uuid4()), "cfg", b"")),
]


class TestContainerdAgentVerbs:
    @pytest.mark.parametrize(("method", "args"), _RAISING, ids=[r[0] for r in _RAISING])
    async def test_unsupported_verbs_raise(
        self, agent: ContainerdAgent, method: str, args: tuple[Any, ...]
    ) -> None:
        kwargs: dict[str, Any] = {"timeout_seconds": None} if method == "pull_image" else {}

        with pytest.raises(KernelVerbNotSupported, match=method):
            await getattr(agent, method)(*args, **kwargs)

    def test_get_cgroup_version_raises(self, agent: ContainerdAgent) -> None:
        with pytest.raises(KernelVerbNotSupported, match="get_cgroup_version"):
            agent.get_cgroup_version()

    async def test_load_kernel_registry_is_empty(self, agent: ContainerdAgent) -> None:
        assert await agent._load_kernel_registry_from_recovery() == {}

    async def test_write_kernel_registry_is_a_noop(self, agent: ContainerdAgent) -> None:
        await agent._write_kernel_to_recovery(MagicMock())

    async def test_enumerate_containers_is_empty(self, agent: ContainerdAgent) -> None:
        assert await agent.enumerate_containers() == []

    async def test_scan_images_is_empty(self, agent: ContainerdAgent) -> None:
        result = await agent.scan_images()

        assert result.scanned_images == {}
        assert result.removed_images == {}
