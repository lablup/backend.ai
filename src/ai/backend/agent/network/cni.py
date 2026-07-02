"""EndpointPlan -> CNI attach chain (BEP-1055).

Runtime-neutral consumption of a v2 backend's `EndpointPlan`: turn the ordered
interface chain into ordered CNI ADD operations (and DEL in reverse for detach).
The actual CNI plugin execution (exec the binary with the CNI_* environment and the
config on stdin) is isolated behind an injected runner; a containerd provisioner
supplies the container's netns and a real runner. Everything here is pure/testable.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ai.backend.common.network.types import AttachKind, EndpointPlan, NetworkRole


@dataclass(frozen=True)
class CniInvocation:
    ifname: str
    role: NetworkRole
    config: Mapping[str, Any]


# runner(command, *, ifname, netns, container_id, config)
CniRunner = Callable[..., Awaitable[None]]


def plan_to_invocations(plan: EndpointPlan) -> list[CniInvocation]:
    """Ordered CNI invocations for a plan's CNI attachments (order preserved:
    LOCAL first, then OVERLAY)."""
    return [
        CniInvocation(a.interface_name, a.role, a.cni_config or {})
        for a in plan.attachments
        if a.kind is AttachKind.CNI
    ]


class CniAttacher:
    """Applies / removes an EndpointPlan against a container netns via CNI."""

    _runner: CniRunner

    def __init__(self, runner: CniRunner) -> None:
        self._runner = runner

    async def attach(self, plan: EndpointPlan, *, container_id: str, netns: str) -> None:
        for inv in plan_to_invocations(plan):
            await self._runner(
                "ADD",
                ifname=inv.ifname,
                netns=netns,
                container_id=container_id,
                config=inv.config,
            )

    async def detach(self, plan: EndpointPlan, *, container_id: str, netns: str) -> None:
        # tear down in reverse order of attach
        for inv in reversed(plan_to_invocations(plan)):
            await self._runner(
                "DEL",
                ifname=inv.ifname,
                netns=netns,
                container_id=container_id,
                config=inv.config,
            )
