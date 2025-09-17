from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID
from strawberry.types import Info

from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.logging import BraceStyleAdapter

from .types import StrawberryGQLContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@strawberry.type
class BackgroundTaskEvent(Node):
    """Background task event information"""

    id: NodeID[str]
    task_id: ID
    event_name: str
    data: strawberry.scalars.JSON
    timestamp: datetime
    retry_count: Optional[int] = None


@strawberry.type
class BackgroundTaskProgress(Node):
    """Background task progress information"""

    id: NodeID[str]
    task_id: ID
    current_progress: Optional[float] = None
    total_progress: Optional[float] = None
    message: Optional[str] = None
    is_completed: bool = False
    is_failed: bool = False
    is_cancelled: bool = False


@strawberry.input
class BackgroundTaskEventFilter:
    """Filter for background task events"""

    task_id: Optional[ID] = None
    event_name: Optional[str] = None


async def _background_task_events_impl(task_id, context):
    """
    Subscribe to real-time background task events for a specific task.
    GraphQL Subscription equivalent of REST API /events/background-task
    """
    print(f"[DEBUG] SUBSCRIPTION IMPL CALLED WITH task_id={task_id}")
    log.info("=== BACKGROUND_TASK_EVENTS IMPL CALLED ===")
    log.info("BACKGROUND_TASK_EVENTS: task_id={}", task_id)

    try:
        # Get event hub and fetcher from context
        event_hub = context.event_hub
        event_fetcher = context.event_fetcher
        task_uuid = uuid.UUID(task_id)
        log.info("BACKGROUND_TASK_EVENTS subscription started (t:{})", task_uuid)

        # EventHub integration - similar to push_background_task_events()
        propagator = WithCachePropagator(event_fetcher)
        event_domain_key = (EventDomain.BGTASK, str(task_uuid))
        log.info("BACKGROUND_TASK_EVENTS: Registering propagator with key: {}", event_domain_key)
        event_hub.register_event_propagator(propagator, [event_domain_key])

        try:
            cache_id = EventCacheDomain.BGTASK.cache_id(str(task_uuid))
            log.info("BACKGROUND_TASK_EVENTS: Cache ID: {}", cache_id)

            # 먼저 현재 캐시된 상태가 있는지 확인해보자
            cached_event = await event_fetcher.fetch_cached_event(cache_id)
            if cached_event is not None:
                user_event = cached_event.user_event()
                if user_event is not None:
                    event_name = user_event.event_name()
                    if event_name is not None:
                        log.info("BACKGROUND_TASK_EVENTS: Yielding cached event: {}", event_name)
                        yield BackgroundTaskEvent(
                            id=ID(str(uuid.uuid4())),
                            task_id=task_id,
                            event_name=event_name,
                            data=user_event.user_event_mapping(),
                            timestamp=datetime.now(),
                            retry_count=user_event.retry_count(),
                        )
            else:
                log.info("BACKGROUND_TASK_EVENTS: No cached event found for task {}", task_uuid)

            # 이제 새로운 이벤트를 기다린다
            log.info("BACKGROUND_TASK_EVENTS: Starting to listen for new events...")
            async for event in propagator.receive(cache_id):
                log.info("BACKGROUND_TASK_EVENTS: Received raw event: {}", event)
                user_event = event.user_event()
                if user_event is None:
                    log.warning(
                        "Received unsupported user event: {}",
                        event.event_name(),
                    )
                    continue

                event_name = user_event.event_name()
                if event_name is None:
                    log.warning("Event has no event_name")
                    continue

                log.info("BACKGROUND_TASK_EVENTS: Yielding new event: {}", event_name)
                yield BackgroundTaskEvent(
                    id=ID(str(uuid.uuid4())),
                    task_id=task_id,
                    event_name=event_name,
                    data=user_event.user_event_mapping(),
                    timestamp=datetime.now(),
                    retry_count=user_event.retry_count(),
                )

                if user_event.is_close_event():
                    log.debug(
                        "Received close event: {}",
                        user_event.event_name(),
                    )
                    break
        finally:
            event_hub.unregister_event_propagator(propagator.id())
            log.info("BACKGROUND_TASK_EVENTS subscription ended (t:{})", task_uuid)

    except Exception as e:
        log.error("BACKGROUND_TASK_EVENTS: Error in subscription: {}", e)
        log.exception("Full traceback:")
        # 예외가 발생해도 최소 하나의 이벤트는 yield하자
        yield BackgroundTaskEvent(
            id=ID(str(uuid.uuid4())),
            task_id=task_id,
            event_name="error_fallback",
            data={"error": str(e)},
            timestamp=datetime.now(),
            retry_count=0,
        )


@strawberry.subscription(description="Subscribe to background task events")
async def background_task_events(
    task_id: ID,
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[Optional[BackgroundTaskEvent], None]:
    """
    Subscribe to real-time background task events for a specific task.
    GraphQL Subscription equivalent of REST API /events/background-task
    """
    async for event in _background_task_events_impl(task_id, info.context):
        yield event


@strawberry.field(description="Get current background task progress")
async def background_task_progress(
    task_id: ID,
    info: Info[StrawberryGQLContext],
) -> Optional[BackgroundTaskProgress]:
    """
    Get current progress status of a specific background task.
    Returns the latest progress information from Redis cache.
    """
    task_uuid = uuid.UUID(task_id)
    log.info("BACKGROUND_TASK_PROGRESS query started (t:{})", task_uuid)

    try:
        # Get the cached progress event directly from Redis via EventFetcher
        cache_id = EventCacheDomain.BGTASK.cache_id(str(task_uuid))
        cached_event = await info.context.event_fetcher.fetch_cached_event(cache_id)

        if cached_event is None:
            log.debug("No cached progress data found for task (t:{})", task_uuid)
            return None

        # Get user event from the cached event
        user_event = cached_event.user_event()
        if user_event is None:
            log.debug("No user event found for task (t:{})", task_uuid)
            return None

        event_name = user_event.event_name()
        event_data = user_event.user_event_mapping()

        # Determine task status
        is_completed = event_name == "bgtask_done"
        is_failed = event_name == "bgtask_failed"
        is_cancelled = event_name == "bgtask_cancelled"

        # Extract progress information
        current_progress = None
        total_progress = None
        message = None

        if event_name == "bgtask_updated":
            current_progress = event_data.get("current_progress")
            total_progress = event_data.get("total_progress")
            message = event_data.get("message")
        elif is_completed or is_failed or is_cancelled:
            message = event_data.get("message")
        return BackgroundTaskProgress(
            id=ID(str(task_uuid)),
            task_id=task_id,
            current_progress=current_progress,
            total_progress=total_progress,
            message=message,
            is_completed=is_completed,
            is_failed=is_failed,
            is_cancelled=is_cancelled,
        )

    except Exception as e:
        log.warning("Failed to get background task progress (t:{}): {}", task_uuid, e)
        return None
    finally:
        log.info("BACKGROUND_TASK_PROGRESS query ended (t:{})", task_uuid)
