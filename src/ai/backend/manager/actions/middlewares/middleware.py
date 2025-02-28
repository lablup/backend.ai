
from abc import ABC

from ..action import BaseAction, ProcessResult


class ActionMiddleware(ABC):
    async def prepare(self, action: BaseAction) -> None:
        pass

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        pass
