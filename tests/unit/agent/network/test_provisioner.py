import asyncio
from typing import Any, cast

import pytest

from ai.backend.agent.errors.network import ContainerAttachFailed
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


class _RunnerThatRaises:
    """A CNI runner whose ADD fails the way the host does, and whose DELs still work.

    The DELs matter: the attacher undoes its own partial work before the failure leaves it, and a
    fake that failed those too would be testing the undo instead of what the caller is told.
    """

    def __init__(self, error: BaseException) -> None:
        self._error = error
        self.calls: list[str] = []

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> dict[str, Any] | None:
        self.calls.append(f"{command}:{ifname}")
        if command == "ADD":
            raise self._error
        return None


class TestWhatAFailedAttachLeavesTheCallerHolding:
    """The plan names the host veth, the address and the rules the attach puts on this host. A
    failure -- above all a CANCELLATION, which is how the kernel-creation timeout and the agent
    stopping arrive -- must not be the moment the caller first hears about it."""

    async def test_the_plan_arrives_before_a_single_interface_is_applied(self) -> None:
        backend = FakeBackend(_plan())
        runner = RecordingRunner()
        prov = ContainerNetworkProvisioner(cast(Any, backend), runner)
        order: list[str] = []

        await prov.attach(
            cast(KernelCreationConfig, {}),
            cast(ClusterInfo, {}),
            meta=_META,
            container_id="c1",
            task_pid=4242,
            on_planned=lambda plan: order.append(f"planned:{len(plan.attachments)}"),
        )
        assert order == ["planned:2"]
        assert runner.calls, "nothing was applied, so the ordering claim proves nothing"

    async def test_a_cancelled_attach_stays_cancelled(self) -> None:
        # It used to be caught as a BaseException and handed on as a plain Exception, which threw
        # away what asyncio.timeout, an agent shutdown and a cancelled parent task all mean.
        backend = FakeBackend(_plan())
        runner = _RunnerThatRaises(asyncio.CancelledError())
        prov = ContainerNetworkProvisioner(cast(Any, backend), runner)
        planned: list[Any] = []

        with pytest.raises(asyncio.CancelledError):
            await prov.attach(
                cast(KernelCreationConfig, {}),
                cast(ClusterInfo, {}),
                meta=_META,
                container_id="c1",
                task_pid=4242,
                on_planned=planned.append,
            )
        # ... and the caller still holds what the cancelled attach may have left on the host.
        assert len(planned) == 1
        assert planned[0].attachments

    async def test_a_failed_attach_is_named_for_the_manager(self) -> None:
        backend = FakeBackend(_plan())
        runner = _RunnerThatRaises(RuntimeError("RTNETLINK answers: Operation not permitted"))
        prov = ContainerNetworkProvisioner(cast(Any, backend), runner)

        with pytest.raises(ContainerAttachFailed) as caught:
            await prov.attach(
                cast(KernelCreationConfig, {}),
                cast(ClusterInfo, {}),
                meta=_META,
                container_id="c1",
                task_pid=4242,
            )
        # The container and the session, which an `ip` command's RuntimeError does not carry.
        assert "c1" in str(caught.value)
        assert "s1" in str(caught.value)
        assert isinstance(caught.value.__cause__, RuntimeError)
