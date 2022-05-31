from __future__ import annotations

from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import EventDispatcher, EventProducer
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.types import RedisConnectionInfo

    from ..models.storage import StorageSessionManager
    from ..models.utils import ExtendedAsyncSAEngine
    from ..idle import IdleCheckerHost
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
    from ..config import LocalConfig, SharedConfig
    from ..types import DistributedLockFactory
    from .types import CORSOptions


class BaseContext:
    pass


@attr.s(slots=True, auto_attribs=True, init=False)
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
    shared_config: SharedConfig
    local_config: LocalConfig
    cors_options: CORSOptions

    webapp_plugin_ctx: WebappPluginContext
    idle_checker_host: IdleCheckerHost
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext

    registry: AgentRegistry

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager
