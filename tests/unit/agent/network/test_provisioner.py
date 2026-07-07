from typing import Any, cast

from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig

_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.5.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1450,
    vni=4097,
)


def _plan() -> EndpointPlan:
    return EndpointPlan(
        attachments=[
            NetworkAttachSpec(
                kind=AttachKind.CNI,
                interface_name="eth0",
                role=NetworkRole.LOCAL,
                is_default_route=True,
                cni_config={"type": "bridge"},
            ),
            NetworkAttachSpec(
                kind=AttachKind.CNI,
                interface_name="baimulti0",
                role=NetworkRole.OVERLAY,
                cni_config={"type": "bridge"},
            ),
        ]
    )


class FakeBackend:
    def __init__(self, plan: EndpointPlan) -> None:
        self._plan = plan
        self.attach_calls: list[str] = []

    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta
    ) -> EndpointPlan:
        self.attach_calls.append(meta.session_id)
        return self._plan


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []  # (command, ifname, netns)

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> dict[str, Any] | None:
        self.calls.append((command, ifname, netns))
        # Mimic a CNI ADD result: eth0 (LOCAL) -> 172.30.x, baimulti0 (OVERLAY) -> 10.128.x
        if command != "ADD":
            return None
        addr = "172.30.0.2/24" if ifname == "eth0" else "10.128.5.2/24"
        return {"ips": [{"address": addr}]}


class TestContainerNetworkProvisioner:
    async def test_attach_builds_plan_and_applies_cni_with_pid_netns(self) -> None:
        backend = FakeBackend(_plan())
        runner = RecordingRunner()
        prov = ContainerNetworkProvisioner(cast(Any, backend), runner)

        plan, assigned = await prov.attach(
            cast(KernelCreationConfig, {}),
            cast(ClusterInfo, {}),
            meta=_META,
            container_id="c1",
            task_pid=4242,
        )
        assert backend.attach_calls == ["s1"]
        # ADD in order, netns derived from task pid
        assert runner.calls == [
            ("ADD", "eth0", "/proc/4242/ns/net"),
            ("ADD", "baimulti0", "/proc/4242/ns/net"),
        ]
        assert plan.overlay() is not None
        # assigned IPs are captured per role (LOCAL is the host-reachable control address)
        assert assigned[NetworkRole.LOCAL] == "172.30.0.2"
        assert assigned[NetworkRole.OVERLAY] == "10.128.5.2"

    async def test_detach_removes_in_reverse_with_pid_netns(self) -> None:
        backend = FakeBackend(_plan())
        runner = RecordingRunner()
        prov = ContainerNetworkProvisioner(cast(Any, backend), runner)
        await prov.detach(_plan(), container_id="c1", task_pid=4242)
        assert runner.calls == [
            ("DEL", "baimulti0", "/proc/4242/ns/net"),
            ("DEL", "eth0", "/proc/4242/ns/net"),
        ]
