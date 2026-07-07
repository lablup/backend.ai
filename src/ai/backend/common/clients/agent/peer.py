"""
Callosum RPC peer wrapper shared by the manager and the agent CLI.

``PeerInvoker`` is a thin subclass of :class:`callosum.rpc.Peer` that exposes a
``.call`` attribute for ergonomic ``peer.call.<method>(...)`` invocation. It has
no manager- or agent-specific dependencies so both the manager's agent client
pool and the agent-side verification CLI construct it identically, guaranteeing
the two exercise the same RPC path.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

from callosum.rpc import Peer


class PeerInvoker(Peer):
    class _CallStub:
        _cached_funcs: dict[str, Callable[..., Any]]
        order_key: ContextVar[str | None]

        def __init__(self, peer: Peer) -> None:
            self._cached_funcs = {}
            self.peer = peer
            self.order_key = ContextVar("order_key", default=None)

        def __getattr__(self, name: str) -> Callable[..., Any]:
            if f := self._cached_funcs.get(name, None):
                return f

            async def _wrapped(*args: Any, **kwargs: Any) -> Any:
                request_body = {
                    "args": args,
                    "kwargs": kwargs,
                }
                self.peer.last_used = time.monotonic()  # type: ignore[attr-defined]
                ret = await self.peer.invoke(name, request_body, order_key=self.order_key.get())
                self.peer.last_used = time.monotonic()  # type: ignore[attr-defined]
                return ret

            self._cached_funcs[name] = _wrapped
            return _wrapped

    call: _CallStub
    last_used: float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.call = self._CallStub(self)
        self.last_used = time.monotonic()
