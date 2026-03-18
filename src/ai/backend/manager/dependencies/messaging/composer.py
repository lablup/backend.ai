from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.manager.config.unified import ManagerUnifiedConfig

from .event_fetcher import EventFetcherDependency
from .event_hub import EventHubDependency
from .event_producer import EventProducerDependency, EventProducerInput
from .message_queue import MessageQueueDependency, MessageQueueInput


@dataclass
class MessagingInput:
    """Input required for messaging setup.

    Contains configuration for all messaging dependencies.
    """

    config: ManagerUnifiedConfig


@dataclass
class MessagingResources:
    """Container for all messaging resources.

    Holds event hub, message queue, event producer, and event fetcher.
    """

    event_hub: EventHub
    message_queue: AbstractMessageQueue
    event_producer: EventProducer
    event_fetcher: EventFetcher


class MessagingComposer(DependencyComposer[MessagingInput, MessagingResources]):
    """Composes all messaging dependencies.

    Composes messaging components in dependency order:
    1. Event hub: Manages event propagation (independent)
    2. Message queue: Redis-based message queue (config dependency)
    3. Event fetcher: Fetches cached events (message_queue dependency)
    4. Event producer: Produces events (message_queue + config dependency)
    """

    @property
    def stage_name(self) -> str:
        return "messaging"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: MessagingInput,
    ) -> AsyncIterator[MessagingResources]:
        """Compose messaging dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Messaging input containing configuration

        Yields:
            MessagingResources containing all messaging components
        """
        # Initialize event hub (independent)
        event_hub = await stack.enter_dependency(
            EventHubDependency(),
            None,
        )

        # Initialize message queue (config dependency)
        message_queue = await stack.enter_dependency(
            MessageQueueDependency(),
            MessageQueueInput(config=setup_input.config),
        )

        # Initialize event fetcher (message_queue dependency)
        event_fetcher = await stack.enter_dependency(
            EventFetcherDependency(),
            message_queue,
        )

        # Initialize event producer (message_queue + config dependency)
        event_producer = await stack.enter_dependency(
            EventProducerDependency(),
            EventProducerInput(
                message_queue=message_queue,
                config=setup_input.config,
            ),
        )

        # Yield messaging resources
        yield MessagingResources(
            event_hub=event_hub,
            message_queue=message_queue,
            event_producer=event_producer,
            event_fetcher=event_fetcher,
        )
