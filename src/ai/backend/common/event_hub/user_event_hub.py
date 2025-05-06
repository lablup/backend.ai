import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import MutableMapping, Optional


class UserEvent(ABC):
    @abstractmethod
    def event_name(self) -> Optional[str]:
        """Get the name of the event."""
        raise NotImplementedError

    @abstractmethod
    def retry_count(self) -> Optional[int]:
        """Get the retry count for the event."""
        raise NotImplementedError

    @abstractmethod
    def serialize_user_event(self) -> str:
        """Serialize the user event to a dictionary."""
        raise NotImplementedError


class UserEventSender(ABC):
    @abstractmethod
    async def send_event(self, event: UserEvent) -> None:
        """Send an event to the event hub."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close the sender."""
        raise NotImplementedError


class AliasDomain(enum.StrEnum):
    """
    Enum for alias domains.
    """

    USER = "user"
    SESSION = "session"
    KERNEL = "kernel"
    BGTASK = "bg_task"


@dataclass
class SenderInfo:
    """
    Class to hold sender information.
    """

    sender: UserEventSender
    aliases: list[tuple[AliasDomain, uuid.UUID]]


class UserEventHub:
    _senders: MutableMapping[uuid.UUID, SenderInfo]
    _key_alias: MutableMapping[tuple[AliasDomain, uuid.UUID], set[uuid.UUID]]

    def __init__(self) -> None:
        self._senders = {}
        self._key_alias = {}

    def register_sender(
        self,
        sender_id: uuid.UUID,
        sender: UserEventSender,
        aliases: list[tuple[AliasDomain, uuid.UUID]] = [],
    ) -> None:
        """
        Register a new event sender
        :param sender_id: Unique identifier for the sender.
        :param sender: The sender instance implementing UserEventSender.
        :param aliases: List of aliases for the sender.
        :raises ValueError: If the sender is already registered.
        """
        if sender_id in self._senders:
            raise ValueError(f"Sender with ID {sender_id} already registered.")
        self._senders[sender_id] = SenderInfo(sender, aliases)
        for alias in aliases:
            if alias in self._key_alias:
                raise ValueError(f"Alias {alias} already registered.")
            self._add_alias(alias, sender_id)

    def unregister_sender(self, sender_id: uuid.UUID) -> None:
        """
        Unregister an event sender
        :param sender_id: Unique identifier for the sender.
        :raises ValueError: If the sender is not registered.
        """
        if sender_id not in self._senders:
            raise ValueError(f"Sender with ID {sender_id} not found.")
        sender_info = self._senders[sender_id]
        for alias in sender_info.aliases:
            if alias in self._key_alias:
                self._remove_alias(alias, sender_id)
        del self._senders[sender_id]

    async def send_event(self, sender_id: uuid.UUID, event: UserEvent) -> None:
        """
        Send an event using the specified sender.
        :param sender_id: Unique identifier for the sender.
        :param event: The event to be sent.
        :raises ValueError: If the sender is not registered.
        """
        if sender_id not in self._senders:
            raise ValueError(f"Sender with ID {sender_id} not found.")
        sender_info = self._senders[sender_id]
        await sender_info.sender.send_event(event)

    async def send_event_by_alias(
        self,
        alias_domain: AliasDomain,
        alias_id: uuid.UUID,
        event: UserEvent,
    ) -> None:
        """
        Send an event using the specified alias.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :param event: The event to be sent.
        """
        if (alias_domain, alias_id) not in self._key_alias:
            raise ValueError(f"Alias {alias_domain}:{alias_id} not found.")

        sender_set = self._key_alias[(alias_domain, alias_id)]
        for sender_id in sender_set:
            await self.send_event(sender_id, event)

    def _add_alias(
        self,
        alias_key: tuple[AliasDomain, uuid.UUID],
        sender_id: uuid.UUID,
    ) -> None:
        """
        Add an alias for a sender.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :param sender_id: Unique identifier for the sender.
        """
        if alias_key not in self._key_alias:
            self._key_alias[alias_key] = set()
        self._key_alias[alias_key].add(sender_id)

    def _remove_alias(
        self,
        alias_key: tuple[AliasDomain, uuid.UUID],
        sender_id: uuid.UUID,
    ) -> None:
        """
        Remove an alias for a sender.
        :param alias_domain: The domain of the alias (e.g., USER, SESSION, KERNEL).
        :param alias_id: The ID of the alias.
        :param sender_id: Unique identifier for the sender.
        """
        if alias_key in self._key_alias:
            self._key_alias[alias_key].discard(sender_id)
            if not self._key_alias[alias_key]:
                del self._key_alias[alias_key]
