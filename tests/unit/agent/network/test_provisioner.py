import asyncio
from typing import Any, cast, override

import pytest

from ai.backend.agent.errors.network import ContainerAttachFailed
from ai.backend.agent.network.orchestrator import ContainerdKernelOrchestrator
from ai.backend.agent.network.privnet.client import PrivNetProvisioner
from ai.backend.agent.network.provisioner import (
    CniProvisioner,
    ContainerNetworkProvisioner,
)
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


class TestCniProvisioner:
    async def test_attach_builds_plan_and_applies_cni_with_pid_netns(self) -> None:
        backend = FakeBackend(_plan())
        runner = RecordingRunner()
        prov = CniProvisioner(cast(Any, backend), runner)

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
        prov = CniProvisioner(cast(Any, backend), runner)
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
        prov = CniProvisioner(cast(Any, backend), runner)
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
        prov = CniProvisioner(cast(Any, backend), runner)
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
        prov = CniProvisioner(cast(Any, backend), runner)

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


class _RecordingClient:
    """Stands in for the privnet's unix-socket client, remembering call order."""

    def __init__(self, events: list[str]) -> None:
        self._events = events

    async def call(self, request: Any) -> Any:
        self._events.append(f"rpc:{request.op.value}")

        class _Resp:
            assigned = {"local": "172.30.0.2"}

        return _Resp()


class TestEveryProvisionerHonoursOnPlanned:
    """Both implementations are handed to the same orchestrator, which always passes
    ``on_planned``. The privnet one shipped without the parameter at all, so every multi-node
    session died on a `TypeError` -- the signature is checked here, and so is the ordering that
    makes the callback worth having.
    """

    @pytest.fixture
    def provisioners(self) -> list[tuple[str, Any, list[str]]]:
        cni_events: list[str] = []
        privnet_events: list[str] = []

        class _EventBackend(FakeBackend):
            @override
            async def attach_endpoint(
                self, kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta
            ) -> EndpointPlan:
                cni_events.append("rpc:plan")
                return await super().attach_endpoint(kernel_config, cluster_info, meta=meta)

        class _EventRunner(RecordingRunner):
            @override
            async def __call__(self, command: str, **kwargs: Any) -> dict[str, Any] | None:
                cni_events.append(f"apply:{command}")
                return await super().__call__(command, **kwargs)

        return [
            ("cni", CniProvisioner(cast(Any, _EventBackend(_plan())), _EventRunner()), cni_events),
            (
                "privnet",
                PrivNetProvisioner(cast(Any, _RecordingClient(privnet_events)), "s1"),
                privnet_events,
            ),
        ]

    async def test_the_plan_reaches_the_caller_before_anything_is_applied(
        self, provisioners: list[tuple[str, Any, list[str]]]
    ) -> None:
        for name, prov, events in provisioners:
            seen: list[EndpointPlan] = []

            def record(plan: EndpointPlan, _seen: list[EndpointPlan] = seen) -> None:
                _seen.append(plan)

            events.append("__mark__")
            returned, _assigned = await prov.attach(
                cast(KernelCreationConfig, {}),
                cast(ClusterInfo, {}),
                meta=_META,
                container_id="c1",
                task_pid=4321,
                on_planned=record,
            )
            assert seen, f"{name} accepted on_planned and never called it"
            after_mark = events[events.index("__mark__") + 1 :]
            assert after_mark, f"{name} did no work at all; the ordering check proves nothing"
            assert seen[0] is returned, (
                f"{name} handed the caller a plan it did not return; detach would be given a"
                " different object than the one the attach produced"
            )

    async def test_a_cancelled_attach_still_left_the_caller_a_plan(
        self, provisioners: list[tuple[str, Any, list[str]]]
    ) -> None:
        """The reason the callback exists: recorded early, a container interrupted mid-attach is
        still detachable; recorded on return, it leaks."""
        for name, prov, _events in provisioners:
            seen: list[EndpointPlan] = []

            def record(plan: EndpointPlan, _seen: list[EndpointPlan] = seen) -> None:
                _seen.append(plan)
                raise asyncio.CancelledError

            with pytest.raises(asyncio.CancelledError):
                await prov.attach(
                    cast(KernelCreationConfig, {}),
                    cast(ClusterInfo, {}),
                    meta=_META,
                    container_id="c1",
                    task_pid=4321,
                    on_planned=record,
                )
            assert seen, f"{name} was cancelled before it told the caller what to detach"


def _every_implementation() -> list[ContainerNetworkProvisioner]:
    """Both provisioners, bound to the protocol the orchestrator holds them by.

    The binding is the test: it is `pants check` that verifies it, and that is the check the
    branch did not have. `PrivNetProvisioner` is a structural drop-in built by a factory annotated
    `-> Any`, so nothing ever compared the two -- it shipped without `on_planned`, which the
    orchestrator always passes, and every multi-node session died on a `TypeError` no type check
    could see. Adding a method to the protocol without adding it to both now fails here.
    """
    return [
        CniProvisioner(cast(Any, FakeBackend(_plan())), RecordingRunner()),
        PrivNetProvisioner(cast(Any, None), "s1"),
    ]


class TestBothProvisionersAreTheSameThing:
    def test_the_protocol_binding_holds_for_every_implementation(self) -> None:
        assert len(_every_implementation()) == 2

    def test_the_orchestrator_accepts_either(self) -> None:
        """The seam the drift crossed: `ContainerdKernelOrchestrator` takes the protocol, and both
        are handed to it in production -- the in-process one, and the privnet one under a privnet."""
        for provisioner in _every_implementation():
            orchestrator = ContainerdKernelOrchestrator(None, provisioner)
            assert orchestrator is not None
