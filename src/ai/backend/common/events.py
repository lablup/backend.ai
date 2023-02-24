from __future__ import annotations

import abc
import asyncio
import enum
import hashlib
import logging
import secrets
import socket
import uuid
from collections import defaultdict
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Coroutine,
    Generic,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

import attrs
from aiomonitor.task import preserve_termination_log
from aiotools.context import aclosing
from aiotools.server import process_index
from aiotools.taskgroup import PersistentTaskGroup
from redis.asyncio import ConnectionPool
from typing_extensions import TypeAlias

from . import msgpack, redis_helper
from .logging import BraceStyleAdapter
from .types import (
    AgentId,
    EtcdRedisConfig,
    KernelId,
    LogSeverity,
    RedisConnectionInfo,
    SessionId,
    aobject,
)

__all__ = (
    "AbstractEvent",
    "EventCallback",
    "EventDispatcher",
    "EventHandler",
    "EventProducer",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

PTGExceptionHandler: TypeAlias = Callable[
    [Type[Exception], Exception, TracebackType], Awaitable[None]
]


class AbstractEvent(metaclass=abc.ABCMeta):

    # derivatives should define the fields.

    name: ClassVar[str] = "undefined"

    @abc.abstractmethod
    def serialize(self) -> tuple:
        """
        Return a msgpack-serializable tuple.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, value: tuple):
        """
        Construct the event args from a tuple deserialized from msgpack.
        """
        pass


class EmptyEventArgs:
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple):
        return cls()


class DoScheduleEvent(EmptyEventArgs, AbstractEvent):
    name = "do_schedule"


class DoPrepareEvent(EmptyEventArgs, AbstractEvent):
    name = "do_prepare"


class DoIdleCheckEvent(EmptyEventArgs, AbstractEvent):
    name = "do_idle_check"


@attrs.define(slots=True, frozen=True)
class DoTerminateSessionEvent(AbstractEvent):
    name = "do_terminate_session"

    session_id: SessionId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field()

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )


@attrs.define(slots=True, frozen=True)
class GenericAgentEventArgs:

    reason: str = attrs.field(default="")

    def serialize(self) -> tuple:
        return (self.reason,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


class AgentStartedEvent(GenericAgentEventArgs, AbstractEvent):
    name = "agent_started"


class AgentTerminatedEvent(GenericAgentEventArgs, AbstractEvent):
    name = "agent_terminated"


@attrs.define(slots=True, frozen=True)
class AgentErrorEvent(AbstractEvent):
    name = "agent_error"

    message: str = attrs.field()
    traceback: Optional[str] = attrs.field(default=None)
    user: Optional[Any] = attrs.field(default=None)
    context_env: Mapping[str, Any] = attrs.field(factory=dict)
    severity: LogSeverity = attrs.field(default=LogSeverity.ERROR)

    def serialize(self) -> tuple:
        return (
            self.message,
            self.traceback,
            self.user,
            self.context_env,
            self.severity.value,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            value[0],
            value[1],
            value[2],
            value[3],
            LogSeverity(value[4]),
        )


@attrs.define(slots=True, frozen=True)
class AgentHeartbeatEvent(AbstractEvent):
    name = "agent_heartbeat"

    agent_info: Mapping[str, Any] = attrs.field()

    def serialize(self) -> tuple:
        return (self.agent_info,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


class KernelLifecycleEventReason(str, enum.Enum):
    AGENT_TERMINATION = "agent-termination"
    ALREADY_TERMINATED = "already-terminated"
    ANOMALY_DETECTED = "anomaly-detected"
    EXEC_TIMEOUT = "exec-timeout"
    FAILED_TO_START = "failed-to-start"
    FORCE_TERMINATED = "force-terminated"
    IDLE_TIMEOUT = "idle-timeout"
    IDLE_SESSION_LIFETIME = "idle-session-lifetime"
    IDLE_UTILIZATION = "idle-utilization"
    KILLED_BY_EVENT = "killed-by-event"
    NEW_CONTAINER_STARTED = "new-container-started"
    PENDING_TIMEOUT = "pending-timeout"
    RESTARTING = "restarting"
    RESTART_TIMEOUT = "restart-timeout"
    RESUMING_AGENT_OPERATION = "resuming-agent-operation"
    SELF_TERMINATED = "self-terminated"
    TASK_DONE = "task-done"
    TASK_FAILED = "task-failed"
    TASK_TIMEOUT = "task-timeout"
    TASK_CANCELLED = "task-cancelled"
    TASK_FINISHED = "task-finished"
    TERMINATED_UNKNOWN_CONTAINER = "terminated-unknown-container"
    UNKNOWN = "unknown"
    USER_REQUESTED = "user-requested"

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional[KernelLifecycleEventReason]:
        try:
            return cls(value)
        except ValueError:
            pass
        return None


@attrs.define(slots=True, frozen=True)
class KernelCreationEventArgs:
    kernel_id: KernelId = attrs.field()
    creation_id: str = attrs.field()
    reason: str = attrs.field(default="")
    creation_info: Mapping[str, Any] = attrs.field(factory=dict)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            self.creation_id,
            self.reason,
            self.creation_info,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            creation_id=value[1],
            reason=value[2],
            creation_info=value[3],
        )


class KernelEnqueuedEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_enqueued"


class KernelPreparingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_preparing"


class KernelPullingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_pulling"


@attrs.define(auto_attribs=True, slots=True)
class KernelPullProgressEvent(AbstractEvent):
    name = "kernel_pull_progress"
    kernel_id: uuid.UUID = attrs.field()
    current_progress: float = attrs.field()
    total_progress: float = attrs.field()
    message: Optional[str] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            self.current_progress,
            self.total_progress,
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
            value[2],
            value[3],
        )


class KernelCreatingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_creating"


class KernelStartedEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_started"


class KernelCancelledEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_cancelled"


@attrs.define(slots=True, frozen=True)
class KernelTerminationEventArgs:
    kernel_id: KernelId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)
    exit_code: int = attrs.field(default=-1)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            KernelId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )


class KernelTerminatingEvent(KernelTerminationEventArgs, AbstractEvent):
    name = "kernel_terminating"


class KernelTerminatedEvent(KernelTerminationEventArgs, AbstractEvent):
    name = "kernel_terminated"


@attrs.define(slots=True, frozen=True)
class SessionCreationEventArgs:
    session_id: SessionId = attrs.field()
    creation_id: str = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.creation_id,
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )


class SessionEnqueuedEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_enqueued"


class SessionScheduledEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_scheduled"


class SessionPreparingEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_preparing"


class SessionCancelledEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_cancelled"


class SessionStartedEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_started"


@attrs.define(slots=True, frozen=True)
class SessionTerminationEventArgs:
    session_id: SessionId = attrs.field()
    reason: str = attrs.field(default="")

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )


class SessionTerminatedEvent(SessionTerminationEventArgs, AbstractEvent):
    name = "session_terminated"


@attrs.define(slots=True, frozen=True)
class SessionResultEventArgs:
    session_id: SessionId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)
    exit_code: int = attrs.field(default=-1)

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )


class SessionSuccessEvent(SessionResultEventArgs, AbstractEvent):
    name = "session_success"


class SessionFailureEvent(SessionResultEventArgs, AbstractEvent):
    name = "session_failure"


@attrs.define(auto_attribs=True, slots=True)
class DoSyncKernelLogsEvent(AbstractEvent):
    name = "do_sync_kernel_logs"

    kernel_id: KernelId = attrs.field()
    container_id: str = attrs.field()

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            self.container_id,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            KernelId(uuid.UUID(value[0])),
            value[1],
        )


@attrs.define(auto_attribs=True, slots=True)
class DoSyncKernelStatsEvent(AbstractEvent):
    name = "do_sync_kernel_stats"

    kernel_ids: Sequence[KernelId] = attrs.field()

    def serialize(self) -> tuple:
        return ([*map(str, self.kernel_ids)],)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            kernel_ids=tuple(KernelId(uuid.UUID(item)) for item in value[0]),
        )


@attrs.define(auto_attribs=True, slots=True)
class GenericSessionEventArgs(AbstractEvent):
    session_id: SessionId = attrs.field()

    def serialize(self) -> tuple:
        return (str(self.session_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
        )


class ExecutionStartedEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_started"


class ExecutionFinishedEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_finished"


class ExecutionTimeoutEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_timeout"


class ExecutionCancelledEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_cancelled"


@attrs.define(auto_attribs=True, slots=True)
class BgtaskUpdatedEvent(AbstractEvent):
    name = "bgtask_updated"

    task_id: uuid.UUID = attrs.field()
    current_progress: float = attrs.field()
    total_progress: float = attrs.field()
    message: Optional[str] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.current_progress,
            self.total_progress,
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
            value[2],
            value[3],
        )


@attrs.define(auto_attribs=True, slots=True)
class BgtaskDoneEventArgs:
    task_id: uuid.UUID = attrs.field()
    message: Optional[str] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
        )


class BgtaskDoneEvent(BgtaskDoneEventArgs, AbstractEvent):
    name = "bgtask_done"


class BgtaskCancelledEvent(BgtaskDoneEventArgs, AbstractEvent):
    name = "bgtask_cancelled"


class BgtaskFailedEvent(BgtaskDoneEventArgs, AbstractEvent):
    name = "bgtask_failed"


class RedisConnectorFunc(Protocol):
    def __call__(
        self,
    ) -> ConnectionPool:
        ...


TEvent = TypeVar("TEvent", bound="AbstractEvent")
TEventCov = TypeVar("TEventCov", bound="AbstractEvent")
TContext = TypeVar("TContext")

EventCallback = Union[
    Callable[[TContext, AgentId, TEvent], Coroutine[Any, Any, None]],
    Callable[[TContext, AgentId, TEvent], None],
]


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=False, order=False)
class EventHandler(Generic[TContext, TEvent]):
    event_cls: Type[TEvent]
    name: str
    context: TContext
    callback: EventCallback[TContext, TEvent]
    coalescing_opts: Optional[CoalescingOptions]
    coalescing_state: CoalescingState


class CoalescingOptions(TypedDict):
    max_wait: float
    max_batch_size: int


@attrs.define(auto_attribs=True, slots=True)
class CoalescingState:
    batch_size: int = 0
    last_added: float = 0.0
    last_handle: asyncio.TimerHandle | None = None
    fut_sync: asyncio.Future | None = None

    def proceed(self):
        if self.fut_sync is not None and not self.fut_sync.done():
            self.fut_sync.set_result(None)

    async def rate_control(self, opts: CoalescingOptions | None) -> bool:
        if opts is None:
            return True
        loop = asyncio.get_running_loop()
        if self.fut_sync is None:
            self.fut_sync = loop.create_future()
        assert self.fut_sync is not None
        self.last_added = loop.time()
        self.batch_size += 1
        if self.batch_size >= opts["max_batch_size"]:
            assert self.last_handle is not None
            self.last_handle.cancel()
            self.fut_sync.cancel()
            self.last_handle = None
            self.last_added = 0.0
            self.batch_size = 0
            return True
        # Schedule.
        self.last_handle = loop.call_later(
            opts["max_wait"],
            self.proceed,
        )
        if self.last_added > 0 and loop.time() - self.last_added < opts["max_wait"]:
            # Cancel the previously pending task.
            self.last_handle.cancel()
            self.fut_sync.cancel()
            # Reschedule.
            self.fut_sync = loop.create_future()
            self.last_handle = loop.call_later(
                opts["max_wait"],
                self.proceed,
            )
        try:
            await self.fut_sync
        except asyncio.CancelledError:
            if self.last_handle is not None and not self.last_handle.cancelled():
                self.last_handle.cancel()
            return False
        else:
            self.fut_sync = None
            self.last_handle = None
            self.last_added = 0.0
            self.batch_size = 0
            return True


class EventDispatcher(aobject):
    """
    We have two types of event handlers: consumer and subscriber.

    Consumers use the distribution pattern. Only one consumer among many manager worker processes
    receives the event.

    Consumer example: database updates upon specific events.

    Subscribers use the broadcast pattern. All subscribers in many manager worker processes
    receive the same event.

    Subscriber example: enqueuing events to the queues for event streaming API handlers
    """

    consumers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    subscribers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    redis_client: RedisConnectionInfo
    consumer_loop_task: asyncio.Task
    subscriber_loop_task: asyncio.Task
    consumer_taskgroup: PersistentTaskGroup
    subscriber_taskgroup: PersistentTaskGroup

    _log_events: bool
    _consumer_name: str

    def __init__(
        self,
        redis_config: EtcdRedisConfig,
        db: int = 0,
        log_events: bool = False,
        *,
        service_name: str = None,
        stream_key: str = "events",
        consumer_group: str = "manager",
        node_id: str = None,
        consumer_exception_handler: PTGExceptionHandler = None,
        subscriber_exception_handler: PTGExceptionHandler = None,
    ) -> None:
        _redis_config = redis_config.copy()
        if service_name:
            _redis_config["service_name"] = service_name
        self.redis_client = redis_helper.get_redis_object(_redis_config, db=db)
        self._log_events = log_events
        self._closed = False
        self.consumers = defaultdict(set)
        self.subscribers = defaultdict(set)
        self._stream_key = stream_key
        self._consumer_group = consumer_group
        self._consumer_name = _generate_consumer_id(node_id)
        self.consumer_taskgroup = PersistentTaskGroup(
            name="consumer_taskgroup",
            exception_handler=consumer_exception_handler,
        )
        self.subscriber_taskgroup = PersistentTaskGroup(
            name="subscriber_taskgroup",
            exception_handler=subscriber_exception_handler,
        )

    async def __ainit__(self) -> None:
        self.consumer_loop_task = asyncio.create_task(self._consume_loop())
        self.subscriber_loop_task = asyncio.create_task(self._subscribe_loop())

    async def close(self) -> None:
        self._closed = True
        try:
            cancelled_tasks = []
            await self.consumer_taskgroup.shutdown()
            await self.subscriber_taskgroup.shutdown()
            if not self.consumer_loop_task.done():
                self.consumer_loop_task.cancel()
                cancelled_tasks.append(self.consumer_loop_task)
            if not self.subscriber_loop_task.done():
                self.subscriber_loop_task.cancel()
                cancelled_tasks.append(self.subscriber_loop_task)
            await asyncio.gather(*cancelled_tasks, return_exceptions=True)
        except Exception:
            log.exception("unexpected error while closing event dispatcher")
        finally:
            await self.redis_client.close()

    def consume(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: CoalescingOptions = None,
        *,
        name: str = None,
    ) -> EventHandler[TContext, TEvent]:
        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls, name, context, callback, coalescing_opts, CoalescingState()
        )
        self.consumers[event_cls.name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unconsume(
        self,
        handler: EventHandler[TContext, TEvent],
    ) -> None:
        self.consumers[handler.event_cls.name].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    def subscribe(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: CoalescingOptions = None,
        *,
        name: str = None,
    ) -> EventHandler[TContext, TEvent]:
        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls, name, context, callback, coalescing_opts, CoalescingState()
        )
        self.subscribers[event_cls.name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unsubscribe(
        self,
        handler: EventHandler[TContext, TEvent],
    ) -> None:
        self.subscribers[handler.event_cls.name].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    async def handle(self, evh_type: str, evh: EventHandler, source: AgentId, args: tuple) -> None:
        coalescing_opts = evh.coalescing_opts
        coalescing_state = evh.coalescing_state
        cb = evh.callback
        event_cls = evh.event_cls
        if self._closed:
            return
        if await coalescing_state.rate_control(coalescing_opts):
            if self._closed:
                return
            if self._log_events:
                log.debug("DISPATCH_{}(evh:{})", evh_type, evh.name)
            if asyncio.iscoroutinefunction(cb):
                # mypy cannot catch the meaning of asyncio.iscoroutinefunction().
                await cb(evh.context, source, event_cls.deserialize(args))  # type: ignore
            else:
                cb(evh.context, source, event_cls.deserialize(args))  # type: ignore

    async def dispatch_consumers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_CONSUMERS(ev:{}, ag:{})", event_name, source)
        for consumer in self.consumers[event_name].copy():
            self.consumer_taskgroup.create_task(
                self.handle("CONSUMER", consumer, source, args),
            )
            await asyncio.sleep(0)

    async def dispatch_subscribers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_SUBSCRIBERS(ev:{}, ag:{})", event_name, source)
        for subscriber in self.subscribers[event_name].copy():
            self.subscriber_taskgroup.create_task(
                self.handle("SUBSCRIBER", subscriber, source, args),
            )
            await asyncio.sleep(0)

    @preserve_termination_log
    async def _consume_loop(self) -> None:
        async with aclosing(
            redis_helper.read_stream_by_group(
                self.redis_client,
                self._stream_key,
                self._consumer_group,
                self._consumer_name,
            )
        ) as agen:
            async for msg_id, msg_data in agen:
                if self._closed:
                    return
                if msg_data is None:
                    continue
                try:
                    await self.dispatch_consumers(
                        msg_data[b"name"].decode(),
                        msg_data[b"source"].decode(),
                        msgpack.unpackb(msg_data[b"args"]),
                    )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("EventDispatcher.consume(): unexpected-error")

    @preserve_termination_log
    async def _subscribe_loop(self) -> None:
        async with aclosing(
            redis_helper.read_stream(
                self.redis_client,
                self._stream_key,
            )
        ) as agen:
            async for msg_id, msg_data in agen:
                if self._closed:
                    return
                if msg_data is None:
                    continue
                try:
                    await self.dispatch_subscribers(
                        msg_data[b"name"].decode(),
                        msg_data[b"source"].decode(),
                        msgpack.unpackb(msg_data[b"args"]),
                    )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("EventDispatcher.subscribe(): unexpected-error")


class EventProducer(aobject):
    redis_client: RedisConnectionInfo
    _log_events: bool

    def __init__(
        self,
        redis_config: EtcdRedisConfig,
        db: int = 0,
        *,
        service_name: str = None,
        stream_key: str = "events",
        log_events: bool = False,
    ) -> None:
        _redis_config = redis_config.copy()
        if service_name:
            _redis_config["service_name"] = service_name
        self._closed = False
        self.redis_client = redis_helper.get_redis_object(_redis_config, db=db)
        self._log_events = log_events
        self._stream_key = stream_key

    async def __ainit__(self) -> None:
        pass

    async def close(self) -> None:
        self._closed = True
        await self.redis_client.close()

    async def produce_event(
        self,
        event: AbstractEvent,
        *,
        source: str = "manager",
    ) -> None:
        if self._closed:
            return
        raw_event = {
            b"name": event.name.encode(),
            b"source": source.encode(),
            b"args": msgpack.packb(event.serialize()),
        }
        await redis_helper.execute(
            self.redis_client,
            lambda r: r.xadd(self._stream_key, raw_event),  # type: ignore # aio-libs/aioredis-py#1182
        )


def _generate_consumer_id(node_id: str = None) -> str:
    h = hashlib.sha1()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()
    h = hashlib.sha1()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()
    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
