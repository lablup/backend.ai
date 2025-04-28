import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncGenerator

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from ai.backend.common.message_queue.queue import AbstractMessageQueue, MessageId, MQMessage
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class KafkaMessageQueueArgs:
    topic: str
    producer: AIOKafkaProducer
    consumer: AIOKafkaConsumer
    subscriber: AIOKafkaConsumer


class KafkaMessageQueue(AbstractMessageQueue):
    _topic: str
    _producer: AIOKafkaProducer
    _consumer: AIOKafkaConsumer
    _subscriber: AIOKafkaConsumer
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[MQMessage]
    _closed: bool
    _consumer_task: asyncio.Task
    _subscriber_task: asyncio.Task

    def __init__(
        self,
        args: KafkaMessageQueueArgs,
    ) -> None:
        self._topic = args.topic
        self._producer = args.producer
        self._consumer = args.consumer
        self._subscriber = args.subscriber
        self._consume_queue = asyncio.Queue[MQMessage]()
        self._subscribe_queue = asyncio.Queue[MQMessage]()
        self._closed = False

        # Start background tasks
        self._consumer_task = asyncio.create_task(self._consume_messages_loop())
        self._subscriber_task = asyncio.create_task(self._subscribe_messages_loop())

    async def _consume_messages_loop(self) -> None:
        """Background task that continuously reads messages for consumers"""
        log.debug("Starting consumer loop for topic {}", self._topic)
        try:
            while not self._closed:
                message = await self._consumer.getone()
                msg = MQMessage(
                    msg_id=str(message.offset).encode(),
                    payload=message.value,
                )
                await self._consume_queue.put(msg)
        except Exception as e:
            if not self._closed:
                log.error("Error in consumer loop: {}", e)

    async def _subscribe_messages_loop(self) -> None:
        """Background task that continuously reads messages for subscribers"""
        log.debug("Starting subscriber loop for topic {}", self._topic)
        try:
            while not self._closed:
                message = await self._subscriber.getone()
                msg = MQMessage(
                    msg_id=str(message.offset).encode(),
                    payload=message.value,
                )
                await self._subscribe_queue.put(msg)
        except Exception as e:
            if not self._closed:
                log.error("Error in subscriber loop: {}", e)

    async def send(self, payload: dict[bytes, bytes]) -> None:
        if self._closed:
            raise RuntimeError("Queue is closed")
        try:
            await self._producer.send(
                self._topic,
                value=payload,
            )
        except KafkaError as e:
            raise RuntimeError(f"Failed to send message: {e}")

    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore
        if self._closed:
            return
        while not self._closed:
            try:
                yield await self._consume_queue.get()
            except asyncio.CancelledError:
                break

    async def subscribe_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore
        if self._closed:
            return
        while not self._closed:
            try:
                yield await self._subscribe_queue.get()
            except asyncio.CancelledError:
                break

    async def done(self, msg_id: MessageId) -> None:
        # Kafka handles message acknowledgment automatically
        pass

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._consumer_task.cancel()
        self._subscriber_task.cancel()
