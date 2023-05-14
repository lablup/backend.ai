from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Sequence

import aiotools
from yarl import URL

from ai.backend.common.events import (
    DoScheduleEvent,
    EventDispatcher,
    EventProducer,
    KernelLifecycleEventReason,
)
from ai.backend.common.reconcilation_loop import ReconcilationLoop
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    SessionEnqueueingConfig,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.types import DistributedLockFactory

from .models.session import SessionRow
from .types import UserScope

if TYPE_CHECKING:
    from .config import LocalConfig, SharedConfig
    from .models.scaling_group import ScalingGroupRow
    from .models.utils import ExtendedAsyncSAEngine
    from .registry import AgentRegistry


class Registry:
    async def enqueue_session(
        self,
        session_creation_id: str,
        session_name: str,
        access_key: AccessKey,
        session_enqueue_configs: SessionEnqueueingConfig,
        scaling_group: str | None,
        session_type: SessionTypes,
        resource_policy: dict,
        *,
        user_scope: UserScope,
        public_sgroup_only: bool = True,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: str = None,
        internal_data: dict = None,
        starts_at: datetime = None,
        agent_list: Sequence[str] = None,
        dependency_sessions: Iterable[SessionId] = None,
        callback_url: URL = None,
    ) -> None:
        pass

    async def restart_session(
        self,
        session: SessionRow,
    ) -> None:
        pass

    async def destroy_session(
        self,
        session: SessionRow,
        *,
        forced: bool = False,
        reason: KernelLifecycleEventReason | None = None,
    ) -> None:
        pass


class Loop(ReconcilationLoop, Registry):
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    local_config: LocalConfig
    shared_config: SharedConfig
    lock_factory: DistributedLockFactory
    registry: AgentRegistry
    db_engine: ExtendedAsyncSAEngine

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        local_config: LocalConfig,
        shared_config: SharedConfig,
        lock_factory: DistributedLockFactory,
        db_engine: ExtendedAsyncSAEngine,
    ) -> None:
        self.local_config = local_config
        self.shared_config = shared_config
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.lock_factory = lock_factory
        self.db_engine = db_engine

    async def schedule_loop(self, resource_group: ScalingGroupRow):
        async with aiotools.aclosing(self.reconcile(DoScheduleEvent, 10.0)) as ag:
            async for ev in ag:
                # agents = await query_agents(status=ALIVE, sgroup=resource_group)
                existing_sessions, pending_sessions, cancelled_sessions = (
                    await SessionRow.get_sgroup_managed_sessions(
                        self.db_engine, resource_group.name
                    )
                )
                # scheduled_sessions = await dispatcher.schedule(candidate_sessions, running_sessions, agents)
                # await set_session_status(kernels, status=SCHEDULED)
                # await set_kernel_status(kernels, status=SCHEDULED)
                # await self.event_producer.produce_event(SessionScheduledEvent())
