import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import MutableMapping

from ai.backend.common.events.types import AbstractEvent, EventDomain
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
        :raises
            ValueError: If the alias is not found.
        :raises
            RuntimeError: If the propagator is already closed.
        """
        if (alias_domain, alias_id) not in self._key_alias:
            log.debug("Propagator not registered with alias {}:{}", alias_domain, alias_id)
            return

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
        :return: The propagator associated with the alias.
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
        :param alias_key: The key for the alias (e.g., (USER, "user_id")).
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
        :param alias_key: The key for the alias (e.g., (USER, "user_id")).
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
