"""Pairing the cluster-network driver against the agent backends that can serve it.

The failure this prevents is silent, which is why it is worth a test: 'overlay' (Docker Swarm) is
the DEFAULT inter-container driver, and a containerd agent cannot speak it. Handed one anyway, the
agent falls back to a node-local bridge, so a multi-node session comes up with kernels that cannot
reach each other — and nothing anywhere says so.
"""

from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch
from ai.backend.manager.network.pairing import require_members_can_serve_driver


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
    async def test_a_docker_agent_is_refused(self) -> None:
        etcd = FakeEtcd({"agent-1": "docker"})
        with pytest.raises(NetworkBackendMismatch, match="cannot serve"):
            await require_members_can_serve_driver(cast(AsyncEtcd, etcd), "cni", ["agent-1"])

    async def test_a_containerd_agent_is_accepted(self) -> None:
        etcd = FakeEtcd({"agent-1": "containerd"})
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
        assert "cni" in message  # the fix: pair containerd with the cni driver
