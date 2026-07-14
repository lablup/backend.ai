"""Container <-> session bookkeeping for deterministic session-network teardown.

A pure (I/O-free) data structure the ContainerdSessionNetwork owns: it records which
kernels of a session are on THIS node so the last one leaving can trigger the session
network's teardown exactly once. Kept separate from the network facade so the lifecycle
bookkeeping is cohesive and unit-testable on its own.

A kernel counts from the moment it *sets the session network up*, not from the moment its
container exists — see `reserve`. The two are far apart (image pull, scratch setup) and the
agent creates kernels concurrently, so counting containers alone would let a session be torn
down while a sibling is still being built on top of it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeardownScope:
    """What to tear down when a session's last kernel on this node is gone."""

    session_id: str


class SessionContainerTracker:
    _kernel_session: dict[str, str]
    _session_containers: dict[str, set[str]]
    # Kernels that have set this node's session network up but have no container yet. They hold the
    # session network open exactly as a running container does: without them, a sibling that dies
    # first ("the last container of the session") tears the data plane, the LOCAL subnet and the
    # etcd membership down under a kernel that is still being created on top of it.
    _session_pending: dict[str, set[str]]

    def __init__(self) -> None:
        self._kernel_session = {}
        self._session_containers = {}
        self._session_pending = {}

    def reserve(self, session_id: str, kernel_id: str) -> None:
        """Claim the session network for a kernel whose container does not exist yet. Idempotent."""
        self._kernel_session[kernel_id] = session_id
        self._session_pending.setdefault(session_id, set()).add(kernel_id)

    def track(self, session_id: str, container_id: str) -> None:
        """The kernel's container now exists: it holds the session as a container, not a claim.

        (In this backend a container's id IS its kernel id, so the claim and the container are the
        same key — there is nothing to correlate.)"""
        self._kernel_session[container_id] = session_id
        self._session_containers.setdefault(session_id, set()).add(container_id)
        if (pending := self._session_pending.get(session_id)) is not None:
            pending.discard(container_id)
            if not pending:
                self._session_pending.pop(session_id, None)

    def release_pending(self, kernel_id: str) -> TeardownScope | None:
        """Drop the claim of a kernel that never got a container; a no-op for one that did.

        A kernel whose creation fails before its container exists never reaches `clean_kernel` (the
        agent registers a kernel only once its container is prepared, and a destroy for one it has
        never heard of returns without queueing a clean), so its claim has to be released where the
        failure is seen. A kernel that DOES have a container is left alone here: its own removal is
        what must decide the session's fate, and releasing the claim early would tear the session
        network down under a container that is still running.
        """
        if kernel_id in self._session_containers.get(self._kernel_session.get(kernel_id, ""), ()):
            return None
        return self.untrack(kernel_id)

    def untrack(self, kernel_id: str) -> TeardownScope | None:
        """Drop a kernel, whether it got as far as a container or not; return its session's
        TeardownScope iff it was that session's last one on this node.

        Kernels whose creation failed before the container existed come through here too (the agent
        cleans every kernel it accepted, and a container's id is its kernel id), so the claim
        `reserve` made is released on both the success and the failure path.
        """
        session_id = self._kernel_session.pop(kernel_id, None)
        if session_id is None:
            return None
        for index in (self._session_containers, self._session_pending):
            if (remaining := index.get(session_id)) is not None:
                remaining.discard(kernel_id)
                if not remaining:
                    index.pop(session_id, None)
        if session_id in self._session_containers or session_id in self._session_pending:
            return None  # other kernels of this session are still live, or still being created
        return TeardownScope(session_id=session_id)
