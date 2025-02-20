from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional, cast

import attrs
from raftify import Raft

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.types import CIStrEnum
from ai.backend.manager.plugin.network import NetworkPluginContext

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import EventDispatcher, EventProducer
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.types import RedisConnectionInfo

    from ..agent_cache import AgentRPCCache
    from ..config import LocalConfig, SharedConfig
    from ..idle import IdleCheckerHost
    from ..models.storage import StorageSessionManager
    from ..models.utils import ExtendedAsyncSAEngine
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
    from ..types import DistributedLockFactory
    from .types import CORSOptions


class BaseContext:
    pass


class KVStoreKind(CIStrEnum):
    RAFT = enum.auto()
    ETCD = enum.auto()


class KVStoreContext:
    kvs_kind: KVStoreKind
    _raft: Optional[Raft] = None

    def __init__(self, kvs_kind: KVStoreKind) -> None:
        self.kvs_kind = kvs_kind

    @property
    def raft(self) -> Raft:
        assert self.kvs_kind == KVStoreKind.RAFT, "Raft is not selected as KVStore kind"
        return cast(Raft, self._raft)

    @raft.setter
    def raft(self, rhs: Raft) -> None:
        self._raft = rhs

    @property
    def etcd(self) -> AsyncEtcd:
        if self.kvs_kind != KVStoreKind.ETCD:
            raise RuntimeError("Etcd is not the selected KV store")
        return cast(AsyncEtcd, self._etcd)

    @etcd.setter
    def etcd(self, rhs: AsyncEtcd) -> None:
        self._etcd = rhs


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext(BaseContext):
    pidx: int
    db: ExtendedAsyncSAEngine
    distributed_lock_factory: DistributedLockFactory
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    redis_live: RedisConnectionInfo
    redis_stat: RedisConnectionInfo
    redis_image: RedisConnectionInfo
    redis_stream: RedisConnectionInfo
    redis_lock: RedisConnectionInfo
    shared_config: SharedConfig
    local_config: LocalConfig
    raft_cluster_config: Optional[LocalConfig]
    cors_options: CORSOptions

    webapp_plugin_ctx: WebappPluginContext
    idle_checker_host: IdleCheckerHost
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext

    registry: AgentRegistry
    agent_cache: AgentRPCCache

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager
    metrics: CommonMetricRegistry
    kvstore_ctx: KVStoreContext

    def __init__(self, *, metrics: CommonMetricRegistry = CommonMetricRegistry(), **kwargs) -> None:
        super().__init__(**kwargs)
        self.metrics = metrics
