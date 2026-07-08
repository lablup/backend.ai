"""Unit tests for ContainerdAgent image methods (facade injected via __new__)."""

from typing import Any, cast

import pytest

import ai.backend.agent.containerd.agent as agent_mod
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import ContainerInfo, ImageInfo
from ai.backend.common.docker import LabelName
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior, ContainerStatus


class FakeFacade:
    def __init__(self, *, exists: bool = True, remove_error: str | None = None) -> None:
        self._exists = exists
        self._remove_error = remove_error
        self.pulled: list[str] = []
        self.pushed: list[str] = []
        self.removed: list[str] = []

    async def image_exists(self, image_ref: str) -> bool:
        return self._exists

    async def image_digest(self, image_ref: str) -> str | None:
        return "sha256:local" if self._exists else None

    async def pull_image(self, image_ref: str, *, auth: Any = None) -> None:
        self.pulled.append(image_ref)
        self.pull_auth = auth

    async def push_image(self, image_ref: str, *, auth: Any = None) -> None:
        self.pushed.append(image_ref)
        self.push_auth = auth

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


class _FakeRuntime:
    """Minimal OciRuntime stub for the distro probe: the container exits immediately."""

    def __init__(self) -> None:
        self.created = False
        self.removed = False

    async def create_container(self, container_id: str, **kwargs: Any) -> None:
        self.created = True

    async def start_container(self, container_id: str) -> Any:
        return None

    async def container_status(self, container_id: str) -> str | None:
        return "stopped"

    async def remove_container(self, container_id: str) -> None:
        self.removed = True


def _agent(facade: FakeFacade) -> ContainerdAgent:
    agent = ContainerdAgent.__new__(ContainerdAgent)
    agent._session_network = cast(Any, facade)
    return agent


class TestResolveImageDistro:
    async def test_reads_base_distro_label(self) -> None:
        agent = _agent(FakeFacade())
        image = cast(Any, {"labels": {LabelName.BASE_DISTRO: "ubuntu20.04"}, "canonical": "x"})
        assert await agent.resolve_image_distro(image) == "ubuntu20.04"

    async def test_unlabeled_probes_ldd(self, tmp_path: Any, monkeypatch: Any) -> None:
        # No base-distro label -> run an `ldd --version` probe container and parse its stdout.
        logfile = tmp_path / "probe.log"
        logfile.write_text("ldd (Ubuntu GLIBC 2.35-0ubuntu3) 2.35\n")
        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.container_log_path", lambda cid: logfile
        )
        runtime = _FakeRuntime()
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, runtime)
        image = cast(Any, {"labels": {}, "canonical": "cr.example/img:1"})
        distro = await agent.resolve_image_distro(image)
        assert isinstance(distro, str) and distro  # a concrete distro was resolved
        assert runtime.created and runtime.removed  # probe container created + cleaned up

    async def test_unlabeled_unknown_libc_raises(self, tmp_path: Any, monkeypatch: Any) -> None:
        logfile = tmp_path / "probe.log"
        logfile.write_text("some unexpected output\n")
        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.container_log_path", lambda cid: logfile
        )
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, _FakeRuntime())
        image = cast(Any, {"labels": {}, "canonical": "cr.example/img:1"})
        with pytest.raises(ImageNotAvailable):
            await agent.resolve_image_distro(image)


class _ScanRuntime:
    def __init__(self, infos: list[Any]) -> None:
        self._infos = infos

    async def list_image_infos(self) -> list[Any]:
        return self._infos


class TestScanImages:
    async def test_keeps_only_labeled_bai_kernel_images(self) -> None:
        infos = [
            ImageInfo(  # valid kernel image
                name="cr.backend.ai/stable/python:3.10-ubuntu20.04",
                digest="sha256:aaa",
                architecture="amd64",
                labels={"ai.backend.kernelspec": "1", "ai.backend.base-distro": "ubuntu20.04"},
            ),
            ImageInfo(  # no labels -> not a kernel image
                name="docker.io/library/redis:7",
                digest="sha256:bbb",
                architecture="amd64",
                labels={},
            ),
            ImageInfo(  # labeled but kernelspec out of range
                name="cr.backend.ai/stable/python:3.9",
                digest="sha256:ccc",
                architecture="amd64",
                labels={"ai.backend.kernelspec": "99"},
            ),
        ]
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, _ScanRuntime(infos))
        agent.images = cast(Any, {})
        result = await agent.scan_images()
        assert set(result.scanned_images) == {"cr.backend.ai/stable/python:3.10-ubuntu20.04"}
        info = result.scanned_images["cr.backend.ai/stable/python:3.10-ubuntu20.04"]
        assert info.digest == "sha256:aaa"
        assert info.architecture == "x86_64"  # amd64 -> x86_64 alias applied

    async def test_reports_removed_images(self) -> None:
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, _ScanRuntime([]))
        gone = cast(Any, object())
        agent.images = cast(Any, {"cr.backend.ai/stable/python:3.10": gone})
        result = await agent.scan_images()
        assert set(result.removed_images) == {"cr.backend.ai/stable/python:3.10"}


