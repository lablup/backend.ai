"""What the second kernel of a session sees while the first brings the cluster resolver up.

Cluster names resolve through a per-session server whose ``:53`` redirect is installed *after* the
server is bound, and the kernels of one session attach on a node concurrently. So "is the resolver
up?" cannot be answered by the presence of the server: between the two steps there is one that is
bound and unreachable, and a caller that returned there would run its command against a gateway
whose ``:53`` goes nowhere -- or, if the first attempt then failed, against a session with no
resolver at all.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest

from ai.backend.agent.errors.network import ClusterDNSStartError
from ai.backend.agent.network.session_network import SessionNetwork

_SESSION = "s1"


class _Backend:
    """A network backend, as much of one as the resolver's start touches.

    Its redirect is held open so a test can stand exactly in the window the gate has to cover.
    """

    def __init__(self, *, redirect_error: Exception | None = None) -> None:
        self.redirect_error = redirect_error
        self.redirects: list[tuple[str, int]] = []
        self.reached = asyncio.Event()
        self.release = asyncio.Event()

    async def setup_dns_redirect(self, session_id: str, port: int) -> None:
        self.reached.set()
        await self.release.wait()
        if self.redirect_error is not None:
            raise self.redirect_error
        self.redirects.append((session_id, port))


async def _local_subnet(session_id: str) -> str | None:
    return "172.30.1.0/24"  # the LOCAL block the first attach allocated; its gateway is .1


def _network(backend: _Backend) -> SessionNetwork:
    """A SessionNetwork wired to that backend and nothing else real."""
    network = SessionNetwork(
        cast(Any, object()),
        agent_id="i-test",
        host_ip="10.0.0.1",
        cni_runner=cast(Any, None),
        locator=cast(Any, object()),
        backends=cast(Any, {"bridge": backend}),
        privnet_local_subnet=_local_subnet,
        vtep_ip="10.0.0.1",
        configured_dns=("10.0.0.53",),
    )
    # What `ensure_session` leaves behind for a session set up on this node. The resolver only
    # ever reads the coordinator when a query arrives, and none does here.
    network._coordinators[_SESSION] = cast(Any, object())
    network._session_backends[_SESSION] = cast(Any, backend)
    return network


async def _settle() -> None:
    """Let every runnable task reach its next suspension."""
    for _ in range(4):
        await asyncio.sleep(0)


class TestTwoKernelsAttachingAtOnce:
    async def test_the_second_waits_for_the_redirect(self) -> None:
        backend = _Backend()
        network = _network(backend)
        first = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await backend.reached.wait()  # bound, recorded, and NOT yet redirected
        second = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await _settle()
        assert not second.done(), "a kernel passed the gate before :53 was redirected"
        backend.release.set()
        await asyncio.gather(first, second)
        assert backend.redirects == [(_SESSION, network._dns_servers[_SESSION].port)]
        await network._stop_cluster_dns(_SESSION)

    async def test_a_failed_redirect_fails_the_kernel_that_was_waiting_too(self) -> None:
        # The failure mode this guards: the first kernel dies with a named error while the second
        # sails past it, and the session runs on with cluster names that resolve nowhere.
        backend = _Backend(redirect_error=RuntimeError("iptables: Permission denied"))
        network = _network(backend)
        first = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await backend.reached.wait()
        second = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await _settle()
        backend.release.set()
        outcomes = await asyncio.gather(first, second, return_exceptions=True)
        assert [type(outcome) for outcome in outcomes] == [
            ClusterDNSStartError,
            ClusterDNSStartError,
        ], outcomes
        assert _SESSION not in network._dns_servers

    async def test_the_resolver_comes_up_once_for_all_of_them(self) -> None:
        backend = _Backend()
        backend.release.set()
        network = _network(backend)
        await asyncio.gather(*(network.ensure_cluster_dns(_SESSION) for _ in range(3)))
        assert len(backend.redirects) == 1, "each kernel started its own resolver"
        await network._stop_cluster_dns(_SESSION)

    async def test_a_cancelled_start_leaves_nothing_for_the_next_kernel_to_read(self) -> None:
        # The kernel-creation timeout and the agent stopping both arrive here as a cancellation,
        # and `except Exception` did not catch it: the entry stayed for a redirect that never
        # landed, and the next kernel read it as a resolver that was up.
        backend = _Backend()
        network = _network(backend)
        first = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await backend.reached.wait()
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert _SESSION not in network._dns_servers

        backend.release.set()
        await network.ensure_cluster_dns(_SESSION)
        assert backend.redirects == [(_SESSION, network._dns_servers[_SESSION].port)]
        await network._stop_cluster_dns(_SESSION)

    async def test_a_session_this_node_never_set_up_is_a_no_op(self) -> None:
        backend = _Backend()
        network = _network(backend)
        await network.ensure_cluster_dns("not-here")
        assert backend.redirects == []


class TestTheLockIsNotTheSetupLock:
    async def test_bringing_the_resolver_up_under_the_session_lock_does_not_deadlock(self) -> None:
        # `ensure_session` calls `ensure_cluster_dns` while holding the session's setup lock, and
        # an asyncio.Lock is not reentrant -- sharing one would hang every adopted session.
        backend = _Backend()
        backend.release.set()
        network = _network(backend)
        async with network._session_locked(_SESSION):
            await asyncio.wait_for(network.ensure_cluster_dns(_SESSION), timeout=5)
        assert len(backend.redirects) == 1
        await network._stop_cluster_dns(_SESSION)

    async def test_a_teardown_waits_for_a_start_instead_of_crossing_it(self) -> None:
        # `_stop_cluster_dns` pops the entry; running it while a start is midway through writing
        # one leaves a live resolver for a session that is gone.
        backend = _Backend()
        network = _network(backend)
        start = asyncio.create_task(network.ensure_cluster_dns(_SESSION))
        await backend.reached.wait()
        stop = asyncio.create_task(network._stop_cluster_dns(_SESSION))
        await _settle()
        assert not stop.done(), "the teardown cut into a start"
        backend.release.set()
        await asyncio.gather(start, stop)
        assert _SESSION not in network._dns_servers

    async def test_an_attach_arriving_after_the_stop_does_not_revive_it(self) -> None:
        # The lock stops a start and a stop from crossing; it does not stop one that arrives
        # after. Teardown stops the resolver before it drops the coordinator, and a kernel
        # attaching in that window used to bring the resolver and its :53 redirect back.
        backend = _Backend()
        backend.release.set()
        network = _network(backend)
        await network.ensure_cluster_dns(_SESSION)
        await network._stop_cluster_dns(_SESSION)
        backend.redirects.clear()

        network._tearing_down.add(_SESSION)
        await network.ensure_cluster_dns(_SESSION)

        assert backend.redirects == [], "a late attach restarted a torn-down session's resolver"
        assert _SESSION not in network._dns_servers

    async def test_the_lock_dict_shrinks_back_to_empty(self) -> None:
        backend = _Backend()
        backend.release.set()
        network = _network(backend)
        await network.ensure_cluster_dns(_SESSION)
        assert network._dns_locks == {} and network._dns_lock_users == {}
        await network._stop_cluster_dns(_SESSION)
