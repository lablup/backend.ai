import json
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
from ai.backend.agent.containerd.session_network import (
    ContainerdSessionNetwork,
    session_net_meta_from_network_config,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    EndpointPlan,
    Member,
    NetworkBackendKind,
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
            k[len(prefix):]: v
            for k, v in self.store.items()
            if k.startswith(prefix) and "/" not in k[len(prefix):]
        }

    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        return
        yield  # pragma: no cover


class RecordingBackend:
    """Minimal AbstractNetworkAgentPluginV2-shaped stub recording setup calls."""

    def __init__(self) -> None:
        self.setup: list[str] = []

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.setup.append(meta.session_id)
        self.last_self_member = self_member

    async def teardown_session_network(self, session_id: str) -> None: ...
    async def add_peer(self, session_id: str, peer: Member) -> None: ...
    async def del_peer(self, session_id: str, peer: Member) -> None: ...
    async def probe_caps(self) -> AgentNetworkCaps:
        return AgentNetworkCaps(tunnel_offload=False, native_routing_ok=False)


class FakeRuntime(ContainerdRuntimeClient):
    async def image_exists(self, image_ref: str) -> bool:
        return True

    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None: ...
    async def list_images(self) -> Sequence[str]:
        return []

    async def remove_image(self, image_ref: str) -> None: ...
    async def create_container(
        self, container_id: str, *, image_ref: str, command: Sequence[str], oci_spec: Mapping[str, Any]
    ) -> None: ...
    async def start_container(self, container_id: str) -> TaskHandle:
        return TaskHandle(container_id=container_id, pid=9001)

    async def kill_container(self, container_id: str, *, signal: int) -> None: ...
    async def remove_container(self, container_id: str) -> None: ...
    async def list_containers(self) -> Sequence[str]:
        return []

    async def container_pid(self, container_id: str) -> int | None:
        return 9001


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, netns))


def _facade(etcd: FakeEtcd, backend: RecordingBackend, runner: RecordingRunner) -> ContainerdSessionNetwork:
    return ContainerdSessionNetwork(
        cast(AbstractKVStore, etcd),
        agent_id="agent-1",
        host_ip="192.168.0.10",
        backend=cast(Any, backend),
        runtime=FakeRuntime(),
        cni_runner=runner,
    )


class TestEnsureSession:
    async def test_sets_up_and_publishes_self_member_with_vtep(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        meta = await facade.ensure_session("s1", _VXLAN_NC)
        try:
            assert backend.setup == ["s1"]
            # vxlan -> self member advertises its vtep = host_ip
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
        await facade.ensure_session("s2", _HOSTGW_NC)
        try:
            assert backend.last_self_member.vtep_ip is None
        finally:
            await facade.teardown_session("s2")


class TestLaunchTerminate:
    async def test_launch_attaches_to_task_pid(self) -> None:
        etcd, backend, runner = FakeEtcd(), RecordingBackend(), RecordingRunner()
        facade = _facade(etcd, backend, runner)
        meta = session_net_meta_from_network_config("s1", _VXLAN_NC)

        # backend.attach_endpoint is required by the provisioner; add it on the stub
        async def attach_endpoint(kc: Any, ci: Any, *, meta: SessionNetMeta) -> EndpointPlan:
            from ai.backend.common.network.types import AttachKind, NetworkAttachSpec, NetworkRole
            return EndpointPlan(attachments=[
                NetworkAttachSpec(kind=AttachKind.CNI, interface_name="baimulti0",
                                  role=NetworkRole.OVERLAY, cni_config={"type": "bridge"})
            ])
        backend.attach_endpoint = attach_endpoint  # type: ignore[attr-defined]

        result = await facade.launch_container(
            "c1", image_ref="img", command=["sleep", "600"], oci_spec={},
            meta=meta, kernel_config=cast(Any, {}), cluster_info=cast(Any, {}),
        )
        assert result.handle.pid == 9001
        assert runner.calls == [("ADD", "/proc/9001/ns/net")]


@pytest.mark.parametrize("nc", [_VXLAN_NC, _HOSTGW_NC])
def test_meta_roundtrip_backend(nc: dict[str, Any]) -> None:
    meta = session_net_meta_from_network_config("sX", nc)
    assert str(meta.backend) == nc["backend"]
