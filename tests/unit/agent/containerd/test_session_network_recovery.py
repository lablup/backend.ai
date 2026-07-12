"""Restart recovery for the containerd session network (BEP-1062).

A restart empties the process memory that names the host resources — attach plans, the
container<->session tracker, the per-session coordinators — while the resources themselves
(bridges, veths, IPAM leases, MASQ rules) survive. These tests pin what `recover` rebuilds from
ground truth, and what it gives back to the durable journals.
"""

import json
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.oci import SESSION_ID_LABEL
from ai.backend.agent.containerd.session_network import ContainerdSessionNetwork
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator
from ai.backend.agent.network.native_attacher import HostLocalIpam
from ai.backend.common.network.keys import endpoint_key, member_key, session_meta_key
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkRole,
    SessionNetMeta,
)

_AGENT_ID = "a1"
_HOST_IP = "10.0.0.1"
_SUBNET = "172.30.0.0/24"
_META_JSON = json.dumps({"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450})


@dataclass
class _ContainerInfo:
    id: str
    labels: Mapping[str, str]
    image: str = "img"
    status: str = "running"


class FakeEtcd:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str, **kwargs: Any) -> str | None:
        return self.store.get(key)

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


class FakeRuntime:
    def __init__(self, containers: list[_ContainerInfo], pids: dict[str, int | None]) -> None:
        self.containers = containers
        self.pids = pids
        self.removed: list[str] = []

    async def list_container_infos(self) -> list[_ContainerInfo]:
        return self.containers

    async def container_pid(self, container_id: str) -> int | None:
        return self.pids.get(container_id)

    async def remove_container(self, container_id: str) -> None:
        self.removed.append(container_id)


class RecordingBackend:
    """Records which lifecycle verb the coordinator drove, so a resume can be told from a setup."""

    def __init__(self) -> None:
        self.setup: list[str] = []
        self.adopted: list[str] = []
        self.torndown: list[str] = []

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.setup.append(meta.session_id)

    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.adopted.append(meta.session_id)

    async def teardown_session_network(self, session_id: str) -> None:
        self.torndown.append(session_id)

    async def add_peer(self, session_id: str, peer: Member) -> None: ...
    async def del_peer(self, session_id: str, peer: Member) -> None: ...
    async def add_endpoint(self, session_id: str, **kwargs: Any) -> None: ...
    async def del_endpoint(self, session_id: str, **kwargs: Any) -> None: ...

    async def probe_caps(self) -> AgentNetworkCaps:
        return AgentNetworkCaps(tunnel_offload=False, native_routing_ok=False)

    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta
    ) -> EndpointPlan:
        # the overlay IP the manager assigned reaches the plan through kernel_config
        overlay_ip = dict(kernel_config).get("cluster_network_ip")
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    cni_config={
                        "ipam": {"type": "host-local", "subnet": _SUBNET},
                        "ip": overlay_ip,
                    },
                )
            ]
        )


class CniRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, command: str, **kwargs: Any) -> dict[str, Any] | None:
        self.calls.append({"command": command, **kwargs})
        return None

    def dels(self) -> list[dict[str, Any]]:
        return [c for c in self.calls if c["command"] == "DEL"]


def _build(
    *,
    containers: list[_ContainerInfo],
    pids: dict[str, int | None],
    etcd: FakeEtcd,
    backend: RecordingBackend,
    cni: CniRecorder,
    local_subnets: LocalSubnetAllocator | None = None,
    ipam: HostLocalIpam | None = None,
) -> tuple[ContainerdSessionNetwork, FakeRuntime]:
    runtime = FakeRuntime(containers, pids)
    net = ContainerdSessionNetwork(
        cast(Any, etcd),
        agent_id=_AGENT_ID,
        host_ip=_HOST_IP,
        runtime=cast(Any, runtime),
        cni_runner=cast(Any, cni),
        backends={"vxlan": cast(Any, backend)},
        local_subnets=local_subnets,
        ipam=ipam,
    )
    return net, runtime


