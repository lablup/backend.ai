from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

import attrs

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import EventDispatcher, EventProducer
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.types import RedisConnectionInfo, ResourceSlot

    from ..config import LocalConfig, SharedConfig
    from ..idle import IdleCheckerHost
    from ..models.storage import StorageSessionManager
    from ..models.user import UserRole, UserStatus
    from ..models.utils import ExtendedAsyncSAEngine
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
    from ..types import DistributedLockFactory
    from .types import CORSOptions


class BaseContext:
    pass


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
    cors_options: CORSOptions

    webapp_plugin_ctx: WebappPluginContext
    idle_checker_host: IdleCheckerHost
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext

    registry: AgentRegistry

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager


@attrs.define(slots=True, init=False)
class AuthData:
    # common
    user_id: UUID = attrs.field()
    access_key: UUID = attrs.field()

    # keypairs
    is_active: bool = attrs.field()
    last_used: datetime = attrs.field()
    rate_limit: int = attrs.field()

    # keypair_resource_policies
    resource_policy_name: str = attrs.field()
    total_resource_slots: ResourceSlot = attrs.field()
    max_session_lifetime: int = attrs.field()
    max_concurrent_sessions: int = attrs.field()
    max_containers_per_session: int = attrs.field()
    max_vfolder_count: int = attrs.field()
    max_vfolder_size: int = attrs.field()
    idle_timeout: int = attrs.field()

    # users
    user_role: UserRole = attrs.field()
    username: str = attrs.field()
    email: str = attrs.field()
    user_status: UserStatus
    domain_name: str = attrs.field()

    # etc
    group: Optional[Sequence[UUID]] = attrs.field(default=None)
    is_authorized: bool = attrs.field(default=False)
