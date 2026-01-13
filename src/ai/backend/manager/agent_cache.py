from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import Any

import sqlalchemy as sa
import zmq
from callosum.exceptions import AuthenticationError
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.rpc import Peer, RPCUserError
from sqlalchemy.engine.row import Row

from ai.backend.common import msgpack
from ai.backend.common.auth import ManagerAuthHandler, PublicKey, SecretKey
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from .exceptions import AgentError, RPCError
from .models.agent import agents
from .models.utils import ExtendedAsyncSAEngine, execute_with_retry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
                request_body: dict[str, object] = {
                    "args": args,
                    "kwargs": kwargs,
                }
                if request_id := current_request_id():
                    request_body["request_id"] = request_id
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


class AgentRPCCache:
    _cache: dict[AgentId, tuple[str, PublicKey | None]]

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        manager_public_key: PublicKey,
        manager_secret_key: SecretKey,
        *,
        rpc_keepalive_timeout: int = 60,  # in seconds
    ) -> None:
        self.db = db
        self.manager_public_key = manager_public_key
        self.manager_secret_key = manager_secret_key
        self.rpc_keepalive_timeout = rpc_keepalive_timeout
        self._cache = {}

    def update(
        self,
        agent_id: AgentId,
        agent_addr: str,
        public_key: PublicKey | None,
    ) -> None:
        self._cache[agent_id] = (agent_addr, public_key)

    def discard(self, agent_id: AgentId) -> None:
        self._cache.pop(agent_id, None)

    async def get_rpc_args(self, agent_id: AgentId) -> tuple[str, PublicKey | None]:
        cached_args = self._cache.get(agent_id, None)
        if cached_args:
            return cached_args

        async def _fetch_agent() -> Row[Any] | None:
            async with self.db.begin_readonly() as conn:
                query = (
                    sa.select(agents.c.addr, agents.c.public_key)
                    .select_from(agents)
                    .where(
                        agents.c.id == agent_id,
                    )
                )
                result = await conn.execute(query)
                return result.first()

        agent = await execute_with_retry(_fetch_agent)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")
        return agent.addr, agent.public_key

    @actxmgr
    async def rpc_context(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: float | None = None,
        _order_key: str | None = None,
    ) -> AsyncIterator[PeerInvoker]:
        agent_addr, agent_public_key = await self.get_rpc_args(agent_id)
        keepalive_retry_count = 3
        keepalive_interval = self.rpc_keepalive_timeout // keepalive_retry_count
        if keepalive_interval < 2:
            keepalive_interval = 2
        if agent_public_key:
            auth_handler = ManagerAuthHandler(
                "local",
                agent_public_key,
                self.manager_public_key,
                self.manager_secret_key,
            )
        else:
            auth_handler = None
        log.debug(
            "rpc_context(): calling ag:{} via {}, with agent_public_key:{!r}",
            agent_id,
            agent_addr,
            agent_public_key.decode() if agent_public_key else None,
        )
        peer = PeerInvoker(
            connect=ZeroMQAddress(agent_addr),
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            transport_opts={
                "zsock_opts": {
                    zmq.TCP_KEEPALIVE: 1,
                    zmq.TCP_KEEPALIVE_IDLE: self.rpc_keepalive_timeout,
                    zmq.TCP_KEEPALIVE_INTVL: keepalive_interval,
                    zmq.TCP_KEEPALIVE_CNT: keepalive_retry_count,
                },
            },
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
        )
        try:
            async with asyncio.timeout(invoke_timeout), peer:
                okey_token = peer.call.order_key.set("")
                try:
                    yield peer
                finally:
                    peer.call.order_key.reset(okey_token)
        except RPCUserError as orig_exc:
            raise AgentError(agent_id, orig_exc.name, orig_exc.repr, orig_exc.args) from orig_exc
        except AuthenticationError as orig_exc:
            detail = (
                "Fail to initate RPC connection. "
                "This could be caused by a connection delay or an attempt to connect to an invalid address. "
                f"(repr: {orig_exc!r})."
            )
            raise RPCError(
                agent_id,
                agent_addr,
                detail,
            ) from orig_exc
        except Exception:
            raise
