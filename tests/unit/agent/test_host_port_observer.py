"""
The port pool must not reclaim a port that is live behind a DNAT rule.

A session-networked kernel runs with `NetworkMode: none` and is reached only through the DNAT
rules the agent installs, so Docker publishes nothing for it and `container.ports` is empty. The
observer read only that, counted every one of those live ports as unused, and after
`PORT_USAGE_THRESHOLD` passes released them — the next kernel drew the same port, installed a
second PREROUTING rule, and the older one won, so its traffic landed in the previous session's
container.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from ai.backend.agent.network.port_forward import PortForward
from ai.backend.agent.observer.host_port import PORT_USAGE_THRESHOLD, HostPortObserver


def _agent(*, published: list[PortForward] | None, used_ports: set[int]) -> Any:
    agent = MagicMock()
    agent.enumerate_containers = AsyncMock(return_value=[])  # Docker publishes nothing for these
    agent.port_pool.used_ports = MagicMock(return_value=set(used_ports))
    agent.port_pool.release_many = MagicMock()
    if published is None:
        agent.port_publisher = MagicMock(return_value=None)
    else:
        publisher = MagicMock()
        publisher.list_forwards = AsyncMock(return_value=published)
        agent.port_publisher = MagicMock(return_value=publisher)
    return agent


def _forward(host_port: int) -> PortForward:
    return PortForward(
        container_id="c1",
        host_port=host_port,
        container_ip="172.30.1.2",
        container_port=2000,
    )


async def _observe_until_the_threshold(observer: HostPortObserver) -> None:
    for _ in range(PORT_USAGE_THRESHOLD):
        await observer.observe()


class TestAPublishedPortIsNotUnused:
    async def test_a_dnat_published_port_is_never_released(self) -> None:
        agent = _agent(published=[_forward(30001)], used_ports={30001})
        observer = HostPortObserver(agent)

        await _observe_until_the_threshold(observer)

        agent.port_pool.release_many.assert_not_called()

    async def test_a_port_nothing_holds_is_still_released(self) -> None:
        """The guard must not turn the observer off."""
        agent = _agent(published=[], used_ports={30002})
        observer = HostPortObserver(agent)

        await _observe_until_the_threshold(observer)

        agent.port_pool.release_many.assert_called_once()
        assert set(agent.port_pool.release_many.call_args.args[0]) == {30002}

    async def test_only_the_unpublished_half_is_released(self) -> None:
        agent = _agent(published=[_forward(30001)], used_ports={30001, 30002})
        observer = HostPortObserver(agent)

        await _observe_until_the_threshold(observer)

        assert set(agent.port_pool.release_many.call_args.args[0]) == {30002}

    async def test_a_backend_that_publishes_nothing_is_unaffected(self) -> None:
        """Kubernetes and the dummy backend have no publisher; the observer still works."""
        agent = _agent(published=None, used_ports={30003})
        observer = HostPortObserver(agent)

        await _observe_until_the_threshold(observer)

        assert set(agent.port_pool.release_many.call_args.args[0]) == {30003}

    async def test_a_listing_that_cannot_be_read_does_not_release_on_that_pass(self) -> None:
        """One unreadable pass must not be what reclaims a live port."""
        agent = _agent(published=[], used_ports={30004})
        agent.port_publisher().list_forwards = AsyncMock(side_effect=RuntimeError("iptables"))
        observer = HostPortObserver(agent)

        await observer.observe()  # must not raise

        agent.port_pool.release_many.assert_not_called()
