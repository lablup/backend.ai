import logging
from collections.abc import Mapping
from typing import ParamSpec, Self, TypeVar, cast

from glide import Batch

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import AgentId, ImageCanonical, ImageID, ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Resilience instance for valkey_image layer
valkey_image_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_IMAGE)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

P = ParamSpec("P")
R = TypeVar("R")


class ValkeyImageClient:
    """
    Client for managing agent-image mappings using Valkey sets.
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
    ) -> Self:
        """
        Create a ValkeyImageClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :return: An instance of ValkeyImageClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_image_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyImageClient connection.
        """
        if self._closed:
            log.debug("ValkeyImageClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    @valkey_image_resilience.apply()
    async def add_agent_to_images(
        self,
        agent_id: str,
        image_ids: list[ImageID],
    ) -> None:
        """
        Add an agent to multiple image sets.

        :param agent_id: The agent ID to add.
        :param image_identifiers: List of image identifiers (canonical:arch).
        """
        if not image_ids:
            return

        tx = self._create_batch()
        for image_id in image_ids:
            tx.sadd(str(image_id), [agent_id])
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_image_resilience.apply()
    async def add_agent_installed_images(
        self,
        agent_id: AgentId,
        installed_image_info: list[InstalledImageInfo],
    ) -> None:
        """
        Add installed image info for an agent.

        :param agent_id: The agent ID to add.
        :param installed_image_info: list of installed image information
        """
        if not installed_image_info:
            return

        value = dump_json_str([img.model_dump() for img in installed_image_info])
        await self._client.client.set(key=f"installed_image:{agent_id}", value=value)

    @valkey_image_resilience.apply()
    async def get_agent_installed_images(
        self,
        agent_id: AgentId,
    ) -> list[InstalledImageInfo]:
        """
        Get installed image info for an agent.

        :param agent_id: The agent ID to get.
        :return: list of installed image information
        """
        value = await self._client.client.get(key=f"installed_image:{agent_id}")
        if value is None:
            return []

        json_value = value.decode()
        installed_image_dicts = load_json(json_value)
        return [InstalledImageInfo.model_validate(img_dict) for img_dict in installed_image_dicts]

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images instead of this if possible
    @valkey_image_resilience.apply()
    async def remove_agent_from_images_by_canonicals(
        self,
        agent_id: str,
        image_canonicals: list[ImageCanonical],
    ) -> None:
        """
        Remove an agent from multiple image sets.

        :param agent_id: The agent ID to remove.
        :param image_ids: List of image identifiers (Image ID).
        """
        if not image_canonicals:
            return

        tx = self._create_batch()
        for image_canonical in image_canonicals:
            tx.srem(str(image_canonical), [agent_id])
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_image_resilience.apply()
    async def remove_agent_from_images(
        self,
        agent_id: str,
        image_ids: list[ImageID],
    ) -> None:
        """
        Remove an agent from multiple image sets.

        :param agent_id: The agent ID to remove.
        :param image_ids: List of image identifiers (Image ID).
        """
        if not image_ids:
            return

        tx = self._create_batch()
        for image_id in image_ids:
            tx.srem(str(image_id), [agent_id])
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_image_resilience.apply()
    async def remove_agent_from_all_images(
        self,
        agent_id: str,
    ) -> None:
        """
        Remove an agent from all image sets.

        :param agent_id: The agent ID to remove.
        """
        cursor = b"0"
        keys_to_remove: list[bytes] = []
        while True:
            result = await self._client.client.scan(cursor)
            if len(result) != 2:
                raise ValueError(
                    f"Unexpected result from scan: {result}. Expected a tuple of (cursor, keys)."
                )
            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])
            keys_to_remove.extend(keys)
            if cursor == b"0":
                break
        if keys_to_remove:
            tx = self._create_batch()
            for key in keys_to_remove:
                tx.srem(key, [agent_id])
            await self._client.client.exec(tx, raise_on_error=True)

    @valkey_image_resilience.apply()
    async def get_agents_for_image(
        self,
        image_id: ImageID,
    ) -> set[AgentId]:
        """
        Get all agents that have a specific image.

        :param image_id: The image identifier.
        :return: Set of agent IDs.
        """
        result = await self._client.client.smembers(str(image_id))
        return {AgentId(member.decode()) for member in result}

    @valkey_image_resilience.apply()
    async def get_agents_for_images(
        self,
        image_ids: list[ImageID],
    ) -> Mapping[ImageID, set[AgentId]]:
        """
        Get all agents for multiple images.

        :param image_ids: List of image identifiers (UUID).
        :return: Mapping of image IDs to sets of agent IDs.
        """
        if not image_ids:
            return {}

        tx = self._create_batch()
        for image_id in image_ids:
            tx.smembers(str(image_id))

        results = await self._client.client.exec(tx, raise_on_error=True)
        final_results: dict[ImageID, set[AgentId]] = {}
        if not results:
            return final_results
        for image_id, result in zip(image_ids, results):
            result = cast(set[bytes], result)
            final_results[image_id] = {AgentId(member.decode()) for member in result}
        return final_results

    @valkey_image_resilience.apply()
    async def get_agent_counts_for_images(
        self,
        image_ids: list[ImageID],
    ) -> list[int]:
        """
        Get the count of agents for multiple images.

        :param image_ids: List of image identifiers (canonical:arch).
        :return: List of agent counts, one for each image.
        """
        if not image_ids:
            return []

        tx = self._create_batch()
        for image_id in image_ids:
            tx.scard(str(image_id))

        results = await self._client.client.exec(tx, raise_on_error=True)
        if not results:
            return []
        return [cast(int, result) for result in results]

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)
