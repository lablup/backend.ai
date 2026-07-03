"""Unit tests for ContainerdAgent image methods (facade injected via __new__)."""

from typing import Any, cast

import pytest

from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.common.docker import LabelName
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior


class FakeFacade:
    def __init__(self, *, exists: bool = True) -> None:
        self._exists = exists
        self.pulled: list[str] = []

    async def image_exists(self, image_ref: str) -> bool:
        return self._exists

    async def pull_image(self, image_ref: str) -> None:
        self.pulled.append(image_ref)

    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return ["/opt/backend.ai/bin/entrypoint.sh"]


class FakeImageRef:
    def __init__(self, canonical: str) -> None:
        self.canonical = canonical


def _agent(facade: FakeFacade) -> ContainerdAgent:
    agent = ContainerdAgent.__new__(ContainerdAgent)
    agent._session_network = cast(Any, facade)
    return agent


class TestResolveImageDistro:
    async def test_reads_base_distro_label(self) -> None:
        agent = _agent(FakeFacade())
        image = cast(Any, {"labels": {LabelName.BASE_DISTRO: "ubuntu20.04"}, "canonical": "x"})
        assert await agent.resolve_image_distro(image) == "ubuntu20.04"

    async def test_unlabeled_raises(self) -> None:
        agent = _agent(FakeFacade())
        image = cast(Any, {"labels": {}, "canonical": "cr.example/img:1"})
        with pytest.raises(NotImplementedError):
            await agent.resolve_image_distro(image)


class TestExtractImageCommand:
    async def test_delegates_to_facade_entrypoint(self) -> None:
        agent = _agent(FakeFacade())
        assert await agent.extract_image_command("img:1") == ["/opt/backend.ai/bin/entrypoint.sh"]


class TestPullImage:
    async def test_pulls_canonical(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        await agent.pull_image(cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}), timeout_seconds=None)
        assert facade.pulled == ["cr.example/img:1"]


class TestBootSafe:
    async def test_scan_images_returns_empty(self) -> None:
        agent = _agent(FakeFacade())
        result = await agent.scan_images()
        assert result.scanned_images == {}
        assert result.removed_images == {}

    async def test_enumerate_containers_empty(self) -> None:
        agent = _agent(FakeFacade())
        assert await agent.enumerate_containers() == []

    def test_cgroup_version_is_v2(self) -> None:
        assert _agent(FakeFacade()).get_cgroup_version() == "2"


class TestCheckImage:
    async def test_present_needs_no_pull(self) -> None:
        agent = _agent(FakeFacade(exists=True))
        need = await agent.check_image(cast(Any, FakeImageRef("i")), "id", AutoPullBehavior.TAG)
        assert need is False

    async def test_absent_tag_needs_pull(self) -> None:
        agent = _agent(FakeFacade(exists=False))
        need = await agent.check_image(cast(Any, FakeImageRef("i")), "id", AutoPullBehavior.TAG)
        assert need is True

    async def test_absent_none_raises(self) -> None:
        agent = _agent(FakeFacade(exists=False))
        with pytest.raises(ImageNotAvailable):
            await agent.check_image(cast(Any, FakeImageRef("i")), "id", AutoPullBehavior.NONE)
