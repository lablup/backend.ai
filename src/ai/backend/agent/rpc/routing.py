"""Agent RPC v3 routing.

Hosts the agent-side counterparts to
``ai.backend.manager.api.rest.routing.RouteRegistry`` — but as a **two-
level** hierarchy:

* ``DomainRPCRegistry[THandler]`` owns a single handler class. At bind
  time it is materialised once per agent (via its
  ``handler_factory``) so each handler instance is bound to a specific
  ``AbstractAgent`` through normal constructor injection. Method
  registrations are ``lambda h: h.<method>`` callables that extract the
  bound methods off each handler.
* ``AgentRPCRegistry`` aggregates domain registries and owns the
  cross-cutting concerns (runtime, middlewares, callosum wiring).

Dispatch flow per v3 RPC call:

1. **Parse body** (``_parse_request_body``) — pull ``req`` and
   ``agent_id`` out of the callosum kwargs envelope.
2. **Resolve agent** via the injected runtime; this fixes *which*
   handler instance serves the call.
3. **Extract parameters** via ``extract_rpc_param_value`` based on the
   bound method's signature.
4. **Invoke** the handler and serialise the ``BaseAgentResponseModel``
   result via ``model_dump(mode="json")``.

Cross-cutting concerns (metrics, logging, auth) land as middlewares
**injected** into ``AgentRPCRegistry`` at construction time — the
routing code contains no hard-coded middleware. See
``ai.backend.agent.rpc.middlewares`` for ready-made providers.

Type aliases (``HandlerMethod``, ``RPCMiddleware``, …) and the
``RPCMiddlewareContext`` dataclass live in ``types.py`` so middleware
modules can share them without importing this module.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from callosum.rpc import Peer, RPCMessage

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors import AgentIdNotFoundError
from ai.backend.agent.exception import ResourceError
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter

from .params import extract_rpc_param_value
from .types import (
    CallosumHandler,
    HandlerMethod,
    RPCMiddleware,
    RPCMiddlewareContext,
    RPCMiddlewareProvider,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


THandler = TypeVar("THandler")


class DomainRPCRegistry[THandler]:
    """Per-domain RPC registry, parameterised by its handler class.

    Instances are created via ``AgentRPCRegistry.create_domain`` so that
    the generic parameter ``THandler`` is inferred from the supplied
    ``handler_factory`` — callers then get type-checked
    ``add_method(name, lambda h: h.<method>)`` registrations.

    The registry does not materialise handlers itself; it holds the
    factory and the method getters, and ``AgentRPCRegistry.bind_to_rpc``
    invokes the factory once per agent at startup to produce one handler
    instance per (domain, agent) pair.
    """

    _handler_factory: Callable[[AbstractAgent[Any, Any]], THandler]
    _method_getters: dict[str, Callable[[THandler], HandlerMethod]]

    def __init__(self, handler_factory: Callable[[AbstractAgent[Any, Any]], THandler]) -> None:
        self._handler_factory = handler_factory
        self._method_getters = {}

    def add_method(
        self,
        name: str,
        method_getter: Callable[[THandler], HandlerMethod],
    ) -> None:
        """Register a v3 RPC method by name and a method-getter lambda.

        ``method_getter`` is a ``lambda h: h.<method>`` expression; the
        generic parameter ``THandler`` makes ``h`` type-check as the
        concrete handler class supplied to ``create_domain``, so IDE
        completion and typos on method names are caught statically.
        """
        if name in self._method_getters:
            raise ValueError(f"RPC method already registered in this domain: {name}")
        self._method_getters[name] = method_getter


class AgentRPCRegistry:
    """Top-level registry aggregating per-domain registries.

    The wire envelope every v3 method receives is::

        {"args": [], "kwargs": {"req": <pydantic-dump>, "agent_id": ...}}

    * ``req`` carries the handler's pydantic payload (validated against
      the type declared in the bound handler method's signature).
    * ``agent_id`` selects which per-agent handler instance serves the
      call; ``None`` (or missing) routes to the primary agent.

    The callosum method name itself acts as the dispatch key — there is
    no separate ``method`` field in the body because callosum already
    routes by method name at the transport level.

    Middlewares are supplied as **providers** at construction time so
    cross-cutting concerns like metrics are wired in by the caller (for
    example, ``AgentRPCServer`` injects ``build_metric_middleware``),
    never hard-coded inside the registry.
    """

    _runtime: AgentRuntime
    _domains: list[DomainRPCRegistry[Any]]
    _middleware_providers: list[RPCMiddlewareProvider]

    def __init__(
        self,
        *,
        runtime: AgentRuntime,
        middlewares: Sequence[RPCMiddlewareProvider] = (),
    ) -> None:
        self._runtime = runtime
        self._domains = []
        self._middleware_providers = list(middlewares)

    def create_domain(
        self,
        handler_factory: Callable[[AbstractAgent[Any, Any]], THandler],
    ) -> DomainRPCRegistry[THandler]:
        """Create a new per-domain registry and attach it to this top-level
        registry.

        ``handler_factory`` is called once per agent at ``bind_to_rpc``
        time — **not** per request — producing one handler instance per
        (domain, agent) pair. The returned ``DomainRPCRegistry[THandler]``
        preserves the concrete handler type so subsequent
        ``add_method(name, lambda h: h.<method>)`` calls get type-checked
        against it.
        """
        domain: DomainRPCRegistry[THandler] = DomainRPCRegistry(handler_factory)
        self._domains.append(domain)
        return domain

    def bind_to_rpc(self, rpc_server: Peer) -> None:
        """Wire every registered entry into the callosum RPC server.

        For each domain: invoke ``handler_factory`` once per agent. For
        each ``add_method`` entry: apply the getter lambda to each
        per-agent handler, producing a ``{method_name: {agent_id: bound
        method}}`` dispatch table. Finally wrap one callosum dispatcher
        per method that selects the right handler based on the request's
        ``agent_id`` and applies the middleware chain.
        """
        dispatch_table: dict[str, dict[AgentId, HandlerMethod]] = {}
        for domain in self._domains:
            per_agent_handlers: dict[AgentId, Any] = {
                agent.id: domain._handler_factory(agent) for agent in self._runtime.get_agents()
            }
            for method_name, getter in domain._method_getters.items():
                if method_name in dispatch_table:
                    raise ValueError(f"RPC method '{method_name}' registered in multiple domains")
                dispatch_table[method_name] = {
                    agent_id: getter(handler) for agent_id, handler in per_agent_handlers.items()
                }

        for method_name, per_agent_methods in dispatch_table.items():
            base = self._wrap_dispatcher(per_agent_methods)
            ctx = RPCMiddlewareContext(method_name=method_name)
            middlewares = [provider(ctx) for provider in self._middleware_providers]
            final = self._apply_rpc_middlewares(base, middlewares) if middlewares else base
            rpc_server.handle_function(method_name, final)

    @staticmethod
    def _parse_request_body(request: RPCMessage) -> tuple[Any, AgentId | None]:
        """Split the v3 RPC envelope into (``req``, ``agent_id``).

        The envelope lives on ``request.body["kwargs"]`` because callosum
        serialises keyword arguments there; manager clients invoke the
        RPC with ``await peer.call.some_method(req=..., agent_id=...)``
        so the mapping lines up naturally.
        """
        body = request.body or {}
        kwargs_body = body.get("kwargs") or {}
        if "req" not in kwargs_body:
            raise ValueError("v3 RPC body is missing the 'req' envelope field")
        return kwargs_body["req"], kwargs_body.get("agent_id")

    def _wrap_dispatcher(
        self,
        per_agent_methods: dict[AgentId, HandlerMethod],
    ) -> CallosumHandler:
        """Build the base callosum dispatcher for a single v3 method.

        Mirrors ``_wrap_api_handler`` in the REST layer, with one extra
        step: after parsing the envelope, resolve the agent via the
        runtime (respecting the ``None → primary`` fallback) and pick
        the corresponding pre-bound handler method out of
        ``per_agent_methods``.
        """

        async def _dispatch(request: RPCMessage) -> Any:
            try:
                raw_req, agent_id = self._parse_request_body(request)
                target_agent = self._runtime.get_agent(agent_id)
                method = per_agent_methods[target_agent.id]
                sig = inspect.signature(method, eval_str=True)

                call_kwargs: dict[str, Any] = {}
                for pname, param in sig.parameters.items():
                    if pname == "self":
                        continue
                    call_kwargs[pname] = await extract_rpc_param_value(raw_req, param.annotation)

                res = await method(**call_kwargs)
                return res.model_dump(mode="json")
            except (TimeoutError, asyncio.CancelledError):
                raise
            except (ResourceError, AgentIdNotFoundError):
                # Expected domain errors — let callosum propagate without
                # log spam; the manager-side error mapper surfaces them.
                raise
            except Exception:
                log.exception("v3 RPC handler error")
                raise

        return _dispatch

    @staticmethod
    def _apply_rpc_middlewares(
        handler: CallosumHandler,
        middlewares: Sequence[RPCMiddleware],
    ) -> CallosumHandler:
        """Chain middlewares around a handler (first element outermost).

        Matches ``_apply_route_middlewares`` in the REST layer.
        """
        wrapped: CallosumHandler = handler
        for middleware in reversed(middlewares):
            wrapped = middleware(wrapped)
        return wrapped
