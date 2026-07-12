"""Unit tests for ContainerdAgent image methods (facade injected via __new__)."""

import asyncio
import struct
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import ai.backend.agent.containerd.agent as agent_mod
from ai.backend.agent.agent import ACTIVE_STATUS_SET, DEAD_STATUS_SET
from ai.backend.agent.config.unified import ContainerSandboxType
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import ContainerInfo, ImageInfo
from ai.backend.agent.network.port_forward import PortForward
from ai.backend.common.docker import LabelName
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior, ContainerStatus, ImageCanonical


class FakeFacade:
    def __init__(
        self,
        *,
        exists: bool = True,
        remove_error: str | None = None,
        hang: bool = False,
    ) -> None:
        self._exists = exists
        self._remove_error = remove_error
        self._hang = hang
        self.pulled: list[str] = []
        self.pushed: list[str] = []
        self.removed: list[str] = []

    async def image_exists(self, image_ref: str) -> bool:
        return self._exists

    async def image_digest(self, image_ref: str) -> str | None:
        return "sha256:local" if self._exists else None

    async def pull_image(self, image_ref: str, *, auth: Any = None) -> None:
        if self._hang:
            await asyncio.sleep(10)
        self.pulled.append(image_ref)
        self.pull_auth = auth

    async def push_image(self, image_ref: str, *, auth: Any = None) -> None:
        if self._hang:
            await asyncio.sleep(10)
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

    async def create_task(self, container_id: str) -> Any:
        return None

    async def start_task(self, container_id: str) -> None:
        return None

    async def container_status(self, container_id: str) -> str | None:
        return "stopped"

    async def remove_container(self, container_id: str) -> None:
        self.removed = True


class _NoForwards:
    async def list_forwards(self, **kwargs: Any) -> list[PortForward]:
        return []


