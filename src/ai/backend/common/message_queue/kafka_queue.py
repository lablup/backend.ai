import asyncio
import json
from typing import AsyncGenerator

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .base import AbstractMessageQueue, AbstractMQMessagePayload, MQMessage


class KafkaQueue(AbstractMessageQueue):
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id

        self.producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)

        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
        )

        self.broadcast_consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=f"broadcast-{group_id}-{id(self)}",
            auto_offset_reset="earliest",
        )
        self._started = False

    async def _start(self) -> None:
        if not self._started:
            await self.producer.start()
            await self.consumer.start()
            await self.broadcast_consumer.start()
            self._started = True

    async def send(self, key: str, msg: AbstractMQMessagePayload) -> None:
        await self._start()
        payload_dict = msg.serialize()
        payload = {k.decode("utf-8"): v.decode("utf-8") for k, v in payload_dict.items()}
        data = json.dumps(payload).encode("utf-8")
        await self.producer.send_and_wait(self.topic, data, key=key.encode("utf-8"))

    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:
        async def generator() -> AsyncGenerator[MQMessage, None]:
            await self._start()
            try:
                while True:
                    kafka_msg = await self.consumer.getone()
                    msg_id = f"{kafka_msg.topic}-{kafka_msg.partition}-{kafka_msg.offset}"
                    if kafka_msg.value is None:
                        raise ValueError("Received Kafka message with no value")
                    payload = AbstractMQMessagePayload.deserialize(kafka_msg.value)
                    yield MQMessage(msg_id, payload)
            except asyncio.CancelledError:
                return

        return generator()

    async def subscribe_queue(self) -> AsyncGenerator[MQMessage, None]:
        async def generator() -> AsyncGenerator[MQMessage, None]:
            await self._start()
            try:
                while True:
                    kafka_msg = await self.broadcast_consumer.getone()
                    msg_id = f"{kafka_msg.topic}-{kafka_msg.partition}-{kafka_msg.offset}"
                    if kafka_msg.value is None:
                        raise ValueError("Received Kafka message with no value")
                    payload = AbstractMQMessagePayload.deserialize(kafka_msg.value)
                    yield MQMessage(msg_id, payload)
            except asyncio.CancelledError:
                return

        return generator()

    async def done(self, msg: MQMessage) -> None:
        pass

    async def close(self) -> None:
        await self.producer.stop()
        await self.consumer.stop()
        await self.broadcast_consumer.stop()