@pytest.fixture
def etcd() -> FakeEtcd:
    e = FakeEtcd()
    e.store[session_meta_key("s1")] = _META_JSON
    return e


class TestResumeLiveSessions:
    async def test_adopts_rather_than_rebuilds_the_data_plane(self, etcd: FakeEtcd) -> None:
        # setup_session_network deletes and recreates host devices by name; running it against a
        # session whose containers survived the restart would cut them off the network.
        backend = RecordingBackend()
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=backend,
            cni=CniRecorder(),
        )
        await net.recover()
        assert backend.adopted == ["s1"]
        assert backend.setup == []

    async def test_republishes_this_node_membership(self, etcd: FakeEtcd) -> None:
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=CniRecorder(),
        )
        await net.recover()
        assert member_key("s1", _AGENT_ID) in etcd.store

    async def test_recovers_the_attachment_with_the_manager_assigned_overlay_ip(
        self, etcd: FakeEtcd
    ) -> None:
        etcd.store[endpoint_key("s1", "c1")] = json.dumps({
            "ip": "10.128.5.9",
            "mac": "02:42:0a:80:05:09",
            "agent_id": _AGENT_ID,
        })
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=CniRecorder(),
        )
        await net.recover()

        session_id, plan, pid = net._attachments["c1"]
        assert session_id == "s1"
        assert pid == 4242
        # the plan is re-derived from durable state, not remembered
        cni_config = plan.attachments[0].cni_config
        assert cni_config is not None
        assert cni_config["ip"] == "10.128.5.9"

    async def test_a_container_without_a_live_task_yields_no_attachment(
        self, etcd: FakeEtcd
    ) -> None:
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": None},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=CniRecorder(),
        )
        await net.recover()
        assert "c1" not in net._attachments

    async def test_one_containers_plan_failure_does_not_abort_the_rest(
        self, etcd: FakeEtcd
    ) -> None:
        # re-deriving a plan can raise (e.g. the vxlan backend now raises when a container's overlay
        # endpoint is gone from etcd). That must not strand the other live containers untracked.
        backend = RecordingBackend()
        calls = {"n": 0}
        orig = backend.attach_endpoint

        async def flaky(kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta) -> Any:
            calls["n"] += 1
            if calls["n"] == 1:  # the first container's re-derivation fails
                raise RuntimeError("plan re-derivation failed")
            return await orig(kernel_config, cluster_info, meta=meta)

        backend.attach_endpoint = flaky  # type: ignore[method-assign]

        net, _ = _build(
            containers=[
                _ContainerInfo("c1", {SESSION_ID_LABEL: "s1"}),
                _ContainerInfo("c2", {SESSION_ID_LABEL: "s1"}),
            ],
            pids={"c1": 1, "c2": 2},
            etcd=etcd,
            backend=backend,
            cni=CniRecorder(),
        )
        await net.recover()  # must not raise
        # exactly one recovered; both remain tracked so neither leaks its session teardown
        assert len(net._attachments) == 1

    async def test_a_session_without_meta_is_not_resumed(self) -> None:
        backend = RecordingBackend()
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "gone"})],
            pids={"c1": 4242},
            etcd=FakeEtcd(),  # manager dropped the meta
            backend=backend,
            cni=CniRecorder(),
        )
        await net.recover()  # must not raise
        assert backend.adopted == []
        assert "c1" not in net._attachments