def _agent(facade: FakeFacade, *, port_forwarder: Any = None) -> ContainerdAgent:
    agent = ContainerdAgent.__new__(ContainerdAgent)
    agent._session_network = cast(Any, facade)
    agent.local_config = cast(
        Any, SimpleNamespace(container=SimpleNamespace(scratch_root=Path("/tmp/bai-scratch")))
    )
    # In production this is the local PortForwarder, or the helper proxy when privilege is split;
    # either way the agent always has one.
    agent._port_forwarder = cast(Any, port_forwarder or _NoForwards())
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
        info = result.scanned_images[ImageCanonical("cr.backend.ai/stable/python:3.10-ubuntu20.04")]
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

    async def test_honors_timeout(self) -> None:
        agent = _agent(FakeFacade(hang=True))
        with pytest.raises(TimeoutError):
            await agent.pull_image(
                cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}), timeout_seconds=0.05
            )


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

    async def test_honors_timeout(self) -> None:
        agent = _agent(FakeFacade(hang=True))
        with pytest.raises(TimeoutError):
            await agent.push_image(
                cast(Any, FakeImageRef("cr.example/img:1")), cast(Any, {}), timeout_seconds=0.05
            )


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
    def test_cgroup_path_matches_spec_cgroups_path(self) -> None:
        # get_cgroup_path must point at the cgroup the OCI spec actually creates
        # (linux.cgroupsPath = /backend-ai/<id>), not the runtime's driver default.
        agent = _agent(FakeFacade())
        path = agent.get_cgroup_path("memory", "abc123")
        assert str(path) == "/sys/fs/cgroup/backend-ai/abc123"


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

    async def test_reports_published_ports_so_a_restart_reclaims_them(self) -> None:
        # the DNAT rules are the only record of a live kernel's host ports; without reporting them
        # the restarted agent would hand one of them to the next kernel
        kid = "33333333-3333-3333-3333-333333333333"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="running",
                          labels={"ai.backend.kernel-id": kid}),
        ]  # fmt: skip

        class _Forwarder:
            async def list_forwards(self, **kwargs: Any) -> list[PortForward]:
                return [
                    PortForward(kid, 30001, "172.30.1.7", 2000),
                    PortForward(kid, 30003, "172.30.1.7", 8070),
                    PortForward("someone-else", 30099, "172.30.1.9", 8070),
                ]

        agent = _agent(FakeFacade(), port_forwarder=_Forwarder())
        agent._runtime = cast(Any, self._runtime_with(infos))
        _kid, container = (await agent.enumerate_containers())[0]
        assert sorted(p.host_port for p in container.ports) == [30001, 30003]

    async def test_reports_no_ports_when_nothing_is_published(self) -> None:
        kid = "44444444-4444-4444-4444-444444444444"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="running",
                          labels={"ai.backend.kernel-id": kid}),
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        _kid, container = (await agent.enumerate_containers())[0]
        assert container.ports == []

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

    async def test_created_container_is_not_dead(self) -> None:
        # A kernel is visible to containerd from Containers.Create until its task starts. If that
        # window maps to EXITED (a DEAD_STATUS_SET member), sync_container_lifecycles() cleans a
        # kernel that is still being created. CREATED is in neither the active nor the dead set.
        kid = "55555555-5555-5555-5555-555555555555"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="created",
                          labels={"ai.backend.kernel-id": kid}),
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        # mapped to CREATED, not EXITED
        result = await agent.enumerate_containers(frozenset({ContainerStatus.CREATED}))
        assert result[0][1].status is ContainerStatus.CREATED
        # ...so the lifecycle sync, which enumerates active|dead, never even sees it and therefore
        # cannot enqueue a CLEAN for a kernel that is still being created.
        assert await agent.enumerate_containers(ACTIVE_STATUS_SET | DEAD_STATUS_SET) == []

    async def test_unrecognized_status_is_not_dead(self) -> None:
        # Fail-safe: an unknown task state must never be reported dead, or the lifecycle sync
        # would destroy a kernel we simply failed to classify.
        kid = "66666666-6666-6666-6666-666666666666"
        infos = [
            ContainerInfo(id=kid, image="img:1", status="something-new",
                          labels={"ai.backend.kernel-id": kid}),
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        assert await agent.enumerate_containers(DEAD_STATUS_SET) == []

    async def test_defaults_to_active_only(self) -> None:
        # reconstruct_resource_usage() enumerates with no argument and restores allocations from
        # whatever comes back; defaulting to "no filter" re-accounted dead containers' resources.
        running = "77777777-7777-7777-7777-777777777777"
        stopped = "88888888-8888-8888-8888-888888888888"
        infos = [
            ContainerInfo(id=running, image="img:1", status="running",
                          labels={"ai.backend.kernel-id": running}),
            ContainerInfo(id=stopped, image="img:1", status="stopped",
                          labels={"ai.backend.kernel-id": stopped}),
        ]  # fmt: skip
        agent = _agent(FakeFacade())
        agent._runtime = cast(Any, self._runtime_with(infos))
        result = await agent.enumerate_containers()
        assert [c.id for _, c in result] == [running]

    def test_cgroup_version_detected(self, monkeypatch: Any) -> None:
        target = "ai.backend.agent.containerd.agent.Path.exists"
        monkeypatch.setattr(target, lambda self: "cgroup.controllers" in str(self))
        assert _agent(FakeFacade()).get_cgroup_version() == "2"
        monkeypatch.setattr(target, lambda self: False)
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


class TestAgentSocket:
    def _agent_with_sandbox(self, jail: bool) -> Any:
        agent = _agent(FakeFacade())
        st = ContainerSandboxType.JAIL if jail else ContainerSandboxType.DOCKER
        agent.local_config = cast(Any, SimpleNamespace(container=SimpleNamespace(sandbox_type=st)))
        return agent

    async def test_is_jail_enabled_reply(self) -> None:
        on = await self._agent_with_sandbox(True)._agent_sock_reply([b"is-jail-enabled"])
        assert on == [struct.pack("i", 0), struct.pack("i", 1)]
        off = await self._agent_with_sandbox(False)._agent_sock_reply([b"is-jail-enabled"])
        assert off == [struct.pack("i", 0), struct.pack("i", 0)]

    async def test_pid_translation_reply(self, monkeypatch: Any) -> None:
        async def fake_h2c(container_id: str, host_pid: int) -> int:
            return 42

        monkeypatch.setattr("ai.backend.agent.containerd.agent.host_pid_to_container_pid", fake_h2c)
        agent = self._agent_with_sandbox(False)
        reply = await agent._agent_sock_reply([
            b"host-pid-to-container-pid",
            b"cid",
            struct.pack("i", 1000),
        ])
        assert reply == [struct.pack("i", 0), struct.pack("i", 42)]

    async def test_invalid_action(self) -> None:
        reply = await self._agent_with_sandbox(False)._agent_sock_reply([b"bogus"])
        assert reply[0] == struct.pack("i", -2)


class TestSeccompConversion:
    def test_null_subarchitectures_and_syscalls(self) -> None:
        # Docker profiles may carry explicit JSON null for subArchitectures/syscalls; .get(k, [])
        # would return None (key present) and blow up — the converter must treat null as empty.
        oci = agent_mod._docker_seccomp_to_oci(
            {
                "defaultAction": "SCMP_ACT_ERRNO",
                "archMap": [{"architecture": "SCMP_ARCH_X86_64", "subArchitectures": None}],
                "syscalls": None,
            },
            arch="x86_64",
        )
        assert oci["architectures"] == ["SCMP_ARCH_X86_64"]
        assert oci["syscalls"] == []

    def test_maps_docker_shape_to_oci(self) -> None:
        oci = agent_mod._docker_seccomp_to_oci(
            {
                "defaultAction": "SCMP_ACT_ERRNO",
                "archMap": [
                    {"architecture": "SCMP_ARCH_X86_64", "subArchitectures": ["SCMP_ARCH_X86"]}
                ],
                "syscalls": [{"names": ["read", "write"], "action": "SCMP_ACT_ALLOW"}],
            },
            arch="x86_64",
        )
        assert oci["architectures"] == ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86"]
        assert oci["syscalls"] == [{"names": ["read", "write"], "action": "SCMP_ACT_ALLOW"}]

    def test_includes_caps_gate_on_container_caps(self) -> None:
        # Cap-gated rules must be dropped unless the container holds the capability, matching how
        # Docker resolves the profile — otherwise privileged syscalls leak into the sandbox.
        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "archMap": [{"architecture": "SCMP_ARCH_X86_64", "subArchitectures": None}],
            "syscalls": [
                {"names": ["chown"], "action": "SCMP_ACT_ALLOW"},  # unconditional
                {
                    "names": ["bpf"],
                    "action": "SCMP_ACT_ALLOW",
                    "includes": {"caps": ["CAP_SYS_ADMIN"]},
                },
                {
                    "names": ["kept"],
                    "action": "SCMP_ACT_ALLOW",
                    "includes": {"caps": ["CAP_CHOWN"]},
                },
            ],
        }
        oci = agent_mod._docker_seccomp_to_oci(
            profile, arch="x86_64", caps=frozenset({"CAP_CHOWN"})
        )
        names = [n for sc in oci["syscalls"] for n in sc["names"]]
        assert "chown" in names  # unconditional
        assert "kept" in names  # CAP_CHOWN held -> included
        assert "bpf" not in names  # CAP_SYS_ADMIN absent -> dropped

    def test_excludes_caps_drop_rule_when_cap_held(self) -> None:
        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "archMap": [{"architecture": "SCMP_ARCH_X86_64"}],
            "syscalls": [
                {
                    "names": ["clone"],
                    "action": "SCMP_ACT_ALLOW",
                    "excludes": {"caps": ["CAP_SYS_ADMIN"]},
                }
            ],
        }
        oci = agent_mod._docker_seccomp_to_oci(
            profile, arch="x86_64", caps=frozenset({"CAP_SYS_ADMIN"})
        )
        assert oci["syscalls"] == []

    def test_arches_gate_rule(self) -> None:
        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "archMap": [{"architecture": "SCMP_ARCH_X86_64"}],
            "syscalls": [
                {
                    "names": ["sync_file_range2"],
                    "action": "SCMP_ACT_ALLOW",
                    "includes": {"arches": ["ppc64le"]},
                }
            ],
        }
        oci = agent_mod._docker_seccomp_to_oci(profile, arch="x86_64", caps=frozenset())
        assert oci["syscalls"] == []  # ppc64le-only rule dropped on x86_64

    def test_minkernel_kept_when_host_satisfies(self) -> None:
        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "archMap": [{"architecture": "SCMP_ARCH_X86_64"}],
            "syscalls": [
                {
                    "names": ["ptrace"],
                    "action": "SCMP_ACT_ALLOW",
                    "includes": {"minKernel": "2.6"},
                }
            ],
        }
        oci = agent_mod._docker_seccomp_to_oci(profile, arch="x86_64", caps=frozenset())
        assert [n for sc in oci["syscalls"] for n in sc["names"]] == ["ptrace"]


class TestEtcHosts:
    def _ctx(self, scratch_dir: Path | None) -> Any:
        ctx = agent_mod.ContainerdKernelCreationContext.__new__(
            agent_mod.ContainerdKernelCreationContext
        )
        ctx._scratch_dir = scratch_dir
        return ctx

    def test_writes_cluster_peers_and_returns_mount(self, tmp_path: Any) -> None:
        (tmp_path / "config").mkdir()
        ctx = self._ctx(tmp_path)
        cluster_info = cast(Any, {"cluster_hosts": {"main1": "10.0.0.2", "sub1": "10.0.0.3"}})
        mount = ctx._prepare_etc_hosts(cluster_info)
        assert mount is not None
        assert str(mount.target) == "/etc/hosts"
        content = (tmp_path / "config" / "hosts").read_text()
        assert "127.0.0.1\tlocalhost" in content
        assert "10.0.0.2\tmain1" in content
        assert "10.0.0.3\tsub1" in content

    def test_no_mount_without_cluster_hosts(self, tmp_path: Any) -> None:
        ctx = self._ctx(tmp_path)
        assert ctx._prepare_etc_hosts(cast(Any, {"cluster_hosts": {}})) is None
        assert ctx._prepare_etc_hosts(cast(Any, {})) is None
