"""Container <-> session bookkeeping for deterministic session-network teardown.

A pure (I/O-free) data structure the ContainerdSessionNetwork owns: it records which
containers belong to which session on THIS node so the removal of a session's *last*
container can trigger its network teardown exactly once. Kept separate from the network
facade so the lifecycle bookkeeping is cohesive and unit-testable on its own.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeardownScope:
    """What to tear down when a session's last container on this node is removed."""

    session_id: str
    local: bool  # True -> single-node local bridge; False -> overlay coordinator


class SessionContainerTracker:
    _container_session: dict[str, str]
    _session_containers: dict[str, set[str]]
    _local_sessions: set[str]

    def __init__(self) -> None:
        self._container_session = {}
        self._session_containers = {}
        self._local_sessions = set()

    def track(self, session_id: str, container_id: str, *, local: bool = False) -> None:
        self._container_session[container_id] = session_id
        self._session_containers.setdefault(session_id, set()).add(container_id)
        if local:
            self._local_sessions.add(session_id)

    def untrack(self, container_id: str) -> TeardownScope | None:
        """Drop a container; return its session's TeardownScope iff it was the last one
        of that session on this node (else None — other kernels are still live)."""
        session_id = self._container_session.pop(container_id, None)
        if session_id is None:
            return None
        remaining = self._session_containers.get(session_id)
        if remaining is not None:
            remaining.discard(container_id)
            if remaining:
                return None
        self._session_containers.pop(session_id, None)
        local = session_id in self._local_sessions
        self._local_sessions.discard(session_id)
        return TeardownScope(session_id=session_id, local=local)
