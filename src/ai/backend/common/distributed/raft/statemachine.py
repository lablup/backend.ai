import abc

from ...types import aobject


class AbstractStateMachine(abc.ABC):
    @abc.abstractmethod
    async def execute(self, command: str) -> None:
        raise NotImplementedError()


class ExecStateMachine(AbstractStateMachine):
    async def execute(self, command: str) -> None:
        exec(command)


class RedisStateMachine(aobject, AbstractStateMachine):
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __ainit__(self, *args, **kwargs) -> None:
        pass

    async def execute(self, command: str) -> None:
        pass
