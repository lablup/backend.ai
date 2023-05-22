from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, ClassVar, Coroutine, Mapping, cast

from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.ordering import ExitOrderedAsyncScheduler
from callosum.rpc import Peer, RPCMessage

from ai.backend.common import config, msgpack
from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events import EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import EtcdRedisConfig, aobject

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class RPCFunctionRegistry:
    functions: set[str]

    def __init__(self) -> None:
        self.functions = set()

    def __call__(
        self,
        meth: Callable[..., Coroutine[None, None, Any]],
    ) -> Callable[[DataStoreRPCServer, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        async def _inner(self_: DataStoreRPCServer, request: RPCMessage) -> Any:
            try:
                if request.body is None:
                    return await meth(self_)
                else:
                    return await meth(
                        self_,
                        *request.body["args"],
                        **request.body["kwargs"],
                    )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                raise
            # except ResourceError:
            #     # This is an expected scenario.
            #     raise
            except Exception:
                log.exception("unexpected error")
                # await self_.error_monitor.capture_exception()
                raise

        self.functions.add(meth.__name__)
        return _inner


class DataStoreRPCServer(aobject):
    rpc_function: ClassVar[RPCFunctionRegistry] = RPCFunctionRegistry()

    loop: asyncio.AbstractEventLoop
    rpc_server: Peer
    rpc_addr: str
    datastore_addr: str
    background_task_manager: BackgroundTaskManager | None

    def __init__(
        self,
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
    ) -> None:
        self.loop = asyncio.get_running_loop()
        self.etcd = etcd
        self.local_config = local_config
        self.background_task_manager = None

    async def __ainit__(self) -> None:
        # Start serving requests.
        await self.read_datastore_config()

        rpc_addr = self.local_config["datastore"]["rpc-listen-addr"]
        self.rpc_server = Peer(
            bind=ZeroMQAddress(f"tcp://{rpc_addr}"),
            transport=ZeroMQRPCTransport,
            scheduler=ExitOrderedAsyncScheduler(),
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
            debug_rpc=self.local_config["debug"]["enabled"],
        )
        for func_name in self.rpc_function.functions:
            self.rpc_server.handle_function(func_name, getattr(self, func_name))
        log.info("started handling RPC requests at {}", rpc_addr)

        await self.etcd.put("ip", rpc_addr.host, scope=ConfigScopes.NODE)

    async def read_datastore_config(self):
        # Fill up Redis configs from etcd.
        self.local_config["redis"] = config.redis_config_iv.check(
            await self.etcd.get_prefix("config/redis"),
        )
        log.info("configured redis_addr: {0}", self.local_config["redis"]["addr"])

    async def init_background_task_manager(self):
        event_producer = await EventProducer.new(
            cast(EtcdRedisConfig, self.local_config["redis"]),
            db=4,  # Identical to manager's REDIS_STREAM_DB
        )
        self.background_task_manager = BackgroundTaskManager(event_producer)

    async def __aenter__(self) -> None:
        await self.rpc_server.__aenter__()

    async def __aexit__(self, *exc_info) -> None:
        # Stop receiving further requests.
        await self.rpc_server.__aexit__(*exc_info)
