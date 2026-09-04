"""What a restarted agent does before it trusts anything, and what it admits it could not do.

Every field the session network holds is process memory, while the resources they name -- bridges,
veths, IPAM leases, MASQ rules, etcd members -- outlive the process. So the order matters: bring
the surviving tunnels DOWN first, because at that point no session metadata is trusted or even
readable and an open tunnel is carrying traffic nobody can account for; and whatever could not be
done has to reach readiness, or the node keeps taking overlay work it cannot serve.

These exercise the methods through the real class, on an object built with the constructor's own
defaults, so a signature change breaks them rather than passing over a stub.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from ai.backend.agent.errors.network import OverlayEncryptionUnavailable
from ai.backend.agent.network.session_network import SessionNetwork
from ai.backend.common.network.types import NetworkBackendKind, SessionNetMeta


class _Backend:
    """A network backend, as much of one as recovery touches."""

    def __init__(
        self, *, preflight_error: Exception | None = None, still_up: frozenset[str] = frozenset()
    ) -> None:
        self.preflight_error = preflight_error
        self.still_up = still_up
        self.preflight_calls = 0
        self.retry_calls = 0

    async def prepare_recovery(self) -> None:
        self.preflight_calls += 1
        if self.preflight_error is not None:
            raise self.preflight_error

    async def retry_fail_close(self) -> frozenset[str]:
        self.retry_calls += 1
        return self.still_up


def _network(**backends: _Backend) -> SessionNetwork:
    """A SessionNetwork whose only real collaborators are the backends under test."""
    return SessionNetwork(
        cast(Any, object()),
        agent_id="i-test",
        host_ip="10.0.0.1",
        cni_runner=cast(Any, None),
        locator=cast(Any, object()),
        backends=cast(Any, backends),
        # The constructor insists on exactly one source for node-local subnets; recovery does not
        # reach it, but leaving it out would be testing the constructor's guard instead.
        privnet_local_subnet=_no_local_subnet,
        vtep_ip="10.0.0.1",
    )


async def _no_local_subnet(session_id: str) -> str | None:
    return None


class TestFailCloseComesFirst:
    async def test_a_failed_preflight_is_reported_as_a_readiness_problem(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("baivx4096 would not go down"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()  # the container listing has no real collaborator
        assert "vxlan" in network.recovery_problems()
        assert "would not go down" in network.recovery_problems()["vxlan"]

    async def test_the_preflight_runs_before_anything_is_read(self) -> None:
        # `recover` goes on to list containers, which fails here. The preflight must already have
        # happened: an open tunnel is carrying traffic while the metadata is still untrusted.
        backend = _Backend()
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        assert backend.preflight_calls == 1


class TestRetryIsNotTheWholePreflightAgain:
    """`prepare_recovery` brings down EVERY tunnel the backend owns and prunes every claim, which
    is right exactly once. Running it again on a timer would take down the sessions that recovered
    in between, drop their claims, and not reopen them."""

    async def test_the_retry_closes_only_what_is_still_open(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        backend.preflight_calls = 0

        await network.retry_recovery_fail_close()
        assert backend.retry_calls == 1
        assert backend.preflight_calls == 0, (
            "the retry re-ran the whole preflight; on a live node that brings down every tunnel"
            " that recovered in between and does not reopen them"
        )

    async def test_the_problem_clears_once_the_device_finally_closes(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        assert await network.retry_recovery_fail_close() == {}
        assert network.recovery_problems() == {}

    async def test_a_device_that_is_still_up_keeps_the_problem(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"), still_up=frozenset({"baivx4096"}))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        remaining = await network.retry_recovery_fail_close()
        assert "baivx4096" in remaining["vxlan"]


class TestRecoveryFailuresReachReadiness:
    """A node that could not recover holds state it can neither converge nor tear down. Saying
    nothing lets it keep accepting overlay sessions."""

    async def test_a_failed_recovery_is_recorded(self) -> None:
        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        assert network.recovery_problems()["session:recovery"] == "containerd was unreachable"

    async def test_a_healthy_node_reports_nothing(self) -> None:
        network = _network(vxlan=_Backend())
        assert network.recovery_problems() == {}


class TestRecoveryIsRetriedNotJustReported:
    """A transient container-runtime or metadata error used to leave a session unmanaged -- and
    the node unable to take overlay work -- until the process restarted, because nothing ever came
    back to it."""

    async def test_a_whole_failed_recovery_is_attempted_again(self) -> None:
        backend = _Backend()
        network = _network(vxlan=backend)
        network.mark_recovery_failed("containerd was unreachable")
        try:
            await network.retry_recovery_fail_close()
        except Exception:
            pass  # the container source is still not real here; the point is that it TRIED
        assert backend.preflight_calls >= 1, "the retry did not re-attempt recovery at all"

    async def test_the_problem_stays_until_recovery_actually_succeeds(self) -> None:
        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        try:
            await network.retry_recovery_fail_close()
        except Exception:
            pass
        assert "session:recovery" in network.recovery_problems()

    async def test_a_node_mid_recovery_refuses_a_new_overlay_session(self) -> None:
        # Readiness tells the manager, but a request decided before it read the new capabilities
        # still arrives here, and would build a new VXLAN beside state this node can neither
        # converge nor tear down.

        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.VXLAN,
            subnet="10.128.0.0/24",
            vni=4096,
            mtu=1450,
        )
        with pytest.raises(OverlayEncryptionUnavailable):
            network._refuse_while_unrecovered(meta)

    async def test_a_node_local_session_is_not_refused(self) -> None:
        # A bridge session shares nothing with the unrecovered overlay state.

        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.BRIDGE,
            subnet="172.30.0.0/26",
            vni=None,
            mtu=1500,
        )
        network._refuse_while_unrecovered(meta)  # must not raise

    async def test_a_recovered_node_accepts_again(self) -> None:
        network = _network(vxlan=_Backend())
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.VXLAN,
            subnet="10.128.0.0/24",
            vni=4096,
            mtu=1450,
        )
        network._refuse_while_unrecovered(meta)  # must not raise
