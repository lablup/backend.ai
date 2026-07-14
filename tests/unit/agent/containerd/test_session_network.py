import asyncio
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import Any, cast, override

import pytest

from ai.backend.agent.containerd.oci import OWNER_AGENT_LABEL, SESSION_ID_LABEL
from ai.backend.agent.containerd.runtime.interface import ExecResult, OciRuntime, TaskHandle
from ai.backend.agent.containerd.session_network import (
    ContainerdSessionNetwork,
    UnknownNetworkBackend,
    build_containerd_session_network,
    session_net_meta_from_network_config,
)
from ai.backend.agent.errors.network import SessionNetworkGone, UnusableVtep
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)

_VXLAN_NC = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450}
_HOSTGW_NC = {"backend": "host-gw", "subnet": "10.129.0.0/24"}


class TestMetaParsing:
    def test_vxlan_config(self) -> None:
        meta = session_net_meta_from_network_config("s1", _VXLAN_NC)
        assert meta.backend is NetworkBackendKind.VXLAN
        assert meta.subnet == "10.128.5.0/24"
        assert meta.vni == 4097
        assert meta.mtu == 1450

    def test_host_gw_has_no_vni_and_default_mtu(self) -> None:
        meta = session_net_meta_from_network_config("s2", _HOSTGW_NC)
        assert meta.backend is NetworkBackendKind.HOST_GW
        assert meta.vni is None
        assert meta.mtu == 1500


class FakeEtcd:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.store[key] = val

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.store.pop(key, None)

    async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
        return {
            k[len(prefix) :]: v
            for k, v in self.store.items()
            if k.startswith(prefix) and "/" not in k[len(prefix) :]
        }

    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        return
        yield  # pragma: no cover


class RecordingBackend:
    """Minimal AbstractNetworkAgentPluginV2-shaped stub recording setup calls."""

    def __init__(self) -> None:
        self.setup: list[str] = []
        self.adopted: list[str] = []
        self.torndown: list[str] = []
        self.last_self_member: Member | None = None

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.setup.append(meta.session_id)
        self.last_self_member = self_member

    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.adopted.append(meta.session_id)
        self.last_self_member = self_member

    async def teardown_session_network(self, session_id: str) -> None:
        self.torndown.append(session_id)

    async def add_peer(self, session_id: str, peer: Member) -> None: ...
    async def del_peer(self, session_id: str, peer: Member) -> None: ...
    async def probe_caps(self) -> AgentNetworkCaps:
        return AgentNetworkCaps(tunnel_offload=False, native_routing_ok=False)

    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta
    ) -> EndpointPlan:
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    cni_config={"type": "bridge"},
                )
            ]
        )


class _ContainerInfo:
    """The subset of ContainerInfo the session network reads: id + session label."""

    def __init__(self, container_id: str, labels: dict[str, str]) -> None:
        self.id = container_id
        self.labels = labels
        self.image = "img:1"
        self.status = "running"


