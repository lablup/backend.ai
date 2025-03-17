import abc


class AbstractSweeper(abc.ABC):
    @abc.abstractmethod
    async def sweep(self, *args) -> None:
        raise NotImplementedError
