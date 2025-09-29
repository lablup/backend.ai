from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Final, MutableMapping

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.metrics.metric import EventPropagatorMetricObserver
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

WILDCARD: Final = "*"


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
    _wildcard_alias: MutableMapping[EventDomain, set[uuid.UUID]]
    _metric_observer: EventPropagatorMetricObserver

    def __init__(self) -> None:
        self._propagators = {}
        self._key_alias = defaultdict(set)
        self._wildcard_alias = defaultdict(set)
        self._metric_observer = EventPropagatorMetricObserver.instance()

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

        # Track metrics
        metric_aliases = [(alias[0].value, alias[1]) for alias in aliases]
        self._metric_observer.observe_propagator_registered(aliases=metric_aliases)

    def unregister_event_propagator(self, propagator_id: uuid.UUID) -> None:
        """
        Unregister an event propagator.
        :param propagator_id: Unique identifier for the propagator.
        :raises ValueError: If the propagator is not registered.
        """
        if propagator_id not in self._propagators:
            raise ValueError(f"propagator with ID {propagator_id} not found.")
        propagator_info = self._propagators[propagator_id]

        # Collect aliases for metrics
        metric_aliases = []
        for alias in propagator_info.aliases:
            self._remove_alias(alias, propagator_id)
            metric_aliases.append((alias[0].value, alias[1]))
        del self._propagators[propagator_id]

        # Track metrics
        self._metric_observer.observe_propagator_unregistered(aliases=metric_aliases)

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
        domain_id: str,
    ) -> None:
        """
        Close all propagators associated with the specified alias.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param domain_id: The target ID within the alias domain.
        :raises ValueError: If the alias is not found.
        :raises RuntimeError: If the propagator is already closed.
        """
        propagator_id_set: set[uuid.UUID] = set()
        if domain_id == WILDCARD:
            propagator_id_set.update(self._wildcard_alias.get(alias_domain, []))
        else:
            propagator_id_set.update(self._key_alias.get((alias_domain, domain_id), []))
        for propagator_id in propagator_id_set:
            if (info := self._propagators.get(propagator_id)) is not None:
                await info.propagator.close()

    def _get_propagators_by_alias(
        self,
        alias_domain: EventDomain,
        domain_id: str,
    ) -> set[EventPropagator]:
        """
        Get the propagator associated with the specified alias.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param domain_id: The target ID within the alias domain.
        :return: The propagator associated with the alias.
        """
        propagators: set[EventPropagator] = set()
        propagators.update(
            info.propagator
            for propagator_id in self._wildcard_alias.get(alias_domain, [])
            if (info := self._propagators.get(propagator_id)) is not None
        )
        propagators.update(
            info.propagator
            for propagator_id in self._key_alias.get((alias_domain, domain_id), [])
            if (info := self._propagators.get(propagator_id)) is not None
        )
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
        if alias_key[1] == WILDCARD:
            self._wildcard_alias[alias_key[0]].add(propagator_id)
        else:
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
        if alias_key[1] == WILDCARD:
            domain = alias_key[0]
            if domain in self._wildcard_alias:
                self._wildcard_alias[domain].discard(propagator_id)
                if not self._wildcard_alias[domain]:
                    del self._wildcard_alias[domain]
        else:
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
