from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .event import (
    EventDispatcherInput,
    EventDispatcherProvider,
    EventProducerInput,
    EventProducerProvider,
)
from .message_queue import MessageQueueInput, MessageQueueProvider


@dataclass
class MessagingComposerInput:
    """Input for Messaging composer."""

    local_config: StorageProxyUnifiedConfig
    redis_config: RedisConfig
    metric_registry: CommonMetricRegistry


@dataclass
class MessagingResources:
    """All messaging resources for storage proxy."""

    message_queue: AbstractMessageQueue
    event_producer: EventProducer
    event_dispatcher: EventDispatcher


class MessagingComposer(DependencyComposer[MessagingComposerInput, MessagingResources]):
    """Composer for messaging layer dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "messaging"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: MessagingComposerInput,
    ) -> AsyncIterator[MessagingResources]:
        """Compose all messaging dependencies."""
        local_config = setup_input.local_config
        log_events = local_config.debug.log_events

        message_queue = await stack.enter_dependency(
            MessageQueueProvider(),
            MessageQueueInput(
                redis_config=setup_input.redis_config,
                node_id=local_config.storage_proxy.node_id,
            ),
        )
        event_producer = await stack.enter_dependency(
            EventProducerProvider(),
            EventProducerInput(message_queue=message_queue, log_events=log_events),
        )
        event_dispatcher = await stack.enter_dependency(
            EventDispatcherProvider(),
            EventDispatcherInput(
                message_queue=message_queue,
                log_events=log_events,
                metric_registry=setup_input.metric_registry,
            ),
        )

        yield MessagingResources(
            message_queue=message_queue,
            event_producer=event_producer,
            event_dispatcher=event_dispatcher,
        )
