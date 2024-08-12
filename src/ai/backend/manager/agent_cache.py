from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import AsyncIterator, Callable, Optional

import sqlalchemy as sa
import zmq
from callosum.exceptions import AuthenticationError
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.rpc import Peer, RPCUserError
from sqlalchemy.engine.row import Row

from ai.backend.common import msgpack
from ai.backend.common.auth import ManagerAuthHandler, PublicKey, SecretKey
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId

from .exceptions import AgentError, RPCError
from .models.agent import agents
from .models.utils import ExtendedAsyncSAEngine, execute_with_retry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PeerInvoker(Peer):
    class _CallStub:
        _cached_funcs: dict[str, Callable]
        order_key: ContextVar[Optional[str]]

        def __init__(self, peer: Peer):
            self._cached_funcs = {}
            self.peer = peer
            self.order_key = ContextVar("order_key", default=None)

        def __getattr__(self, name: str):
            if f := self._cached_funcs.get(name, None):
                return f
            else:

                async def _wrapped(*args, **kwargs):
                    request_body = {
                        "args": args,
                        "kwargs": kwargs,
                    }
                    self.peer.last_used = time.monotonic()
                    ret = await self.peer.invoke(name, request_body, order_key=self.order_key.get())
                    self.peer.last_used = time.monotonic()
                    return ret

                self._cached_funcs[name] = _wrapped
                return _wrapped

    call: _CallStub
    last_used: float

    def __init__(self, *args, **kwargs) -> None:
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
        public_key: Optional[PublicKey],
    ) -> None:
        self._cache[agent_id] = (agent_addr, public_key)

    def discard(self, agent_id: AgentId) -> None:
        self._cache.pop(agent_id, None)

    async def get_rpc_args(self, agent_id: AgentId) -> tuple[str, PublicKey | None]:
        cached_args = self._cache.get(agent_id, None)
        if cached_args:
            return cached_args

        async def _fetch_agent() -> Row:
            async with self.db.begin_readonly() as conn:
                query = (
                    sa.select([agents.c.addr, agents.c.public_key])
                    .select_from(agents)
                    .where(
                        agents.c.id == agent_id,
                    )
                )
                result = await conn.execute(query)
                return result.first()

        agent = await execute_with_retry(_fetch_agent)
        return agent["addr"], agent["public_key"]

    @actxmgr
    async def rpc_context(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
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
            raise AgentError(agent_id, orig_exc.name, orig_exc.repr, orig_exc.args)
        except AuthenticationError as orig_exc:
            detail = (
                "Fail to initate RPC connection. "
                "This could be caused by a connection delay or an attempt to connect to an invalid address. "
                f"(repr: {repr(orig_exc)})."
            )
            raise RPCError(
                agent_id,
                agent_addr,
                detail,
            )
        except Exception:
            raise
