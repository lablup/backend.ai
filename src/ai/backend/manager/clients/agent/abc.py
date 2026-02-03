"""
Abstract base classes for Backend.AI clients.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BackendAIClient(ABC):
    """Abstract base class for Backend.AI clients."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the server."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close connection to the server."""
        raise NotImplementedError