class TestExtractImageCommand:
    async def test_delegates_to_facade_entrypoint(self) -> None:
        agent = _agent(FakeFacade())
        assert await agent.extract_image_command("img:1") == ["/opt/backend.ai/bin/entrypoint.sh"]


class TestPullImage:
    async def test_pulls_canonical(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        await agent.pull_image(
            cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}), timeout_seconds=None
        )
        assert facade.pulled == ["cr.example/img:1"]

    async def test_threads_registry_credentials(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        reg = cast(Any, {"username": "u", "password": "p"})
        await agent.pull_image(
            cast(Any, FakeImageRef("cr.example/img:1")), reg, timeout_seconds=None
        )
        assert facade.pull_auth == {"username": "u", "password": "p"}

    async def test_no_auth_without_credentials(self) -> None:
        facade = FakeFacade()
        agent = _agent(facade)
        await agent.pull_image(
            cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}), timeout_seconds=None
        )
        assert facade.pull_auth is None


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
        facade = FakeFacade()
        agent = _agent(facade)
        resp = await agent.purge_images(PurgeImagesReq(images=["a:1", "b:2"]))
        assert facade.removed == ["a:1", "b:2"]
        assert {r.image for r in resp.responses} == {"a:1", "b:2"}
        assert all(r.error is None for r in resp.responses)

    async def test_reports_error_per_image(self) -> None:
        facade = FakeFacade(remove_error="in use")
        agent = _agent(facade)
        resp = await agent.purge_images(PurgeImagesReq(images=["a:1"]))
        assert resp.responses[0].error == "in use"


class TestCgroupPath:
    def test_containerd_systemd_scope(self) -> None:
        agent = _agent(FakeFacade())
        path = agent.get_cgroup_path("memory", "abc123")
        assert str(path) == "/sys/fs/cgroup/system.slice/containerd-abc123.scope"


class TestEnumerateContainers:
    def _runtime_with(self, infos: list[Any]) -> Any:
        class _R:
            async def list_container_infos(self) -> list[Any]:
                return infos

        return _R()

    async def test_maps_kernel_containers_by_label(self) -> None:
        kid = "11111111-1111-1111-1111-111111111111"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="running",
                          labels={"ai.backend.kernel-id": kid}),
            ContainerInfo(id="c2", image="redis", status="running", labels={}),  # not a kernel
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        result = await agent.enumerate_containers()
        assert len(result) == 1
        got_kid, container = result[0]
        assert str(got_kid) == kid
        assert container.status is ContainerStatus.RUNNING
        assert container.id == kid

    async def test_status_filter_excludes(self) -> None:
        kid = "22222222-2222-2222-2222-222222222222"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="stopped",
                          labels={"ai.backend.kernel-id": kid}),
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        # stopped -> EXITED; filtering to RUNNING excludes it
        assert await agent.enumerate_containers(frozenset({ContainerStatus.RUNNING})) == []

    def test_cgroup_version_detected(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(
            agent_mod.Path, "exists", lambda self: "cgroup.controllers" in str(self)
        )
        assert _agent(FakeFacade()).get_cgroup_version() == "2"
        monkeypatch.setattr(agent_mod.Path, "exists", lambda self: False)
        assert _agent(FakeFacade()).get_cgroup_version() == "1"


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

    async def test_digest_mismatch_needs_pull(self) -> None:
        # present locally (digest "sha256:local") but requested a different digest
        agent = _agent(FakeFacade(exists=True))
        need = await agent.check_image(
            cast(Any, FakeImageRef("i")), "sha256:remote", AutoPullBehavior.DIGEST
        )
        assert need is True

    async def test_digest_match_no_pull(self) -> None:
        agent = _agent(FakeFacade(exists=True))
        need = await agent.check_image(
            cast(Any, FakeImageRef("i")), "sha256:local", AutoPullBehavior.DIGEST
        )
        assert need is False