class FakeRuntime(OciRuntime):
    def __init__(self, containers: list[_ContainerInfo] | None = None) -> None:
        self.calls: list[str] = []
        self.containers = containers or []  # what containerd still runs for us

    @override
    async def image_exists(self, image_ref: str) -> bool:
        return True

    @override
    async def image_digest(self, image_ref: str) -> str | None:
        return "sha256:x"

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        return None

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        return None

    @override
    async def pull_image(
        self, image_ref: str, *, auth: Mapping[str, str] | None = None
    ) -> None: ...
    @override
    async def list_images(self) -> Sequence[str]:
        return []

    @override
    async def list_image_infos(self) -> Sequence[Any]:
        return []

    @override
    async def list_container_infos(self) -> Sequence[Any]:
        return self.containers

    @override
    async def subscribe_task_events(self) -> Any:
        return
        yield  # pragma: no cover

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None: ...
    @override
    async def push_image(
        self, image_ref: str, *, auth: Mapping[str, str] | None = None
    ) -> None: ...

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return ["/entry"]

    @override
    async def container_status(self, container_id: str) -> str | None:
        return "running"

    @override
    async def exec_in_container(
        self,
        container_id: str,
        args: Any,
        *,
        uid: int | None = None,
        gid: int | None = None,
        cwd: str | None = None,
        timeout_sec: float = 30.0,
    ) -> ExecResult:
        return ExecResult(exit_code=0, stdout=b"", stderr=b"")

    @override
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        self.calls.append(f"create:{container_id}:{image_ref}")

    @override
    async def create_task(self, container_id: str, *, use_logger: bool = True) -> TaskHandle:
        self.calls.append(f"create_task:{container_id}")
        return TaskHandle(container_id=container_id, pid=9001)

    @override
    async def start_task(self, container_id: str) -> None:
        self.calls.append(f"start_task:{container_id}")

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        self.calls.append(f"kill:{container_id}:{signal}")

    @override
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        self.calls.append(f"stop:{container_id}:{grace_period}")

    @override
    async def commit_container(
        self, container_id: str, *, base_image_ref: str, target_ref: str, labels: Any = None
    ) -> None:
        self.calls.append("commit_container")

    @override
    async def remove_container(self, container_id: str) -> None:
        self.calls.append(f"remove:{container_id}")

    @override
    async def list_containers(self) -> Sequence[str]:
        return []

    @override
    async def container_pid(self, container_id: str) -> int | None:
        return 9001


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, netns))


def _facade(
    etcd: FakeEtcd,
    backend: RecordingBackend,
    runner: RecordingRunner,
    *,
    backends: dict[str, Any] | None = None,
    runtime: FakeRuntime | None = None,
    vtep_ip: str | None = "192.168.0.10",
) -> ContainerdSessionNetwork:
    return ContainerdSessionNetwork(
        cast(AbstractKVStore, etcd),
        agent_id="agent-1",
        host_ip="192.168.0.10",
        runtime=runtime or FakeRuntime(),
        cni_runner=runner,
        backends=backends or {"vxlan": cast(Any, backend), "host-gw": cast(Any, backend)},
        vtep_ip=vtep_ip,
    )


class TestEnsureSession:
    async def test_sets_up_and_publishes_self_member_with_vtep(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        meta = await facade.ensure_session("s1", "k1", _VXLAN_NC)
        try:
            assert backend.setup == ["s1"]
            # vxlan -> self member advertises its vtep = host_ip
            assert backend.last_self_member is not None
            assert backend.last_self_member.vtep_ip == "192.168.0.10"
            # membership published to etcd
            assert "network/session/s1/members/agent-1" in etcd.store
            published = json.loads(etcd.store["network/session/s1/members/agent-1"])
            assert published["vtep_ip"] == "192.168.0.10"
            assert meta.vni == 4097
        finally:
            await facade.teardown_session("s1")

    async def test_host_gw_self_member_has_no_vtep(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        await facade.ensure_session("s2", "k1", _HOSTGW_NC)
        try:
            assert backend.last_self_member is not None
            assert backend.last_self_member.vtep_ip is None
        finally:
            await facade.teardown_session("s2")

    async def test_a_vxlan_session_is_refused_without_a_usable_vtep(self) -> None:
        # Joining anyway would publish an unusable VTEP; peers guard on `is None` only, so they
        # would program "" / 0.0.0.0 into their FDB and the session would hang at rendezvous with
        # no error. Refusing here is what turns that into a diagnosable failure.
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner, vtep_ip=None)
        with pytest.raises(UnusableVtep):
            await facade.ensure_session("s1", "k1", _VXLAN_NC)
        assert backend.setup == []  # nothing was built
        assert "network/session/s1/members/agent-1" not in etcd.store

    async def test_a_single_node_session_still_works_without_a_vtep(self) -> None:
        # A node with no routable address only ever runs single-node sessions; those must not care.
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner, vtep_ip=None)
        await facade.ensure_session("s2", "k1", _HOSTGW_NC)
        try:
            assert backend.setup == ["s2"]
            assert backend.last_self_member is not None
            assert backend.last_self_member.vtep_ip is None
        finally:
            await facade.teardown_session("s2")


