from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional, cast

import attrs
from raftify import Raft

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


class GlobalTimerKind(enum.StrEnum):
    RAFT = "raft"
    DISTRIBUTED_LOCK = "distributed_lock"


class GlobalTimerContext:
    timer_kind: GlobalTimerKind
    _raft: Optional[Raft] = None

    def __init__(self, timer_kind: GlobalTimerKind) -> None:
        self.timer_kind = timer_kind

    @property
    def raft(self) -> Raft:
        return cast(Raft, self._raft)

    @raft.setter
    def raft(self, rhs: Raft) -> None:
        self._raft = rhs


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

    registry: AgentRegistry
    agent_cache: AgentRPCCache

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager
    global_timer_ctx: GlobalTimerContext
