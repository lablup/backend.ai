
from typing import AsyncGenerator
from .base import AbstractMessageQueue, MQMessage, AbstractMQMessagePayload


class KafkaQueue(AbstractMessageQueue):
    def __init__(self) -> None:
        pass

    async def send(self, key: str, msg: AbstractMQMessagePayload) -> None:
        ...
    
    async def consume_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]: ...

    async def subscribe_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]: ...

    async def done(self, msg: MQMessage) -> None:
        ...
    
    async def close(self) -> None:
        ...
