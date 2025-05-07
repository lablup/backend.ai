import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, MutableMapping, Optional

from ai.backend.common.events.events import AbstractEvent, EventDomain
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventPropagator(ABC):
    @abstractmethod
    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for the propagator.
        """
        raise NotImplementedError

    @abstractmethod
    async def propagate_event(self, event: AbstractEvent) -> None:
        """
        Propagate an event to the event hub.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the propagator.
        """
        raise NotImplementedError


class AsyncBypassPropagator(EventPropagator):
    """
    A simple event propagator that uses an asyncio queue to propagate events.
    """

    _id: uuid.UUID
    _queue: asyncio.Queue[Optional[AbstractEvent]]
    _closed: bool = False

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._queue = asyncio.Queue()
        self._closed = False

    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for the propagator.
        """
        return self._id

    async def receive_once(self) -> AbstractEvent:
        """
        Receive an event from the queue.
        When use this method, don't use the receive method.
        """
        if self._closed:
            raise RuntimeError("AsyncBypassPropagator is closed")
        event = await self._queue.get()
        if event is None:
            raise RuntimeError("AsyncBypassPropagator is closed")
        return event

    async def receive(self) -> AsyncIterator[AbstractEvent]:
        """
        Receive events from the queue.
        This method is a generator that yields events until the queue is closed.
        When use this method, don't use the receive_once method.
        """
        while not self._closed:
            event = await self._queue.get()
            try:
                if event is None:
                    break
                yield event
            except Exception as e:
                log.error("Error propagating event: {}", e)

    async def propagate_event(self, event: AbstractEvent) -> None:
        await self._queue.put(event)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)


@dataclass
class _PropagatorInfo:
    """
    Class to hold propagator information.
    """

    propagator: EventPropagator
    aliases: list[tuple[EventDomain, str]]


class EventHub:
    """
    EventHub manages the registration and propagation of events to various subscribers.
    It allows for the registration of event subscribers, the propagation of events to those subscribers,
    and the management of event aliases.
    """

    _propagators: MutableMapping[uuid.UUID, _PropagatorInfo]
    _key_alias: MutableMapping[tuple[EventDomain, str], set[uuid.UUID]]

    def __init__(self) -> None:
        self._propagators = {}
        self._key_alias = {}

    def register_event_propagator(
        self,
        event_propagator: EventPropagator,
        aliases: list[tuple[EventDomain, str]] = [],
    ) -> None:
        """
        Register a new event propagator.
        :param event_propagator: The event propagator instance implementing EventPropagator.
        :param aliases: List of aliases for the propagator.
        :raises ValueError: If the propagator is already registered.
        """
        propagator_id = event_propagator.id()
        self._propagators[propagator_id] = _PropagatorInfo(event_propagator, aliases)
        for alias in aliases:
            self._add_alias(alias, propagator_id)

    def unregister_event_propagator(self, propagator_id: uuid.UUID) -> None:
        """
        Unregister an event propagator.
        :param propagator_id: Unique identifier for the propagator.
        :raises ValueError: If the propagator is not registered.
        """
        if propagator_id not in self._propagators:
            raise ValueError(f"propagator with ID {propagator_id} not found.")
        propagator_info = self._propagators[propagator_id]
        for alias in propagator_info.aliases:
            if alias in self._key_alias:
                self._remove_alias(alias, propagator_id)
        del self._propagators[propagator_id]

    async def propagate_event(self, event: AbstractEvent) -> None:
        """
        Propagate an event to all registered propagators.
        :param event: The event to be propagated.
        """
        domain_id = event.domain_id()
        if domain_id is None:
            # If the event does not have a domain ID, it is not propagated.
            return
        propagators = self._get_propagators_by_alias(event.event_domain(), domain_id)
        for propagator in propagators:
            await propagator.propagate_event(event)

    async def close_by_alias(
        self,
        alias_domain: EventDomain,
        alias_id: str,
    ) -> None:
        """
        Close all propagators associated with the specified alias.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        """
        if (alias_domain, alias_id) not in self._key_alias:
            raise ValueError(f"Alias {alias_domain}:{alias_id} not found.")

        propagator_set = self._key_alias[(alias_domain, alias_id)]
        for propagator_id in propagator_set:
            await self._propagators[propagator_id].propagator.close()

    def _get_propagators_by_alias(
        self,
        alias_domain: EventDomain,
        alias_id: str,
    ) -> set[EventPropagator]:
        """
        Get the propagator associated with the specified alias.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :return: The propagator associated with the alias, or None if not found.
        """
        if (alias_domain, alias_id) not in self._key_alias:
            return set()
        propagator_set = self._key_alias[(alias_domain, alias_id)]
        propagators = set()
        for propagator_id in propagator_set.copy():
            if propagator_id in self._propagators:
                propagators.add(self._propagators[propagator_id].propagator)
        return propagators

    def _add_alias(
        self,
        alias_key: tuple[EventDomain, str],
        propagator_id: uuid.UUID,
    ) -> None:
        """
        Add an alias for a propagator.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :param propagator_id: Unique identifier for the propagator.
        """
        if alias_key not in self._key_alias:
            self._key_alias[alias_key] = set()
        self._key_alias[alias_key].add(propagator_id)

    def _remove_alias(
        self,
        alias_key: tuple[EventDomain, str],
        propagator_id: uuid.UUID,
    ) -> None:
        """
        Remove an alias for a propagator.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :param propagator_id: Unique identifier for the propagator.
        """
        if alias_key in self._key_alias:
            self._key_alias[alias_key].discard(propagator_id)
            if not self._key_alias[alias_key]:
                del self._key_alias[alias_key]

    async def shutdown(self) -> None:
        """
        Close all registered propagators.
        """
        for propagator_info in self._propagators.values():
            await propagator_info.propagator.close()
