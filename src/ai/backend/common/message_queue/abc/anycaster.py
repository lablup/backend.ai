from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractAnycaster(ABC):
    """
    Abstract interface for sending messages to queues (point-to-point delivery).
    Messages are delivered to exactly one consumer.
    """

    @abstractmethod
    async def anycast(self, payload: dict[bytes, bytes]) -> None:
        """
        Send a message to the anycast queue.

        Args:
            payload: Message payload as a dict of bytes

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the anycaster and cleanup resources.
        """
        raise NotImplementedError
