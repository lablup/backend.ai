from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import ContainerdAgent, _kernel_slots
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported, ProfileNotApplicable
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import (
    AutoPullBehavior,
    ContainerId,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    SlotName,
)

from .conftest import FakeProfile

TDX = SlotName("confidential.tdx")


@pytest.fixture
def agent() -> ContainerdAgent:
    """A bare agent carrying only the attributes the tested methods touch."""
    instance = object.__new__(ContainerdAgent)
    instance._runtime_profiles = []
    instance._profile_required_slots = frozenset()
    instance._runc_profile = RuncProfile(1.0)
    instance.event_producer = MagicMock()
    instance.local_config = MagicMock()
    instance.computers = {}
    return instance


def _image(labels: dict[str, str]) -> ImageConfig:
    return cast(ImageConfig, {"canonical": "cr.example.com/stable/python:3.11", "labels": labels})


class TestResolveImageDistro:
    async def test_label_present(self, agent: ContainerdAgent) -> None:
        image = _image({"ai.backend.base-distro": "ubuntu22.04"})

        assert await agent.resolve_image_distro(image) == "ubuntu22.04"

    async def test_label_missing(self, agent: ContainerdAgent) -> None:
        with pytest.raises(UnsupportedBaseDistroError, match=r"ai\.backend\.base-distro"):
            await agent.resolve_image_distro(_image({}))

    async def test_label_empty(self, agent: ContainerdAgent) -> None:
        with pytest.raises(UnsupportedBaseDistroError):
            await agent.resolve_image_distro(_image({"ai.backend.base-distro": ""}))


class TestInitKernelContext:
    async def test_required_slot_without_accepting_profile_fails_before_distro(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        agent._runtime_profiles = [FakeProfile("coco-tdx", accepts=False)]
        agent._profile_required_slots = frozenset({TDX})
        config = cast(
            KernelCreationConfig,
            {
                **kernel_config,
                "resource_slots": {"cpu": "1", TDX: "1"},
                # no base-distro label: reaching resolve_image_distro would raise another error
                "image": _image({}),
            },
        )

        with pytest.raises(ProfileNotApplicable):
            await agent.init_kernel_context(ownership_data, MagicMock(), config)

    async def test_builtin_profile_is_selected(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        assert ctx._profile is agent._runc_profile
        assert ctx.distro == "ubuntu22.04"


class TestKernelSlots:
    def test_json_string_amounts_become_decimals(self, kernel_config: KernelCreationConfig) -> None:
        slots = _kernel_slots(kernel_config)

        assert slots == {SlotName("cpu"): Decimal(1), SlotName("mem"): Decimal(1073741824)}
        assert all(isinstance(v, Decimal) for v in slots.values())


_RAISING: list[tuple[str, tuple[Any, ...]]] = [
    ("pull_image", (MagicMock(), MagicMock())),
    ("push_image", (MagicMock(), MagicMock())),
    ("purge_images", (MagicMock(),)),
    ("restart_kernel__load_config", (KernelId(uuid.uuid4()), "cfg")),
    ("create_local_network", ("net",)),
    ("destroy_local_network", ("net",)),
    ("get_cgroup_path", (MagicMock(), ContainerId("c"))),
    ("extract_image_command", ("img",)),
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
        await agent._write_kernel_registry_to_recovery({}, MagicMock())

    async def test_scan_images_is_empty(self, agent: ContainerdAgent) -> None:
        result = await agent.scan_images()

        assert result.scanned_images == {}
        assert result.removed_images == {}

    async def test_check_image_is_false(self, agent: ContainerdAgent) -> None:
        assert await agent.check_image(MagicMock(), "id", AutoPullBehavior.DIGEST) is False

    async def test_restart_store_config_is_a_noop(self, agent: ContainerdAgent) -> None:
        await agent.restart_kernel__store_config(KernelId(uuid.uuid4()), "c", b"")

    async def test_enumerate_containers_is_empty(self, agent: ContainerdAgent) -> None:
        assert await agent.enumerate_containers() == []

    async def test_destroy_and_clean_kernel_are_noops(self, agent: ContainerdAgent) -> None:
        kernel_id = KernelId(uuid.uuid4())

        await agent.destroy_kernel(kernel_id, None)
        await agent.clean_kernel(kernel_id, None, False)
