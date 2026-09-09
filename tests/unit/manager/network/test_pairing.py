"""Pairing the cluster-network driver against the agent backends that can serve it.

The failure this prevents is silent, which is why it is worth a test: 'overlay' (Docker Swarm) is
the DEFAULT inter-container driver, and a containerd agent cannot speak it. Handed one anyway, the
agent falls back to a node-local bridge, so a multi-node session comes up with kernels that cannot
reach each other — and nothing anywhere says so.
"""

import json
from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch
from ai.backend.manager.network.pairing import (
    require_members_can_serve_driver,
    require_members_overlay_ready,
    resolve_driver_for_agents,
)


class FakeEtcd:
    """Serves the backend each agent published at startup."""

    def __init__(self, backends: dict[str, str]) -> None:
        self._store = {agent_backend_key(a): b for a, b in backends.items()}

    async def get(self, key: str, *, scope: Any = None) -> str | None:
        return self._store.get(key)


class TestOverlayDriver:
    async def test_a_containerd_agent_is_refused(self) -> None:
        # The default driver + a containerd agent. This is the pairing that used to come up
        # silently broken.
        etcd = FakeEtcd({"agent-1": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="cannot serve"):
            await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "overlay", ["agent-1"])

    async def test_a_docker_agent_is_accepted(self) -> None:
        etcd = FakeEtcd({"agent-1": "docker"})
        await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "overlay", ["agent-1"])

    async def test_one_bad_member_in_a_mixed_cluster_is_enough(self) -> None:
        # A uniform fabric is the whole point: one containerd agent among docker ones still
        # leaves its kernels stranded.
        etcd = FakeEtcd({"a": "docker", "b": "docker", "c": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="'c'"):
            await require_members_can_serve_driver(
                cast(AsyncEtcd, etcd), "overlay", ["a", "b", "c"]
            )


class TestCniDriver:
    async def test_a_docker_agent_is_accepted(self) -> None:
        etcd = FakeEtcd({"agent-1": "docker"})
        await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "cni", ["agent-1"])

    async def test_a_containerd_agent_is_refused_until_implemented(self) -> None:
        etcd = FakeEtcd({"agent-1": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="cannot serve"):
            await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "cni", ["agent-1"])


class TestUnknownBackends:
    async def test_an_agent_that_has_not_published_is_allowed(self) -> None:
        # Refusing on absence would take out every deployment whose agents predate the publish
        # path the moment this shipped. Unknown is allowed, on purpose.
        etcd = FakeEtcd({})
        await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "overlay", ["agent-1"])

    async def test_a_driver_we_do_not_know_is_not_policed(self) -> None:
        etcd = FakeEtcd({"agent-1": "containerd"})
        await require_members_can_serve_driver(
            cast(AsyncEtcd, etcd), "some-third-party-driver", ["agent-1"]
        )


class TestTheErrorSaysWhatToDo:
    async def test_it_names_the_agent_the_backend_and_the_fix(self) -> None:
        etcd = FakeEtcd({"agent-7": "containerd"})
        with pytest.raises(NetworkBackendMismatch) as excinfo:
            await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "overlay", ["agent-7"])
        message = str(excinfo.value)
        assert "agent-7" in message
        assert "containerd" in message
        assert "overlay" in message
        assert "implemented by that agent backend" in message


class TestTheDriverFollowsTheAgentsBackend:
    """Picking the container runtime IS the choice. The network driver that goes with it is not a
    second, independent decision the operator should also have to get right — and getting it wrong
    used to produce a session whose kernels silently could not reach each other.
    """

    async def test_unsupported_backend_does_not_get_an_unimplemented_driver(self) -> None:
        etcd = FakeEtcd({"a": "containerd", "b": "containerd"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a", "b"], configured_driver="overlay"
        )
        assert driver == "overlay"

    async def test_docker_agents_get_overlay(self) -> None:
        etcd = FakeEtcd({"a": "docker"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay"
        )
        assert driver == "overlay"

    async def test_docker_agents_get_cni_when_it_was_configured(self) -> None:
        # Docker is the one backend that can serve either, so the operator's choice stands. It has
        # to be asked for by name: an existing Swarm deployment upgrading into this must not have
        # its fabric swapped underneath it.
        etcd = FakeEtcd({"a": "docker"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="cni"
        )
        assert driver == "cni"

    async def test_docker_agents_still_default_to_overlay(self) -> None:
        etcd = FakeEtcd({"a": "docker"})
        for configured in (None, "overlay"):
            driver = await resolve_driver_for_agents(
                cast(AsyncEtcd, etcd), ["a"], configured_driver=configured
            )
            assert driver == "overlay", configured

    async def test_an_unsupported_backend_keeps_configured_driver_for_explicit_rejection(
        self,
    ) -> None:
        etcd = FakeEtcd({"a": "containerd"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay"
        )
        assert driver == "overlay"

    async def test_unpublished_backends_fall_back_to_the_configured_driver(self) -> None:
        # An older agent that does not publish must not be stranded: keep doing what the operator
        # configured.
        etcd = FakeEtcd({})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay"
        )
        assert driver == "overlay"

    async def test_a_mixed_cluster_is_refused(self) -> None:
        # No driver spans both fabrics, so there is nothing to auto-select.
        etcd = FakeEtcd({"a": "docker", "b": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="different container runtimes"):
            await resolve_driver_for_agents(
                cast(AsyncEtcd, etcd), ["a", "b"], configured_driver="overlay"
            )


class _CapsEtcd:
    """Serves whatever a test puts in ``store``, for the capability records."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str, *, scope: Any = None) -> str | None:
        return self.store.get(key)


class TestOverlayReadinessGate:
    """The node already knows it cannot serve the backend -- it probes at startup and publishes
    the answer. Without this the answer went nowhere: the session was scheduled anyway and failed
    on that one node at create time."""

    async def test_a_node_that_dropped_vxlan_is_refused(self) -> None:
        etcd = _CapsEtcd()
        etcd.store["network/agent/a1/caps"] = json.dumps({
            "tunnel_offload": False,
            "backends": [],
            "readiness": ["iptables has no `u32` match (xt_u32)."],
        })
        with pytest.raises(NetworkBackendMismatch) as excinfo:
            await require_members_overlay_ready(cast(AsyncEtcd, etcd), ["a1"])
        assert "xt_u32" in str(excinfo.value)

    async def test_a_ready_node_passes(self) -> None:
        etcd = _CapsEtcd()
        etcd.store["network/agent/a1/caps"] = json.dumps({
            "tunnel_offload": False,
            "backends": ["vxlan"],
            "readiness": [],
        })
        await require_members_overlay_ready(cast(AsyncEtcd, etcd), ["a1"])

    async def test_a_node_that_published_nothing_is_allowed(self) -> None:
        # Refusing on absence would take out every deployment whose agents predate the probe.
        await require_members_overlay_ready(cast(AsyncEtcd, _CapsEtcd()), ["a1"])

    async def test_an_unreadable_record_is_not_evidence(self) -> None:
        etcd = _CapsEtcd()
        etcd.store["network/agent/a1/caps"] = "not json"
        await require_members_overlay_ready(cast(AsyncEtcd, etcd), ["a1"])
