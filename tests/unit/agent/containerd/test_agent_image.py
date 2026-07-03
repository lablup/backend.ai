"""Unit tests for ContainerdAgent image methods (facade injected via __new__)."""

from typing import Any, cast

import pytest

from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.common.docker import LabelName
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior


class FakeFacade:
    def __init__(self, *, exists: bool = True, remove_error: str | None = None) -> None:
        self._exists = exists
        self._remove_error = remove_error
        self.pulled: list[str] = []
        self.pushed: list[str] = []
        self.removed: list[str] = []

    async def image_exists(self, image_ref: str) -> bool:
        return self._exists

    async def pull_image(self, image_ref: str) -> None:
        self.pulled.append(image_ref)

    async def push_image(self, image_ref: str) -> None:
        self.pushed.append(image_ref)

    async def remove_image(self, image_ref: str) -> None:
        if self._remove_error:
            raise RuntimeError(self._remove_error)
        self.removed.append(image_ref)

    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return ["/opt/backend.ai/bin/entrypoint.sh"]


class FakeImageRef:
    def __init__(self, canonical: str, *, is_local: bool = False) -> None:
        self.canonical = canonical
        self.is_local = is_local


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


class TestPushImage:
    async def test_pushes_non_local(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        await agent.push_image(cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}))
        assert facade.pushed == ["cr.example/img:1"]

    async def test_skips_local_image(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        await agent.push_image(cast(Any, FakeImageRef("local/img", is_local=True)), cast(Any, {}))
        assert facade.pushed == []


class TestPurgeImages:
    async def test_removes_each_and_reports(self) -> None:
        from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq

        facade = FakeFacade()
        agent = _agent(facade)
        resp = await agent.purge_images(PurgeImagesReq(images=["a:1", "b:2"]))
        assert facade.removed == ["a:1", "b:2"]
        assert {r.image for r in resp.responses} == {"a:1", "b:2"}
        assert all(r.error is None for r in resp.responses)

    async def test_reports_error_per_image(self) -> None:
        from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq

        facade = FakeFacade(remove_error="in use")
        agent = _agent(facade)
        resp = await agent.purge_images(PurgeImagesReq(images=["a:1"]))
        assert resp.responses[0].error == "in use"


class TestCgroupPath:
    def test_containerd_systemd_scope(self) -> None:
        agent = _agent(FakeFacade())
        path = agent.get_cgroup_path("memory", "abc123")
        assert str(path) == "/sys/fs/cgroup/system.slice/containerd-abc123.scope"


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
