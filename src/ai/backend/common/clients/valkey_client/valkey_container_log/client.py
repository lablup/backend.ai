import logging
from typing import (
    Optional,
    Self,
)

from glide import (
    Batch,
)

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.log.types import ContainerLogData
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_container_log client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_CONTAINER_LOG)


class ValkeyContainerLogClient:
    """
    Client for interacting with Valkey for container log operations using GlideClient.

    This client intentionally ignores server-side failures or connection failures in
    its log-related action methods so that crashes or failures of the container log
    subsystem would not impact the other parts of the system.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
        pubsub_channels: Optional[set[str]] = None,
    ) -> Self:
        """
        Create a ValkeyContainerLogClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyContainerLogClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(client=client)

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyContainerLogClient connection.
        """
        if self._closed:
            log.debug("ValkeyContainerLogClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch object for batch operations.

        :param is_atomic: Whether the batch should be atomic (transaction-like).
        :return: A Batch object.
        """
        return Batch(is_atomic=is_atomic)

    async def enqueue_container_logs(
        self,
        container_id: str,
        logs: ContainerLogData,
    ) -> None:
        """
        Enqueue logs for a specific container.
        TODO: Replace with a more efficient log storage solution.

        :param container_id: The ID of the container.
        :param logs: The logs to enqueue.
        :raises: GlideClientError if the logs cannot be enqueued.
        """
        key = self._container_log_key(container_id)
        tx = self._create_batch()
        tx.rpush(
            key,
            [logs.serialize()],
        )
        tx.expire(
            key,
            3600,  # 1 hour expiration
        )
        await self._client.client.exec(tx, raise_on_error=True)

    async def container_log_len(
        self,
        container_id: str,
    ) -> int:
        """
        Get the length of logs for a specific container.

        :param container_id: The ID of the container.
        :return: The number of logs for the container.
        :raises: GlideClientError if the length cannot be retrieved.
        """
        key = self._container_log_key(container_id)
        return await self._client.client.llen(key)

    async def pop_container_logs(
        self,
        container_id: str,
        count: int = 1,
    ) -> Optional[list[ContainerLogData]]:
        """
        Pop logs for a specific container.

        :param container_id: The ID of the container.
        :return: List of logs for the container.
        :raises: GlideClientError if the logs cannot be popped.
        """
        key = self._container_log_key(container_id)
        logs = await self._client.client.lpop_count(key, count)
        if logs is None:
            return None

        return [ContainerLogData.deserialize(log) for log in logs]

    async def clear_container_logs(
        self,
        container_id: str,
    ) -> None:
        """
        Clear logs for a specific container.

        :param container_id: The ID of the container.
        :raises: GlideClientError if the logs cannot be cleared.
        """
        key = self._container_log_key(container_id)
        await self._client.client.delete([key])

    def _container_log_key(self, container_id: str) -> str:
        return f"containerlog.{container_id}"
