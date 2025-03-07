import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from ai.backend.common.message_queue.base import AbstractMessageQueue, MQMessage
from ai.backend.common.types import KafkaConnectionInfo


class KafkaMessageQueue(AbstractMessageQueue):
    def __init__(self, kafka_connection_info: KafkaConnectionInfo):
        self.connection_info = kafka_connection_info
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._group_consumer: Optional[AIOKafkaConsumer] = None
        self._log = logging.getLogger(__name__)

    async def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.connection_info.bootstrap_servers,
                client_id=self.connection_info.client_id,
            )
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.connection_info.bootstrap_servers,
                    client_id=self.connection_info.client_id,
                )
                await self._producer.start()
        return self._producer

    async def _get_consumer(self, stream_key: str) -> AIOKafkaConsumer:
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                stream_key,
                bootstrap_servers=self.connection_info.bootstrap_servers,
                group_id=self.connection_info.group_id,
                client_id=self.connection_info.client_id,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
            )
            await self._consumer.start()
        return self._consumer

    async def receive(
        self,
        stream_key: str,
        *,
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]:
        async def generator():
            if not self._consumer:
                self._consumer = AIOKafkaConsumer(
                    stream_key,
                    bootstrap_servers=self.connection_info.bootstrap_servers,
                    security_protocol=self.connection_info.security_protocol,
                    enable_auto_commit=False
                )
                await self._consumer.start()
            try:
                while True:
                    msgs_by_topic = await self._consumer.getmany(timeout_ms=block_timeout)

                    if not msgs_by_topic: # no messages
                        continue

                    for tp, msgs in msgs_by_topic.items():
                        for msg in msgs:
                            try:
                                payload = json.loads(msg.value) if msg.value is not None else None
                            except (json.JSONDecodeError, TypeError):
                                payload = msg.value

                            message =  MQMessage(
                                topic=msg.topic,
                                payload=payload if payload is not None else {},
                                metadata={
                                    "partition": msg.partition,
                                    "offset": msg.offset
                                }
                            )
                            yield message
            except asyncio.CancelledError:
                raise
            finally:
                pass # let close handle the cleanup

        return generator()

    async def receive_group(
        self,
        stream_key: str,
        group_name: str,
        consumer_id: str,
        *,
        autoclaim_idle_timeout: int = 1_000,  # in msec
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]:
        async def generator():
            if not self._group_consumer:
                self._group_consumer = AIOKafkaConsumer(
                    stream_key,
                    group_id=group_name,
                    client_id=consumer_id,
                    bootstrap_servers=self.connection_info.bootstrap_servers,
                    security_protocol=self.connection_info.security_protocol,
                    enable_auto_commit=False
                )
                await self._group_consumer.start()

            try:
                while True:
                    msgs_by_topic = await self._group_consumer.getmany(timeout_ms=block_timeout)
                    if not msgs_by_topic:
                        continue

                    for tp, msgs in msgs_by_topic.items():
                        for msg in msgs:
                            try:
                                payload = json.loads(msg.value) if msg.value is not None else None
                            except (json.JSONDecodeError, TypeError):
                                payload = msg.value

                            yield MQMessage(
                                topic=msg.topic,
                                payload=payload if payload is not None else {},
                                metadata={
                                    "partition": msg.partition,
                                    "offset": msg.offset
                                }
                            )
            except asyncio.CancelledError:
                raise
            finally:
                pass
        return generator()

    async def send(
        self,
        msg: MQMessage,
        *,
        is_flush: bool = False,
        service_name: Optional[str] = None,
        encoding: Optional[str] = None,
        command_timeout: Optional[float] = None,
    ) -> None:
        if is_flush:
            await self._flush_kafka_topic(self.connection_info.topic)
            return

        if not self._producer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.connection_info.bootstrap_servers,
                client_id=self.connection_info.client_id,
            )
            await self._producer.start()

        payload = msg.payload
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        elif isinstance(payload, str):
            payload = payload.encode('utf-8')
        elif not isinstance(payload, (bytes, bytearray)):
            payload = str(payload).encode('utf-8')

        await self._producer.send_and_wait(msg.topic, payload)

    async def _flush_kafka_topic(self, topic: str) -> None:
        try:
            await self._set_topic_retention(topic, 0)
            await asyncio.sleep(1) # wait for retention to take effect
            await self._set_topic_retention(topic, 604800000)  #restore default retention
        except Exception as e:
            self._log.error(f"Failed to set topic retention to 0: {e}")
            await self._send_tombstone_message(topic)

    async def _set_topic_retention(self, topic: str, retention_ms: int) -> None:
        from aiokafka.admin import AIOKafkaAdminClient
        from aiokafka.admin.config_resource import ConfigResource, ConfigResourceType

        admin_client = AIOKafkaAdminClient(bootstrap_servers=self.connection_info.bootstrap_servers)
        await admin_client.start()

        try:
            await admin_client.alter_configs(
                config_resources=[ConfigResource(resource_type=ConfigResourceType.TOPIC, name=topic, configs={"retention.ms": str(retention_ms)})]
            )
        finally:
            await admin_client.close()

    async def _send_tombstone_message(self, topic: str) -> None:
        if not self._producer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.connection_info.bootstrap_servers,
                client_id=self.connection_info.client_id,
            )
            await self._producer.start()

        await self._producer.send_and_wait(topic, None)  # Null payload = tombstone


    async def close(self, close_connection_pool: Optional[bool] = None) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
        if self._group_consumer:
            await self._group_consumer.stop()
            self._group_consumer = None
