from collections.abc import Sequence
from typing import Any, cast

import pytest

from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
from ai.backend.common.network.types import (
    EndpointPlan,
    Member,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)


def _subnet(plan: EndpointPlan) -> str:
    cfg = plan.attachments[0].cni_config
    assert cfg is not None
    return str(cfg["ipam"]["subnet"])


def _meta(session_id: str) -> SessionNetMeta:
    return SessionNetMeta(
        session_id=session_id,
        subnet="172.30.0.0/24",
        backend=NetworkBackendKind.BRIDGE,
        mtu=1500,
        vni=None,
    )


class _Runner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def __call__(self, argv: Sequence[str]) -> None:
        self.calls.append(list(argv))


@pytest.fixture
def plugin() -> BridgeNetworkPlugin:
    return BridgeNetworkPlugin({}, {}, runner=_Runner())


class TestBridgeAttach:
    async def test_attach_returns_single_local_bridge(self, plugin: BridgeNetworkPlugin) -> None:
        plan = await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s1"))
        assert len(plan.attachments) == 1
        att = plan.attachments[0]
        assert att.role is NetworkRole.LOCAL
        assert att.is_default_route is True
        assert att.cni_config is not None
        assert att.cni_config["type"] == "bridge"
        assert att.cni_config["ipam"]["type"] == "host-local"

    async def test_subnet_is_node_local_and_stable(self, plugin: BridgeNetworkPlugin) -> None:
        p1 = await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s1"))
        p2 = await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s1"))
        subnet = _subnet(p1)
        assert subnet.startswith("172.30.")
        assert _subnet(p2) == subnet  # idempotent per session

    async def test_distinct_sessions_get_distinct_subnets(
        self, plugin: BridgeNetworkPlugin
    ) -> None:
        a = await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s1"))
        b = await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s2"))
        assert _subnet(a) != _subnet(b)


class TestBridgeLifecycle:
    async def test_no_overlay_peer_ops(self, plugin: BridgeNetworkPlugin) -> None:
        # single-node: peers are a no-op and must not touch the data plane
        runner = cast(_Runner, plugin._runner)
        await plugin.add_peer("s1", Member(agent_id="a", host_ip="10.0.0.2"))
        await plugin.del_peer("s1", Member(agent_id="a", host_ip="10.0.0.2"))
        assert runner.calls == []

    async def test_teardown_deletes_the_bridge(self, plugin: BridgeNetworkPlugin) -> None:
        await plugin.attach_endpoint(cast(Any, {}), cast(Any, {}), meta=_meta("s1"))
        runner = cast(_Runner, plugin._runner)
        runner.calls.clear()
        await plugin.teardown_session_network("s1")
        assert any("del" in c for c in runner.calls)

    async def test_teardown_unknown_session_is_noop(self, plugin: BridgeNetworkPlugin) -> None:
        await plugin.teardown_session_network("never-seen")
        assert cast(_Runner, plugin._runner).calls == []