class TestFailedSetup:
    async def test_a_failed_setup_leaves_no_claim_and_no_orphan_coordinator(self) -> None:
        # The coordinator can already have published this node's membership and started its watch
        # tasks when setup fails. It is about to go out of scope unregistered — nobody could ever
        # stop it — and the claim its kernel made must not outlive the kernel either.
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)

        async def boom(meta: Any, self_member: Any) -> None:
            raise RuntimeError("ip link add failed")

        backend.setup_session_network = boom  # type: ignore[method-assign]
        with pytest.raises(RuntimeError):
            await facade.ensure_session("s1", "c1", _VXLAN_NC)

        assert "s1" not in facade._coordinators
        assert "network/session/s1/members/agent-1" not in etcd.store  # unwound, not left published
        assert backend.torndown == ["s1"]  # the half-built data plane was torn back down

        # ...and the claim is gone: a later kernel of the session sets it up and, when it leaves,
        # the session is torn down — no stale claim from c1 holds it open.
        backend.setup_session_network = RecordingBackend.setup_session_network.__get__(backend)  # type: ignore[method-assign]
        await facade.ensure_session("s1", "c2", _VXLAN_NC)
        await facade.create_container("s1", "c2", image_ref="img", command=[], oci_spec={})
        assert backend.setup == ["s1"]

        await facade.remove_container("c2")
        assert backend.torndown == ["s1", "s1"]


class TestFailedAdopt:
    async def test_a_failed_adopt_does_not_tear_down_the_live_data_plane(self) -> None:
        # The unwind may only give back what THIS call built. A failed adopt must not stop the
        # coordinator: that deletes the devices and releases the LOCAL block of a data plane this
        # node did not build and whose kernels are still running on it. And the failure that trips
        # the adopt is the same transient etcd error that made the resume fail — correlated.
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        rt = FakeRuntime([
            _ContainerInfo("c1", {SESSION_ID_LABEL: "s1", OWNER_AGENT_LABEL: "agent-1"})
        ])
        facade = _facade(etcd, backend, runner, runtime=rt)

        async def boom(meta: Any, self_member: Any) -> None:
            raise RuntimeError("etcd is having a moment")

        backend.adopt_session_network = boom  # type: ignore[method-assign]
        with pytest.raises(RuntimeError):
            await facade.ensure_session("s1", "c2", _VXLAN_NC)

        assert backend.torndown == []  # c1's devices, block and membership are untouched
        assert "s1" not in facade._coordinators


class TestSetupUnderLiveContainers:
    async def test_a_session_whose_containers_survive_is_adopted_not_rebuilt(self) -> None:
        # "No coordinator" does not mean "no data plane": a session whose resume failed on the last
        # restart keeps running its kernels while this process knows nothing about it. Rebuilding
        # would delete the bridge they are enslaved to (setup clears devices by name) and purge the
        # addresses they hold — handing a live container's IP to the next kernel.
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        rt = FakeRuntime([
            _ContainerInfo("c1", {SESSION_ID_LABEL: "s1", OWNER_AGENT_LABEL: "agent-1"})
        ])
        facade = _facade(etcd, backend, runner, runtime=rt)

        await facade.ensure_session("s1", "c2", _VXLAN_NC)  # a NEW kernel of that same session

        assert backend.adopted == ["s1"]  # adopted the running data plane
        assert backend.setup == []  # never rebuilt it under the live container

        # ...and the survivor is adopted as a *user* of the session, not just left running: it must
        # keep the session open when the kernel that adopted it goes away, or the teardown would
        # delete the devices and release the addresses out from under a container that is still up.
        await facade.create_container("s1", "c2", image_ref="img", command=[], oci_spec={})
        await facade.remove_container("c2")
        assert backend.torndown == []
        assert "s1" in facade._coordinators

        await facade.remove_container("c1")  # the survivor finally goes
        assert backend.torndown == ["s1"]


