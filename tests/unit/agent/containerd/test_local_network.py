"""The single-node cluster network is a deliberate no-op on this backend.

The Docker backend answers ``create_local_network`` by creating a real ``bridge`` network labelled
``ai.backend.cluster-network`` and tearing it down again on destroy. Under BEP-1062 the intra-node
path is already carried by the session's own LOCAL/overlay bridges, so the containerd backend
answers the same calls with nothing at all.

That divergence from the reference backend lived only in a code comment. These tests pin it: the
calls must stay harmless and idempotent, and they must not reach the session network — so that
implementing the standing TODO becomes a deliberate change to this file rather than a silent one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from ai.backend.agent.containerd.agent import ContainerdAgent


class _ExplodingSessionNetwork:
    """Any attribute touched here means the no-op has started doing network work."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(
            f"the local-network no-op must not reach the session network (touched {name!r})"
        )


def _agent() -> ContainerdAgent:
    agent = ContainerdAgent.__new__(ContainerdAgent)
    agent._session_network = cast(Any, _ExplodingSessionNetwork())
    return agent


class TestLocalNetworkIsANoOp:
    async def test_create_does_nothing_and_does_not_raise(self, tmp_path: Path) -> None:
        before = sorted(tmp_path.rglob("*"))

        await _agent().create_local_network("bai-singlenode-abc")

        assert sorted(tmp_path.rglob("*")) == before

    async def test_destroying_a_network_that_was_never_created_does_not_raise(self) -> None:
        """The manager tears down unconditionally. Docker's version swallows a 404 for the same
        reason; here there is nothing to miss in the first place."""
        await _agent().destroy_local_network("bai-singlenode-never-made")

    async def test_both_calls_are_idempotent(self) -> None:
        agent = _agent()

        await agent.create_local_network("bai-singlenode-abc")
        await agent.create_local_network("bai-singlenode-abc")
        await agent.destroy_local_network("bai-singlenode-abc")
        await agent.destroy_local_network("bai-singlenode-abc")
