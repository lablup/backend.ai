from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import EventDispatcher, EventProducer
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.types import RedisConnectionInfo

    from ..config import LocalConfig, SharedConfig
    from ..idle import IdleCheckerHost
    from ..models.resource_policy import ConcurrencyTracker
    from ..models.storage import StorageSessionManager
    from ..models.utils import ExtendedAsyncSAEngine
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
    from ..types import DistributedLockFactory
    from .types import CORSOptions


class BaseContext:
    pass


@attrs.define(slots=True, auto_attribs=True, init=False)
class ConfigContext:
    pidx: int
    local_config: LocalConfig
    shared_config: SharedConfig
    cors_options: CORSOptions


@attrs.define(slots=True, auto_attribs=True, init=False)
class HalfstackContext:
    db: ExtendedAsyncSAEngine
    redis_live: RedisConnectionInfo
    redis_stat: RedisConnectionInfo
    redis_image: RedisConnectionInfo
    redis_stream: RedisConnectionInfo
    redis_lock: RedisConnectionInfo


@attrs.define(slots=True, auto_attribs=True, init=False)
class GlobalObjectContext:
    distributed_lock_factory: DistributedLockFactory
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    idle_checker_host: IdleCheckerHost
    storage_manager: StorageSessionManager
    background_task_manager: BackgroundTaskManager
    concurrency_tracker: ConcurrencyTracker
    webapp_plugin_ctx: WebappPluginContext
    hook_plugin_ctx: HookPluginContext
    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext(BaseContext):
    c: ConfigContext
    h: HalfstackContext
    g: GlobalObjectContext
    registry: AgentRegistry
