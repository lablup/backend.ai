from abc import ABC, abstractmethod


class AbstractResource(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def setup(self) -> None:
        """
        Set up the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def release(self) -> None:
        """
        Release the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")
