from __future__ import annotations

import asyncio
import enum
import logging
import secrets
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from typing import (
    Any,
    Callable,
    Coroutine,
    Generic,
    Optional,
    Protocol,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    override,
)

import attrs
from aiomonitor.task import preserve_termination_log
from aiotools.taskgroup import PersistentTaskGroup
from aiotools.taskgroup.types import AsyncExceptionHandler

from ai.backend.common.message_queue.queue import AbstractMessageQueue, MessageId
from ai.backend.logging import BraceStyleAdapter

from .. import msgpack
from ..types import (
    AgentId,
)
from .reporter import AbstractEventReporter, CompleteEventReportArgs, PrepareEventReportArgs
from .types import AbstractEvent

__all__ = (
    "EventCallback",
    "EventDispatcher",
    "EventHandler",
    "EventProducer",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class _EventHandlerType(enum.StrEnum):
    CONSUMER = "consumer"
    SUBSCRIBER = "subscriber"


TEvent = TypeVar("TEvent", bound="AbstractEvent")
TEventCov = TypeVar("TEventCov", bound="AbstractEvent")
TContext = TypeVar("TContext")

EventCallback = Union[
    Callable[[TContext, AgentId, TEvent], Coroutine[Any, Any, None]],
    Callable[[TContext, AgentId, TEvent], None],
]


class EventHandlerType(enum.Enum):
    CONSUMER = "CONSUMER"
    SUBSCRIBER = "SUBSCRIBER"


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=False, order=False)
class EventHandler(Generic[TContext, TEvent]):
    event_cls: Type[TEvent]
    name: str
    context: TContext
    callback: EventCallback[TContext, TEvent]
    handler_type: _EventHandlerType
    coalescing_opts: Optional[CoalescingOptions]
    coalescing_state: CoalescingState
    args_matcher: Callable[[tuple], bool] | None
    event_start_reporters: tuple[AbstractEventReporter, ...] = attrs.field(factory=tuple)
    event_complete_reporters: tuple[AbstractEventReporter, ...] = attrs.field(factory=tuple)


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


class EventObserver(Protocol):
    def observe_event_success(self, *, event_type: str, duration: float) -> None: ...

    def observe_event_failure(
        self, *, event_type: str, duration: float, exception: BaseException
    ) -> None: ...


class NopEventObserver:
    def observe_event_success(self, *, event_type: str, duration: float) -> None:
        pass

    def observe_event_failure(
        self, *, event_type: str, duration: float, exception: BaseException
    ) -> None:
        pass


class _ConsumerPostCallback:
    def __init__(
        self,
        msg_id: MessageId,
        msg_queue: AbstractMessageQueue,
        remaining_handler_cnt: int,
    ) -> None:
        self._msg_id = msg_id
        self._msg_queue = msg_queue
        self._remaining_handler_cnt = remaining_handler_cnt
        self._lock = asyncio.Lock()

    async def done(self) -> None:
        # To ensure that all consumer handlers are called.
        # Basically there should be only one consumer handler for one event.
        async with self._lock:
            self._remaining_handler_cnt -= 1
            if self._remaining_handler_cnt > 0:
                return
        # All consumer handlers are called.
        await self._msg_queue.done(self._msg_id)


class PostCallback(Protocol):
    async def done(self) -> None:
        pass


class EventDispatcherGroup(ABC):
    @abstractmethod
    def with_reporters(
        self,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> EventDispatcherGroup:
        raise NotImplementedError

    @abstractmethod
    def consume(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
    ) -> EventHandler[TContext, TEvent]:
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        override_event_name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
    ) -> EventHandler[TContext, TEvent]:
        raise NotImplementedError


