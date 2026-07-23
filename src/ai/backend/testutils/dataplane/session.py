"""Creating and destroying real sessions, for scenarios that need one.

Sessions are driven through the manager's v2 client SDK rather than the `./bai` CLI. The CLI
resolves its credentials from ``Path.home() / ".backend.ai"`` with no override, so driving it would
mean either overwriting the developer's own config or fighting `HOME` — and it costs a subprocess
per call besides. `BackendAIClientRegistry` takes the endpoint and keypair as arguments, which is
the same thing `tests/integration` does.

**Use a keypair reserved for the suite.** Concurrent sessions are capped per keypair (5 by
default), so sharing the developer's keypair means their running sessions decide whether the suite
can start. That is not a hypothetical: it is how the first live run failed.

Every wait is bounded and reports what the session's status actually was when the bound expired.
A scenario that hangs waiting for RUNNING tells you nothing; one that says "still CREATING after
180s" points straight at the agent.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.request import (
    EnqueueSessionInput,
    TerminateSessionsInput,
)
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    CreateSessionTypeEnum,
)

RUNNING = "RUNNING"
TERMINATED = "TERMINATED"

# Statuses a session cannot leave. A wait stops at one of these even when it is not what was
# asked for — a session that went to CANCELLED while we waited for RUNNING must fail at once, not
# at the deadline.
#
# RUNNING is deliberately NOT here. It is a resting state, not a final one: a running session is
# exactly what `destroy` waits on its way out of, and treating it as final made every teardown
# fail the moment it was asked to wait for TERMINATED.
_FINAL = frozenset({TERMINATED, "CANCELLED", "ERROR"})


class SessionWaitTimeout(RuntimeError):
    """A session did not reach the expected status within the bound."""


class SessionWentWrong(RuntimeError):
    """A session reached a terminal status other than the expected one."""


@dataclass(frozen=True)
class SessionSpec:
    """The minimum a data-plane scenario needs to describe a session.

    Deliberately not a passthrough of `EnqueueSessionInput`: a scenario should say "two kernels on
    one node" and not have to know which of the manager's forty fields express that.
    """

    image_id: UUID
    project_id: UUID
    cpu: str = "1"
    mem: str = "2147483648"
    cluster_size: int = 1
    cluster_mode: ClusterModeEnum = ClusterModeEnum.SINGLE_NODE
    """SINGLE_NODE places every kernel on one agent; MULTI_NODE spreads them."""

    def to_enqueue_input(self, name: str) -> EnqueueSessionInput:
        """Build the manager's own request model, never a hand-written dict.

        Two reasons, and the second is the one that bites. The client serializes with
        ``request.model_dump()``, so a mapping fails at runtime rather than at the type checker.
        And a scenario that hand-wrote this payload would drift from what the manager actually
        accepts, which produces the worst possible outcome for a test suite: green here, broken in
        production. Same rule as the etcd records the RPC-driven scenarios write.
        """
        return EnqueueSessionInput(
            session_name=name,
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=self.image_id,
            project_id=self.project_id,
            resource_entries=[
                ResourceSlotEntryInput(resource_type="cpu", quantity=self.cpu),
                ResourceSlotEntryInput(resource_type="mem", quantity=self.mem),
            ],
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
        )


@dataclass
class SessionHandle:
    session_id: UUID
    name: str
    kernel_ids: tuple[str, ...] = field(default_factory=tuple)


class SessionApi(Protocol):
    """The slice of the client SDK this driver uses.

    Narrow on purpose: it is what lets the driver's own tests run without a manager. The parameter
    names match `SessionClient`'s exactly — a Protocol compares them, so `request`/`session_id`
    are part of the contract, not decoration.
    """

    async def enqueue(self, request: EnqueueSessionInput) -> Any: ...
    async def get(self, session_id: UUID) -> Any: ...
    async def terminate(self, request: TerminateSessionsInput) -> Any: ...


def _status_of(session: Any) -> str:
    """Pull the status out of a `SessionNode`, tolerating both the model and a plain mapping.

    The REST payload nests it under ``lifecycle``; a mapping is what the driver's tests feed in.
    """
    lifecycle = getattr(session, "lifecycle", None)
    if lifecycle is None and isinstance(session, dict):
        lifecycle = session.get("lifecycle")
    if lifecycle is None:
        raise SessionWentWrong(f"session payload has no lifecycle: {session!r}")
    status = getattr(lifecycle, "status", None)
    if status is None and isinstance(lifecycle, dict):
        status = lifecycle.get("status")
    if status is None:
        raise SessionWentWrong(f"session lifecycle has no status: {lifecycle!r}")
    return str(status)


class SessionDriver:
    _api: SessionApi
    _interval: float
    _max_wait: float

    def __init__(self, api: SessionApi, *, interval: float = 2.0, max_wait: float = 300.0) -> None:
        self._api = api
        self._interval = interval
        self._max_wait = max_wait

    async def status(self, session_id: UUID) -> str:
        return _status_of(await self._api.get(session_id))

    async def wait_until(
        self,
        session_id: UUID,
        accept: frozenset[str],
        *,
        max_wait: float | None = None,
    ) -> str:
        """Poll until the status is in `accept`; fail early on a final status outside it.

        `accept` is a set rather than one value because the acceptable end of a teardown is
        genuinely more than one status: a session torn down before it ever ran ends CANCELLED, not
        TERMINATED, and that is a success for the caller's purposes.
        """
        bound = self._max_wait if max_wait is None else max_wait
        deadline = time.monotonic() + bound
        while True:
            last = await self.status(session_id)
            if last in accept:
                return last
            if last in _FINAL:
                raise SessionWentWrong(
                    f"session {session_id} reached {last} while waiting for "
                    f"{'/'.join(sorted(accept))}"
                )
            if time.monotonic() >= deadline:
                raise SessionWaitTimeout(
                    f"session {session_id} was still {last} after {bound}s "
                    f"(waiting for {'/'.join(sorted(accept))})"
                )
            await asyncio.sleep(self._interval)

    async def create(self, spec: SessionSpec, name: str) -> SessionHandle:
        payload = await self._api.enqueue(spec.to_enqueue_input(name))
        session_id = _session_id_of(payload)
        await self.wait_until(session_id, frozenset({RUNNING}))
        return SessionHandle(session_id=session_id, name=name)

    async def destroy(self, session_id: UUID, *, wait: bool = True) -> None:
        await self._api.terminate(TerminateSessionsInput(session_ids=[session_id]))
        if wait:
            await self.wait_until(session_id, frozenset({TERMINATED, "CANCELLED"}))

    @asynccontextmanager
    async def session(self, spec: SessionSpec, name: str) -> AsyncIterator[SessionHandle]:
        """A session that is destroyed even when the scenario fails.

        The teardown is unconditional: a scenario that raised mid-way is exactly when leaving a
        session behind would poison every later test's baseline.
        """
        handle = await self.create(spec, name)
        try:
            yield handle
        finally:
            await self.destroy(handle.session_id)


def _session_id_of(payload: Any) -> UUID:
    for attr in ("id", "session_id"):
        value = getattr(payload, attr, None)
        if value is None and isinstance(payload, dict):
            value = payload.get(attr)
        if value is not None:
            return value if isinstance(value, UUID) else UUID(str(value))
    # `enqueue` returns the created session nested under `session` in the REST payload.
    nested = getattr(payload, "session", None)
    if nested is None and isinstance(payload, dict):
        nested = payload.get("session")
    if nested is not None:
        return _session_id_of(nested)
    raise SessionWentWrong(f"enqueue payload carries no session id: {payload!r}")


def unique_name(prefix: str, *, suffix: str) -> str:
    """Session names must be unique per user among active sessions.

    The suffix is the caller's to supply — this module cannot generate one, because a scenario that
    reruns after a crash needs a name that does not collide with the session the crash left behind,
    and only the caller knows whether it wants that.
    """
    return f"{prefix}-{suffix}"[:64]


def kernel_ids_of(session: Any) -> Sequence[str]:
    """Kernel ids of a session, from whichever shape the payload carries them in."""
    kernels = getattr(session, "kernels", None)
    if kernels is None and isinstance(session, dict):
        kernels = session.get("kernels")
    if not kernels:
        return ()
    out: list[str] = []
    for kernel in kernels:
        kid = getattr(kernel, "id", None)
        if kid is None and isinstance(kernel, dict):
            kid = kernel.get("id")
        if kid is not None:
            out.append(str(kid))
    return tuple(out)