class TestCleanupAfterRecovery:
    async def test_remove_container_detaches_using_the_recovered_plan(self, etcd: FakeEtcd) -> None:
        # the whole point: before this, a restarted agent's clean_kernel skipped detach entirely,
        # leaking the host veth, the IPAM lease and the MASQ rule.
        cni = CniRecorder()
        net, runtime = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=cni,
        )
        await net.recover()
        await net.remove_container("c1")

        assert [d["container_id"] for d in cni.dels()] == ["c1"]
        assert runtime.removed == ["c1"]

    async def test_removing_the_last_container_tears_the_session_down(self, etcd: FakeEtcd) -> None:
        backend = RecordingBackend()
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=backend,
            cni=CniRecorder(),
        )
        await net.recover()
        await net.remove_container("c1")
        assert backend.torndown == ["s1"]

    async def test_a_session_keeps_running_while_a_sibling_container_remains(
        self, etcd: FakeEtcd
    ) -> None:
        backend = RecordingBackend()
        net, _ = _build(
            containers=[
                _ContainerInfo("c1", {SESSION_ID_LABEL: "s1"}),
                _ContainerInfo("c2", {SESSION_ID_LABEL: "s1"}),
            ],
            pids={"c1": 1, "c2": 2},
            etcd=etcd,
            backend=backend,
            cni=CniRecorder(),
        )
        await net.recover()
        await net.remove_container("c1")
        assert backend.torndown == []


class TestJournalReclamation:
    async def test_reclaims_the_subnet_block_of_a_dead_session(
        self, etcd: FakeEtcd, tmp_path: Path
    ) -> None:
        # A durable journal that is never reconciled only grows; the pool holds 256 blocks.
        allocator = LocalSubnetAllocator(tmp_path / "subnets")
        await allocator.allocate("s1")  # live
        await allocator.allocate("dead")  # died while the agent was down

        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=CniRecorder(),
            local_subnets=allocator,
        )
        await net.recover()

        assert await allocator.sessions() == frozenset({"s1"})

    async def test_a_live_session_whose_meta_is_gone_keeps_its_block(self, tmp_path: Path) -> None:
        # The manager dropped s1's meta while the agent was down, so s1 does not resume — but its
        # container is still live and its bridge is up. Reclaiming its /24 would hand the block to a
        # new session, whose setup would delete s1's live bridge. It must be kept.
        allocator = LocalSubnetAllocator(tmp_path / "subnets")
        await allocator.allocate("s1")
        await allocator.allocate("truly-dead")

        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=FakeEtcd(),  # no meta for s1 -> not resumed, but c1 is live
            backend=RecordingBackend(),
            cni=CniRecorder(),
            local_subnets=allocator,
        )
        await net.recover()

        # s1 survives (live container), only the session with no live container is reclaimed
        assert await allocator.sessions() == frozenset({"s1"})

    async def test_reclaims_the_address_and_veth_of_a_dead_container(
        self, etcd: FakeEtcd, tmp_path: Path
    ) -> None:
        ipam = HostLocalIpam(tmp_path / "ipam")
        await ipam.allocate(_SUBNET, "c1", "eth0", reserve=["172.30.0.1"])  # live
        await ipam.allocate(_SUBNET, "dead", "eth0", reserve=["172.30.0.1"])  # gone

        cni = CniRecorder()
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=cni,
            ipam=ipam,
        )
        await net.recover()

        reclaimed = [d for d in cni.dels() if d["container_id"] == "dead"]
        assert len(reclaimed) == 1
        assert reclaimed[0]["ifname"] == "eth0"
        assert reclaimed[0]["config"]["ipam"]["subnet"] == _SUBNET
        # the live container's address is untouched
        assert [d["container_id"] for d in cni.dels()] == ["dead"]

    async def test_a_helper_owned_store_is_never_reclaimed(self, etcd: FakeEtcd) -> None:
        # Under a privileged helper the journals are None: the helper owns the host state, keeps
        # its own records, and outlives the agent.
        cni = CniRecorder()
        net, _ = _build(
            containers=[_ContainerInfo("c1", {SESSION_ID_LABEL: "s1"})],
            pids={"c1": 4242},
            etcd=etcd,
            backend=RecordingBackend(),
            cni=cni,
            local_subnets=None,
            ipam=None,
        )
        await net.recover()
        assert cni.dels() == []