class TestSessionLockLifetime:
    """The lock must keep its identity while anyone holds or waits on it. Dropping it on teardown
    the moment the lock is released hands the woken waiter an orphan, and the next arrival mints a
    fresh lock and sets the session up alongside it — the concurrent setup the lock exists to stop.
    """

    async def test_a_setup_arriving_after_a_teardown_cannot_overlap_the_one_it_woke(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        await facade.ensure_session("s1", "k1", _VXLAN_NC)

        gate = asyncio.Event()
        inflight = 0
        overlapped = False
        original = backend.setup_session_network

        async def gated_setup(meta: Any, self_member: Any) -> None:
            nonlocal inflight, overlapped
            inflight += 1
            overlapped |= inflight > 1
            await gate.wait()  # stay inside setup, so a later arrival gets the chance to overlap
            await original(meta, self_member)
            inflight -= 1

        backend.setup_session_network = gated_setup  # type: ignore[method-assign]

        teardown = asyncio.create_task(facade.teardown_session("s1"))
        await asyncio.sleep(0)  # the teardown takes the session's lock
        first = asyncio.create_task(
            facade.ensure_session("s1", "k1", _VXLAN_NC)
        )  # queues behind it
        await teardown  # releases the lock — and must NOT drop it while `first` is waiting on it
        for _ in range(3):
            await asyncio.sleep(0)  # `first` wakes and enters setup
        second = asyncio.create_task(facade.ensure_session("s1", "k1", _VXLAN_NC))  # arrives after
        for _ in range(3):
            await asyncio.sleep(0)  # a fresh lock here would let it set up alongside `first`

        gate.set()
        await asyncio.gather(first, second)
        try:
            assert not overlapped
        finally:
            await facade.teardown_session("s1")

    async def test_the_lock_registry_empties_once_the_session_is_gone(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        await facade.ensure_session("s1", "k1", _VXLAN_NC)
        await facade.teardown_session("s1")
        assert facade._session_locks == {}  # no unbounded growth across a node's session churn


class TestLaunchTerminate:
    async def test_launch_attaches_to_task_pid(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        meta = await facade.ensure_session("s1", "k1", _VXLAN_NC)  # registers the orchestrator
        try:
            result = await facade.launch_container(
                "s1",
                "c1",
                image_ref="img",
                command=["sleep", "600"],
                oci_spec={},
                meta=meta,
                kernel_config=cast(Any, {}),
                cluster_info=cast(Any, {}),
            )
            assert result.handle.pid == 9001
            assert runner.calls == [("ADD", "/proc/9001/ns/net")]
            assert "c1" in facade._attachments  # plan kept for later detach
        finally:
            await facade.teardown_session("s1")

    async def test_remove_after_launch_detaches_network(self) -> None:
        # The clean/remove phase must replay the attach-time plan as a DEL so the host veth,
        # IPAM address and MASQ rule are released (otherwise they leak across the node).
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        meta = await facade.ensure_session("s1", "k1", _VXLAN_NC)
        await facade.launch_container(
            "s1",
            "c1",
            image_ref="img",
            command=[],
            oci_spec={},
            meta=meta,
            kernel_config=cast(Any, {}),
            cluster_info=cast(Any, {}),
        )
        await facade.remove_container("c1")
        assert ("ADD", "/proc/9001/ns/net") in runner.calls
        assert ("DEL", "/proc/9001/ns/net") in runner.calls  # detach replayed on remove
        assert "c1" not in facade._attachments  # bookkeeping cleared


class TestSplitAndTeardown:
    async def test_create_container_routes_to_runtime(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "k1", _VXLAN_NC)
        try:
            await facade.create_container(
                "s1", "c1", image_ref="img:1", command=["sleep", "1"], oci_spec={}
            )
            assert rt.calls == ["create:c1:img:1"]  # created, not started
        finally:
            await facade.teardown_session("s1")

    async def test_start_and_attach_starts_then_attaches(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        meta = await facade.ensure_session("s1", "k1", _VXLAN_NC)
        try:
            await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})
            result = await facade.start_and_attach_container(
                "s1", "c1", meta=meta, kernel_config=cast(Any, {}), cluster_info=cast(Any, {})
            )
            assert rt.calls == ["create:c1:img", "create_task:c1", "start_task:c1"]
            assert runner.calls == [("ADD", "/proc/9001/ns/net")]
            assert result.handle.pid == 9001
        finally:
            await facade.teardown_session("s1")

    async def test_kill_and_remove_container(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.kill_container("c1", signal=9)
        await facade.remove_container("c1")
        assert rt.calls == ["kill:c1:9", "remove:c1"]


class TestDeterministicTeardown:
    async def test_removing_last_kernel_tears_down_session_network(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})
        assert "network/session/s1/members/agent-1" in etcd.store

        await facade.remove_container("c1")

        # last kernel gone -> devices + membership torn down, coordinator dropped
        assert backend.torndown == ["s1"]
        assert "network/session/s1/members/agent-1" not in etcd.store
        assert "s1" not in facade._coordinators

    async def test_teardown_only_after_last_kernel_removed(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.ensure_session("s1", "c2", _VXLAN_NC)
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})
        await facade.create_container("s1", "c2", image_ref="img", command=[], oci_spec={})

        await facade.remove_container("c1")
        assert backend.torndown == []  # c2 still alive -> keep the network
        assert "s1" in facade._coordinators

        await facade.remove_container("c2")
        assert backend.torndown == ["s1"]  # now the last one is gone

    async def test_remove_untracked_container_is_noop_teardown(self) -> None:
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.remove_container("unknown")  # never created here
        assert backend.torndown == []
        assert rt.calls == ["remove:unknown"]

    async def test_a_kernel_still_being_created_holds_the_session_open(self) -> None:
        # A kernel is created in stages (image pull, scratch, container) and the agent runs those
        # stages for several kernels of a session concurrently. Counting only *containers* made a
        # sibling that dies early look like the session's last kernel: it tore the data plane down
        # under a kernel that was still being built on it, which then found no orchestrator and
        # had no network.
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.ensure_session("s1", "c2", _VXLAN_NC)  # c2: still pulling its image
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})

        await facade.remove_container("c1")  # c1 dies at start; it is the only *container*

        assert backend.torndown == []  # c2 is still being created: the session stays up
        assert "s1" in facade._coordinators

        # c2 can still be built on it...
        await facade.create_container("s1", "c2", image_ref="img", command=[], oci_spec={})
        assert backend.torndown == []
        # ...and taking it away tears the session down, exactly once.
        await facade.remove_container("c2")
        assert backend.torndown == ["s1"]

    async def test_a_kernel_that_fails_before_its_container_still_releases_the_session(
        self,
    ) -> None:
        # The claim must not outlive a kernel that never got a container, or the session network
        # would be held open forever. clean_kernel removes every kernel the agent accepted, whether
        # its container was created or not (and a container's id IS its kernel id).
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.ensure_session("s1", "c2", _VXLAN_NC)
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})

        await facade.remove_container("c2")  # c2 failed during the pull: no container was created
        assert backend.torndown == []  # c1 is live

        await facade.remove_container("c1")
        assert backend.torndown == ["s1"]  # no stale claim keeps the session alive

    async def test_release_kernel_frees_a_claim_whose_kernel_never_got_a_container(self) -> None:
        # A kernel that dies before its container exists never reaches clean_kernel (the agent
        # registers a kernel only once its container is prepared, and a destroy for one it never
        # heard of queues no clean). Its claim must be released where the failure IS seen, or the
        # session network stays pinned for good — a permanent leak in place of a transient race.
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.ensure_session("s1", "c2", _VXLAN_NC)
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})

        await facade.release_kernel("c2")  # c2 blew up during the image pull
        assert backend.torndown == []  # c1 is live

        await facade.remove_container("c1")
        assert backend.torndown == ["s1"]  # nothing left holding the session open

    async def test_release_kernel_does_not_disturb_a_kernel_that_has_a_container(self) -> None:
        # Releasing a claim for a kernel whose container is running would tear the session down
        # under it. release_kernel must be a no-op there — that kernel's own removal decides.
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})

        await facade.release_kernel("c1")

        assert backend.torndown == []
        assert "s1" in facade._coordinators

    async def test_a_kernel_reaching_a_torn_down_session_gets_a_named_error(self) -> None:
        # The guard behind the reservation: a bare KeyError on the orchestrator dict said nothing.
        etcd, backend, runner, rt = FakeEtcd(), RecordingBackend(), RecordingRunner(), FakeRuntime()
        facade = _facade(etcd, backend, runner, runtime=rt)
        await facade.ensure_session("s1", "c1", _VXLAN_NC)
        await facade.teardown_session("s1")
        with pytest.raises(SessionNetworkGone):
            await facade.create_container("s1", "c1", image_ref="img", command=[], oci_spec={})