class _EventDispatcherWrapper(EventDispatcherGroup):
    _event_dispatcher: EventDispatcher

    _start_reporters: list[AbstractEventReporter]
    _complete_reporters: list[AbstractEventReporter]

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> None:
        self._event_dispatcher = event_dispatcher
        self._start_reporters = list(start_reporters)
        self._complete_reporters = list(complete_reporters)

    @override
    def with_reporters(
        self,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> _EventDispatcherWrapper:
        return _EventDispatcherWrapper(
            event_dispatcher=self._event_dispatcher,
            start_reporters=self._start_reporters + list(start_reporters),
            complete_reporters=self._complete_reporters + list(complete_reporters),
        )

    @override
    def consume(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
    ) -> EventHandler[TContext, TEvent]:
        return self._event_dispatcher.consume(
            event_cls,
            context,
            callback,
            coalescing_opts=coalescing_opts,
            name=name,
            args_matcher=args_matcher,
            start_reporters=tuple(self._start_reporters),
            complete_reporters=tuple(self._complete_reporters),
        )

    @override
    def subscribe(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        override_event_name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
    ) -> EventHandler[TContext, TEvent]:
        return self._event_dispatcher.subscribe(
            event_cls,
            context,
            callback,
            coalescing_opts=coalescing_opts,
            name=name,
            override_event_name=override_event_name,
            args_matcher=args_matcher,
            start_reporters=tuple(self._start_reporters),
            complete_reporters=tuple(self._complete_reporters),
        )


class EventDispatcher(EventDispatcherGroup):
    """
    We have two types of event handlers: consumer and subscriber.

    Consumers use the distribution pattern. Only one consumer among many manager worker processes
    receives the event.

    Consumer example: database updates upon specific events.

    Subscribers use the broadcast pattern. All subscribers in many manager worker processes
    receive the same event.

    Subscriber example: enqueuing events to the queues for event streaming API handlers
    """

    _consumers: defaultdict[
        str, set[EventHandler[Any, AbstractEvent]]
    ]  # TODO: set only one consumer handler for one event
    _subscribers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    _msg_queue: AbstractMessageQueue

    _consumer_loop_task: Optional[asyncio.Task]
    _subscriber_loop_task: Optional[asyncio.Task]
    _consumer_taskgroup: PersistentTaskGroup
    _subscriber_taskgroup: PersistentTaskGroup

    _log_events: bool
    _metric_observer: EventObserver

    def __init__(
        self,
        message_queue: AbstractMessageQueue,
        log_events: bool = False,
        *,
        consumer_exception_handler: AsyncExceptionHandler | None = None,
        subscriber_exception_handler: AsyncExceptionHandler | None = None,
        event_observer: EventObserver = NopEventObserver(),
    ) -> None:
        self._log_events = log_events
        self._closed = False
        self._consumers = defaultdict(set)
        self._subscribers = defaultdict(set)
        self._msg_queue = message_queue
        self._metric_observer = event_observer
        self._consumer_taskgroup = PersistentTaskGroup(
            name="consumer_taskgroup",
            exception_handler=consumer_exception_handler,
        )
        self._subscriber_taskgroup = PersistentTaskGroup(
            name="subscriber_taskgroup",
            exception_handler=subscriber_exception_handler,
        )
        self._consumer_loop_task = None
        self._subscriber_loop_task = None

    async def start(self) -> None:
        if self._closed:
            return
        self._consumer_loop_task = asyncio.create_task(self._consume_loop())
        self._subscriber_loop_task = asyncio.create_task(self._subscribe_loop())

    async def close(self) -> None:
        self._closed = True
        try:
            cancelled_tasks = []
            await self._consumer_taskgroup.shutdown()
            await self._subscriber_taskgroup.shutdown()

            def cancel_task(task: Optional[asyncio.Task]) -> None:
                if task is not None and not task.done():
                    task.cancel()
                    cancelled_tasks.append(task)

            cancel_task(self._consumer_loop_task)
            cancel_task(self._subscriber_loop_task)
            await asyncio.gather(*cancelled_tasks, return_exceptions=True)
        except Exception:
            log.exception("unexpected error while closing event dispatcher")

    @override
    def with_reporters(
        self,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> EventDispatcherGroup:
        return _EventDispatcherWrapper(
            event_dispatcher=self,
            start_reporters=list(start_reporters),
            complete_reporters=list(complete_reporters),
        )

    @override
    def consume(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> EventHandler[TContext, TEvent]:
        """
        Register a callback as a consumer. When multiple callback registers as a consumer
        on a single event, only one callable among those will be called.

        args_matcher:
          Optional. A callable which accepts event argument and supplies a bool as a return value.
          When specified, EventDispatcher will only execute callback when this lambda returns True.
        """

        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls,
            name,
            context,
            callback,
            _EventHandlerType.CONSUMER,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
            event_start_reporters=tuple(start_reporters),
            event_complete_reporters=tuple(complete_reporters),
        )
        self._consumers[event_cls.event_name()].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unconsume(
        self,
        handler: EventHandler[TContext, TEvent],
    ) -> None:
        self._consumers[handler.event_cls.event_name()].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    @override
    def subscribe(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        override_event_name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
        start_reporters: Sequence[AbstractEventReporter] = tuple(),
        complete_reporters: Sequence[AbstractEventReporter] = tuple(),
    ) -> EventHandler[TContext, TEvent]:
        """
        Subscribes to given event. All handlers will be called when certain event pops up.

        args_matcher:
          Optional. A callable which accepts event argument and supplies a bool as a return value.
          When specified, EventDispatcher will only execute callback when this lambda returns True.
        """

        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls,
            name,
            context,
            callback,
            _EventHandlerType.SUBSCRIBER,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
            event_start_reporters=tuple(start_reporters),
            event_complete_reporters=tuple(complete_reporters),
        )
        override_event_name = override_event_name or event_cls.event_name()
        self._subscribers[override_event_name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unsubscribe(
        self,
        handler: EventHandler[TContext, TEvent],
        *,
        override_event_name: Optional[str] = None,
    ) -> None:
        override_event_name = override_event_name or handler.event_cls.event_name()
        self._subscribers[override_event_name].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    async def _handle(
        self,
        evh: EventHandler,
        source: AgentId,
        args: tuple,
        post_callbacks: Sequence[PostCallback] = tuple(),
    ) -> None:
        if evh.args_matcher and not evh.args_matcher(args):
            return
        coalescing_opts = evh.coalescing_opts
        coalescing_state = evh.coalescing_state
        cb = evh.callback
        evh_type = evh.handler_type
        event_cls = evh.event_cls
        if self._closed:
            return
        event_type = event_cls.event_name()
        event = event_cls.deserialize(args)
        start = time.perf_counter()
        for start_reporter in evh.event_start_reporters:
            await start_reporter.prepare_event_report(event, PrepareEventReportArgs())
        try:
            if await coalescing_state.rate_control(coalescing_opts):
                if self._closed:
                    return
                if self._log_events:
                    log.debug("DISPATCH_{}(evh:{})", evh_type.name, evh.name)
                if asyncio.iscoroutinefunction(cb):
                    # mypy cannot catch the meaning of asyncio.iscoroutinefunction().
                    await cb(evh.context, source, event)  # type: ignore
                else:
                    cb(evh.context, source, event)  # type: ignore
                for post_callback in post_callbacks:
                    await post_callback.done()
                self._metric_observer.observe_event_success(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                )
        except Exception as e:
            self._metric_observer.observe_event_failure(
                event_type=event_type,
                duration=time.perf_counter() - start,
                exception=e,
            )
            log.exception(f"EventDispatcher.{evh_type}(): unexpected-error, {repr(e)}")
            raise
        except BaseException as e:
            self._metric_observer.observe_event_failure(
                event_type=event_type,
                duration=time.perf_counter() - start,
                exception=e,
            )
            raise
        duration = time.perf_counter() - start
        for complete in evh.event_complete_reporters:
            await complete.complete_event_report(event, CompleteEventReportArgs(duration))

    async def dispatch_consumers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
        post_callbacks: Sequence[PostCallback] = tuple(),
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_CONSUMERS(ev:{}, ag:{})", event_name, source)
        for consumer in self._consumers[event_name].copy():
            self._consumer_taskgroup.create_task(
                self._handle(consumer, source, args, post_callbacks),
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
        for subscriber in self._subscribers[event_name].copy():
            self._subscriber_taskgroup.create_task(
                self._handle(subscriber, source, args),
            )
            await asyncio.sleep(0)

    @preserve_termination_log
    async def _consume_loop(self) -> None:
        async for msg in self._msg_queue.consume_queue():  # type: ignore
            if self._closed:
                return
            decoded_event_name = msg.payload[b"name"].decode()
            post_callback = _ConsumerPostCallback(
                msg.msg_id,
                self._msg_queue,
                len(self._consumers[decoded_event_name]),
            )

            await self.dispatch_consumers(
                decoded_event_name,
                AgentId(msg.payload[b"source"].decode()),
                msgpack.unpackb(msg.payload[b"args"]),
                [post_callback],
            )

    @preserve_termination_log
    async def _subscribe_loop(self) -> None:
        async for msg in self._msg_queue.subscribe_queue():  # type: ignore
            if self._closed:
                return
            decoded_event_name = msg.payload[b"name"].decode()
            await self.dispatch_subscribers(
                decoded_event_name,
                AgentId(msg.payload[b"source"].decode()),
                msgpack.unpackb(msg.payload[b"args"]),
            )


class EventProducer:
    _closed: bool
    _msg_queue: AbstractMessageQueue
    _log_events: bool

    def __init__(
        self,
        msg_queue: AbstractMessageQueue,
        *,
        source: AgentId,
        log_events: bool = False,
    ) -> None:
        self._closed = False
        self._msg_queue = msg_queue
        self._source_bytes = source.encode()
        self._log_events = log_events

    async def close(self) -> None:
        self._closed = True
        await self._msg_queue.close()

    async def produce_event(
        self,
        event: AbstractEvent,
        source_override: Optional[AgentId] = None,
    ) -> None:
        if self._closed:
            return
        source_bytes = self._source_bytes
        if source_override is not None:
            source_bytes = source_override.encode()

        raw_event = {
            b"name": event.event_name().encode(),
            b"source": source_bytes,
            b"args": msgpack.packb(event.serialize()),
        }
        await self._msg_queue.send(raw_event)
