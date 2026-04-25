"""Shared types for agent RPC v3.

Parallel to ``ai.backend.manager.api.rest.types``: collects the type
aliases and setup-time context dataclasses that both ``AgentRPCRegistry``
(in ``routing.py``) and middleware providers (in ``middlewares/``)
need. Keeping them here lets middleware modules import from ``types``
without pulling in ``routing`` — avoiding cycles and keeping the
routing module focused on the registry classes themselves.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from callosum.rpc import RPCMessage

from ai.backend.common.dto.agent.response import BaseAgentResponseModel

HandlerMethod = Callable[..., Coroutine[None, None, BaseAgentResponseModel]]
"""Bound handler method exposed on the wire.

Domain registries turn a handler-class instance plus a method-getter
``lambda h: h.<method>`` into this shape at bind time.
"""

CallosumHandler = Callable[[RPCMessage], Coroutine[None, None, Any]]

RPCMiddleware = Callable[[CallosumHandler], CallosumHandler]
"""Single-arg handler wrapper — matches the REST ``RouteMiddleware`` shape."""


@dataclass(frozen=True)
class RPCMiddlewareContext:
    """Setup-time context passed to every ``RPCMiddlewareProvider``.

    Carries values that are known when ``bind_to_rpc`` wires an entry —
    i.e., values that do **not** vary per request. Per-request data such
    as ``agent_id`` flow through the ``RPCMessage`` itself, not through
    this context, so the middleware chain can be built once per method.

    Wrapped in a dataclass (rather than passing ``method_name`` alone)
    so new setup-time fields can be added later without breaking every
    existing provider signature.
    """

    method_name: str


RPCMiddlewareProvider = Callable[[RPCMiddlewareContext], RPCMiddleware]
"""Per-method middleware factory.

Called by ``bind_to_rpc`` with a ``RPCMiddlewareContext`` describing the
entry being wired; the returned ``RPCMiddleware`` is applied to that
method's dispatcher. Providers let middlewares that need setup-time
values (method name for metric labels, tracing spans, …) close over
them once per registration.
"""