class TestBackendResolution:
    async def test_selects_backend_by_session_config(self) -> None:
        etcd, runner = FakeEtcd(), RecordingRunner()
        vxlan_b, hostgw_b = RecordingBackend(), RecordingBackend()
        facade = _facade(etcd, vxlan_b, runner, backends={"vxlan": vxlan_b, "host-gw": hostgw_b})
        await facade.ensure_session("sv", "k1", _VXLAN_NC)
        await facade.ensure_session("sh", "k1", _HOSTGW_NC)
        try:
            assert vxlan_b.setup == ["sv"]  # vxlan config -> vxlan backend only
            assert hostgw_b.setup == ["sh"]  # host-gw config -> host-gw backend only
        finally:
            await facade.teardown_session("sv")
            await facade.teardown_session("sh")

    async def test_unknown_backend_raises(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner, backends={"vxlan": cast(Any, backend)})
        with pytest.raises(UnknownNetworkBackend):
            await facade.ensure_session("s1", "k1", _HOSTGW_NC)  # host-gw not registered


class TestFactory:
    def test_builds_facade_with_defaults(self) -> None:
        # default path registers the vxlan + bridge backends and the containerd gRPC runtime
        facade = build_containerd_session_network(
            cast(AbstractKVStore, FakeEtcd()),
            agent_id="agent-1",
            host_ip="192.168.0.10",
            uplink="lima0",
        )
        assert isinstance(facade, ContainerdSessionNetwork)
        assert "vxlan" in facade._backends
        assert "bridge" in facade._backends

    def test_injected_collaborators_are_used(self) -> None:
        backend, runner = RecordingBackend(), RecordingRunner()
        facade = build_containerd_session_network(
            cast(AbstractKVStore, FakeEtcd()),
            agent_id="agent-1",
            host_ip="192.168.0.10",
            runtime=FakeRuntime(),
            cni_runner=runner,
            backends={"vxlan": cast(Any, backend)},
        )
        assert cast(Any, facade._backends["vxlan"]) is backend


@pytest.mark.parametrize("nc", [_VXLAN_NC, _HOSTGW_NC])
def test_meta_roundtrip_backend(nc: dict[str, Any]) -> None:
    meta = session_net_meta_from_network_config("sX", nc)
    assert str(meta.backend) == nc["backend"]
