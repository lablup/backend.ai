"""Pairing the cluster-network driver against the agent backends that can serve it: a containerd
agent handed the overlay driver silently falls back to a node-local bridge."""

from typing import cast
from unittest.mock import MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch
from ai.backend.manager.network.pairing import (
    require_members_can_serve_driver,
    resolve_driver_for_agents,
)
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin
from ai.backend.testutils.in_memory_etcd import InMemoryEtcd


def _plugin(compatible_backends: frozenset[str] | None) -> AbstractNetworkManagerPlugin:
    """A driver as the pairing sees it: only what it declares it can serve."""
    plugin = MagicMock(spec=AbstractNetworkManagerPlugin)
    plugin.compatible_backends = compatible_backends
    return cast(AbstractNetworkManagerPlugin, plugin)


_DOCKER_ONLY = frozenset({"docker"})
# The two drivers this repo ships, as they declare themselves.
_PLUGINS = {"overlay": _plugin(_DOCKER_ONLY), "cni": _plugin(_DOCKER_ONLY)}


def _etcd_with_backends(backends: dict[str, str]) -> InMemoryEtcd:
    """Serves the backend each agent published at startup."""
    return InMemoryEtcd({agent_backend_key(a): b for a, b in backends.items()})


class TestOverlayDriver:
    async def test_a_containerd_agent_is_refused(self) -> None:
        # The default driver + a containerd agent. This is the pairing that used to come up
        # silently broken.
        etcd = _etcd_with_backends({"agent-1": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="cannot serve"):
            await require_members_can_serve_driver(
                cast(AsyncEtcd, etcd), "overlay", _PLUGINS["overlay"], ["agent-1"]
            )

    async def test_a_docker_agent_is_accepted(self) -> None:
        etcd = _etcd_with_backends({"agent-1": "docker"})
        await require_members_can_serve_driver(
            cast(AsyncEtcd, etcd), "overlay", _PLUGINS["overlay"], ["agent-1"]
        )

    async def test_one_bad_member_in_a_mixed_cluster_is_enough(self) -> None:
        # A uniform fabric is the whole point: one containerd agent among docker ones still
        # leaves its kernels stranded.
        etcd = _etcd_with_backends({"a": "docker", "b": "docker", "c": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="'c'"):
            await require_members_can_serve_driver(
                cast(AsyncEtcd, etcd), "overlay", _PLUGINS["overlay"], ["a", "b", "c"]
            )


class TestCniDriver:
    async def test_a_docker_agent_is_accepted(self) -> None:
        etcd = _etcd_with_backends({"agent-1": "docker"})
        await require_members_can_serve_driver(
            cast(AsyncEtcd, etcd), "cni", _PLUGINS["cni"], ["agent-1"]
        )

    async def test_a_containerd_agent_is_refused_until_implemented(self) -> None:
        etcd = _etcd_with_backends({"agent-1": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="cannot serve"):
            await require_members_can_serve_driver(
                cast(AsyncEtcd, etcd), "cni", _PLUGINS["cni"], ["agent-1"]
            )


class TestUnknownBackends:
    async def test_an_agent_that_has_not_published_is_allowed(self) -> None:
        # Refusing on absence would take out every deployment whose agents predate the publish
        # path the moment this shipped. Unknown is allowed, on purpose.
        etcd = _etcd_with_backends({})
        await require_members_can_serve_driver(
            cast(AsyncEtcd, etcd), "overlay", _PLUGINS["overlay"], ["agent-1"]
        )

    async def test_a_driver_we_do_not_know_is_not_policed(self) -> None:
        etcd = _etcd_with_backends({"agent-1": "containerd"})
        await require_members_can_serve_driver(
            cast(AsyncEtcd, etcd), "some-third-party-driver", _plugin(None), ["agent-1"]
        )


class TestTheErrorSaysWhatToDo:
    async def test_it_names_the_agent_the_backend_and_the_fix(self) -> None:
        etcd = _etcd_with_backends({"agent-7": "containerd"})
        with pytest.raises(NetworkBackendMismatch) as excinfo:
            await require_members_can_serve_driver(
                cast(AsyncEtcd, etcd), "overlay", _PLUGINS["overlay"], ["agent-7"]
            )
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

    async def test_docker_agents_get_cni_when_it_was_configured(self) -> None:
        # Docker is the one backend that can serve either, so the operator's choice stands. It has
        # to be asked for by name: an existing Swarm deployment upgrading into this must not have
        # its fabric swapped underneath it.
        etcd = _etcd_with_backends({"a": "docker"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="cni", plugins=_PLUGINS
        )
        assert driver == "cni"

    async def test_docker_agents_still_default_to_overlay(self) -> None:
        etcd = _etcd_with_backends({"a": "docker"})
        for configured in (None, "overlay"):
            driver = await resolve_driver_for_agents(
                cast(AsyncEtcd, etcd), ["a"], configured_driver=configured, plugins=_PLUGINS
            )
            assert driver == "overlay", configured

    async def test_an_operators_own_driver_is_never_replaced(self) -> None:
        # A driver outside the table is a third-party plugin; main always used it as configured.
        etcd = _etcd_with_backends({"a": "docker"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="weave", plugins=_PLUGINS
        )
        assert driver == "weave"

    async def test_an_unsupported_backend_keeps_configured_driver_for_explicit_rejection(
        self,
    ) -> None:
        etcd = _etcd_with_backends({"a": "containerd"})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay", plugins=_PLUGINS
        )
        assert driver == "overlay"

    async def test_unpublished_backends_fall_back_to_the_configured_driver(self) -> None:
        # A released agent publishes no network keys and must not be stranded: keep doing what the
        # operator configured.
        etcd = _etcd_with_backends({})
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay", plugins=_PLUGINS
        )
        assert driver == "overlay"

    async def test_a_mixed_cluster_is_refused(self) -> None:
        # No driver spans both fabrics, so there is nothing to auto-select.
        etcd = _etcd_with_backends({"a": "docker", "b": "containerd"})
        with pytest.raises(NetworkBackendMismatch, match="different container runtimes"):
            await resolve_driver_for_agents(
                cast(AsyncEtcd, etcd), ["a", "b"], configured_driver="overlay", plugins=_PLUGINS
            )

    async def test_a_driver_that_declares_the_backend_replaces_one_that_cannot_serve_it(
        self,
    ) -> None:
        etcd = _etcd_with_backends({"a": "containerd"})
        plugins = {**_PLUGINS, "cni": _plugin(frozenset({"docker", "containerd"}))}
        driver = await resolve_driver_for_agents(
            cast(AsyncEtcd, etcd), ["a"], configured_driver="overlay", plugins=plugins
        )
        assert driver == "cni"
