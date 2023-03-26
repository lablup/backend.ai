from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Mapping, Optional, Type
from uuid import UUID

import attrs
from tenacity import RetryError, TryAgain

from ai.backend.common.automata import (
    AsyncStateMachine,
    BaseMachineContext,
    BaseStateContext,
    BaseStateName,
    BaseTrigger,
    State,
    Transition,
)
from ai.backend.common.events import KernelPullingEvent
from ai.backend.common.types import (
    ClusterMode,
    KernelEnqueueingConfig,
    SessionId,
    SessionResult,
    SessionTypes,
)

from ..models.session import SessionStatus

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import AbstractEvent, EventDispatcher, EventProducer

    from ..models.utils import ExtendedAsyncSAEngine


@attrs.define(slots=True)
class SessionMachineContext(BaseMachineContext):
    db: ExtendedAsyncSAEngine
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    background_task_manager: BackgroundTaskManager


@attrs.define(slots=True)
class SessionStateContext(BaseStateContext):
    session_id: SessionId
    name: str
    session_type: SessionTypes
    kernel_enqueue_configs: list[KernelEnqueueingConfig]

    cluster_mode: ClusterMode
    cluster_size: int
    # Resource ownership
    scaling_group_name: str
    target_sgroup_names: Optional[str]
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    access_key: UUID
    tag: Optional[str]

    # Resource occupation
    occupying_slots: dict
    requested_slots: dict
    vfolder_mounts: dict
    resource_opts: dict
    environ: dict
    bootstrap_script: str
    use_host_network: bool

    # Lifecycle
    timeout: int
    created_at: datetime
    terminated_at: datetime
    starts_at: datetime
    status: SessionStatus
    status_info: str

    status_data: dict
    status_history: dict
    callback_url: str

    startup_command: str
    result: SessionResult


class SessionStateName(BaseStateName):
    CHECK_IMAGE = "check-image"
    PULL_IMAGE = "pull-image"
    PREPARE_NETWORK = "prepare-network"
    CREATE_CONTAINER = "create-container"
    START_CONTAINER = "start-container"
    WAIT_KERNEL_RUNNER = "wait-kernel-runner"
    CLEANUP = "cleanup"
    DONE = "done"
    FAILURE = "failure"


class SessionTransitionTrigger(BaseTrigger):
    SUCCESS = "success"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    MAX_RETRY_EXCEEDED = "max-retry-exceeded"


async def check_image(
    ctx: SessionMachineContext, state_ctx: Optional[SessionStateContext]
) -> Optional[SessionStateContext]:
    return state_ctx


async def pull_image(
    ctx: SessionMachineContext, state_ctx: Optional[SessionStateContext]
) -> Optional[SessionStateContext]:
    return state_ctx


check_image_state: State = State(SessionStateName.CHECK_IMAGE, check_image)
pull_image_state: State = State(SessionStateName.PULL_IMAGE, pull_image)
done_state: State = State(SessionStateName.DONE)
failure_state: State = State(SessionStateName.FAILURE)

to_pull_image = Transition(
    [(check_image_state, SessionTransitionTrigger.SUCCESS)], pull_image_state
)

EVENT_TRANSITION_MAP: Mapping[Type[AbstractEvent], Transition] = {
    KernelPullingEvent: to_pull_image,
}


class SessionStateMachine(AsyncStateMachine):
    async def interrupt(self, event: AbstractEvent) -> None:
        """
        Handle event in this state machine.
        """

    async def run(self) -> None:
        coro_factory = self.current_state.coro_factory
        if coro_factory is None:
            return
        try:
            retry = self.current_state.retry
            if retry is not None:
                async for attempt in retry:
                    with attempt:
                        try:
                            new_data = await coro_factory(self.ctx, self.current_state.data)
                        except asyncio.TimeoutError:
                            raise TryAgain
            else:
                new_data = await coro_factory(self.ctx, self.current_state.data)
        except asyncio.CancelledError:
            self.current_state = await self.trigger(SessionTransitionTrigger.CANCELLED)
            raise
        except asyncio.TimeoutError:
            self.current_state = await self.trigger(SessionTransitionTrigger.TIMEOUT)
            raise
        except RetryError:
            self.current_state = await self.trigger(SessionTransitionTrigger.MAX_RETRY_EXCEEDED)
            raise
        except Exception:
            self.current_state = await self.trigger(SessionTransitionTrigger.EXCEPTION)
            raise
        else:
            self.current_state = await self.trigger(SessionTransitionTrigger.SUCCESS, new_data)
        if self.current_state not in (done_state, failure_state):
            await self.run()
