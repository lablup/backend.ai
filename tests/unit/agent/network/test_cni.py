from typing import Any

import pytest

from ai.backend.agent.network.cni import CniAttacher, plan_to_invocations
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

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, ifname))


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


class TestCniAttacher:
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
