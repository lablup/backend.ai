from abc import ABC, abstractmethod


class AbstractObserver(ABC):
    """
    Abstract base class for observers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the observer.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def observe(self) -> None:
        """
        Observe the state of the system.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def observe_interval(self) -> float:
        """
        Return the interval at which to observe the system.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources used by the observer.
        """
        raise NotImplementedError("Subclasses must implement this method.")
