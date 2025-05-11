from abc import ABC, abstractmethod


class AbstractObserver(ABC):
    """
    Abstract base class for observers.
    """

    def __init__(self):
        pass

    @abstractmethod
    async def observe(self) -> None:
        """
        Observe the state of the system.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def observe_interval(self) -> float:
        """
        Return the interval at which to observe the system.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def close(self) -> None:
        """
        Clean up resources used by the observer.
        """
        raise NotImplementedError("Subclasses must implement this method.")
