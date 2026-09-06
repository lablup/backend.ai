import asyncio
from typing import Any, cast, override

import pytest

from ai.backend.agent.network.cni import (
    CniAttacher,
    CniInvocation,
    CniRunner,
    plan_to_invocations,
)
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkRole,
)


def _plan() -> EndpointPlan:
    return EndpointPlan(
        attachments=[
            NetworkAttachSpec(
                kind=AttachKind.CNI,
                interface_name="eth0",
                role=NetworkRole.LOCAL,
                is_default_route=True,
                cni_config={"type": "bridge", "bridge": "bai-local0"},
            ),
            NetworkAttachSpec(
                kind=AttachKind.CNI,
                interface_name="baimulti0",
                role=NetworkRole.OVERLAY,
                cni_config={"type": "bridge", "bridge": "baibr4097"},
            ),
        ]
    )


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.configs: list[Any] = []

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, ifname))
        self.configs.append(config)


class TestPlanToInvocations:
    def test_preserves_local_then_overlay_order(self) -> None:
        invs = plan_to_invocations(_plan())
        assert [i.role for i in invs] == [NetworkRole.LOCAL, NetworkRole.OVERLAY]
        assert [i.ifname for i in invs] == ["eth0", "baimulti0"]

    def test_skips_non_cni_attachments(self) -> None:
        plan = EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.DOCKER_NETWORK,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    cni_config={"type": "bridge"},
                ),
            ]
        )
        invs = plan_to_invocations(plan)
        assert [i.ifname for i in invs] == ["baimulti0"]


class TestEffectiveConfig:
    def test_injects_declared_capability_arg_into_runtime_config(self) -> None:
        inv = CniInvocation(
            "eth0",
            NetworkRole.LOCAL,
            {"type": "bridge", "capabilities": {"ips": True}},
            {"ips": ["172.30.1.5/26"]},
        )
        assert inv.effective_config()["runtimeConfig"] == {"ips": ["172.30.1.5/26"]}

    def test_drops_an_undeclared_capability_arg(self) -> None:
        # A conforming CNI runtime injects runtimeConfig only for capabilities the config declares.
        inv = CniInvocation(
            "eth0", NetworkRole.LOCAL, {"type": "bridge"}, {"mac": "02:42:00:00:00:01"}
        )
        assert "runtimeConfig" not in inv.effective_config()

    def test_no_capability_args_is_identity(self) -> None:
        config = {"type": "bridge", "capabilities": {"mac": True}}
        inv = CniInvocation("eth0", NetworkRole.OVERLAY, config)
        assert inv.effective_config() is config


class TestCniAttacher:
    async def test_attach_passes_injected_runtime_config_to_the_runner(self) -> None:
        runner = RecordingRunner()
        plan = EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    cni_config={"type": "bridge", "capabilities": {"mac": True}},
                    cni_capability_args={"mac": "02:42:0a:80:05:07"},
                ),
            ]
        )
        await CniAttacher(runner).attach(plan, container_id="c1", netns="/proc/1/ns/net")
        assert runner.configs[0]["runtimeConfig"] == {"mac": "02:42:0a:80:05:07"}

    async def test_attach_issues_add_in_order(self) -> None:
        runner = RecordingRunner()
        await CniAttacher(runner).attach(_plan(), container_id="c1", netns="/proc/1/ns/net")
        assert runner.calls == [("ADD", "eth0"), ("ADD", "baimulti0")]

    async def test_detach_issues_del_in_reverse(self) -> None:
        runner = RecordingRunner()
        await CniAttacher(runner).detach(_plan(), container_id="c1", netns="/proc/1/ns/net")
        assert runner.calls == [("DEL", "baimulti0"), ("DEL", "eth0")]

    async def test_attach_rolls_back_applied_adds_on_failure(self) -> None:
        # OVERLAY ADD fails after LOCAL ADD succeeded: the LOCAL ADD must be rolled back (DEL) so
        # no half-attached veth/IPAM/MASQ survives (the caller records the plan only on success).
        # The FAILED ADD is rolled back too — a failed ADD can leave the container partly wired,
        # which is exactly why CNI requires a DEL after one, and DEL is idempotent.
        class FailingRunner:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str]] = []

            async def __call__(
                self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
            ) -> None:
                self.calls.append((command, ifname))
                if command == "ADD" and ifname == "baimulti0":
                    raise RuntimeError("overlay ADD failed")

        runner = FailingRunner()
        with pytest.raises(RuntimeError):
            await CniAttacher(runner).attach(_plan(), container_id="c1", netns="/proc/1/ns/net")
        assert runner.calls == [
            ("ADD", "eth0"),
            ("ADD", "baimulti0"),  # failed
            ("DEL", "baimulti0"),  # ...and is cleaned up: it may have wired part of the container
            ("DEL", "eth0"),  # rollback of the one that succeeded
        ]


class TestAnAttachThatDidNotFinish:
    """D2, the container side. An attach applies interfaces one at a time, and until it returns
    nobody else knows they exist -- the caller records the plan only on success. So whatever it
    left had to be undone here, on every way out."""

    @staticmethod
    def _plan_of_two() -> EndpointPlan:
        return _plan()

    async def test_a_cancelled_attach_removes_what_it_applied(self) -> None:
        started = asyncio.Event()

        class StallsOnTheSecond(RecordingRunner):
            @override
            async def __call__(
                self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
            ) -> None:
                await super().__call__(
                    command, ifname=ifname, netns=netns, container_id=container_id, config=config
                )
                if ifname == "baimulti0" and command == "ADD":
                    started.set()
                    await asyncio.sleep(60)

        runner = StallsOnTheSecond()
        attacher = CniAttacher(cast(CniRunner, runner))
        task = asyncio.create_task(
            attacher.attach(self._plan_of_two(), container_id="c1", netns="/proc/1/ns/net")
        )
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert ("DEL", "eth0") in runner.calls, "the interface it had already applied stayed"

    async def test_one_del_that_fails_does_not_stop_the_others(self) -> None:
        # Stopping at the first would leave the earlier interfaces behind, which are the ones
        # this is here for.
        class RefusesTheOverlayDel(RecordingRunner):
            @override
            async def __call__(
                self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
            ) -> None:
                await super().__call__(
                    command, ifname=ifname, netns=netns, container_id=container_id, config=config
                )
                if command == "ADD" and ifname == "baimulti0":
                    raise RuntimeError("the overlay bridge is missing")
                if command == "DEL" and ifname == "baimulti0":
                    raise RuntimeError("iproute2 said no")

        runner = RefusesTheOverlayDel()
        attacher = CniAttacher(cast(CniRunner, runner))
        with pytest.raises(RuntimeError):
            await attacher.attach(_plan(), container_id="c1", netns="/proc/1/ns/net")

        assert ("DEL", "eth0") in runner.calls
