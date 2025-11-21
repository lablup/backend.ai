import json
import logging
from collections.abc import Mapping
from typing import (
    Any,
    Final,
    Optional,
    Self,
    Sequence,
    Union,
    cast,
)

from glide import (
    Batch,
    ExpirySet,
    ExpiryType,
)
from msgpack.exceptions import ExtraData, UnpackException

from ai.backend.common import msgpack
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import AccessKey, ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_stat client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_STAT)

_DEFAULT_EXPIRATION = 86400  # 24 hours default expiration
_KEYPAIR_CONCURRENCY_PREFIX: Final[str] = "keypair.concurrency_used"
_KEYPAIR_SFTP_CONCURRENCY_PREFIX: Final[str] = "keypair.sftp_concurrency_used"
_KERNEL_COMMIT_PREFIX: Final[str] = "kernel"
_KERNEL_COMMIT_SUFFIX: Final[str] = "commit"
_ABUSE_REPORT_HASH: Final[str] = "abuse_report"
_CONTAINER_COUNT_PREFIX: Final[str] = "container_count"
_MANAGER_STATUS_PREFIX: Final[str] = "manager.status"
_INFERENCE_PREFIX: Final[str] = "inference"
_COMPUTER_METADATA_KEY: Final[str] = "computer.metadata"
_COMPUTE_CONCURRENCY_USED_KEY_PREFIX: Final[str] = "keypair.concurrency_used."
_SYSTEM_CONCURRENCY_USED_KEY_PREFIX: Final[str] = "keypair.sftp_concurrency_used."
_TOTAL_RESOURCE_SLOTS_KEY: Final[str] = "system.total_resource_slots"


class ValkeyStatClient:
    """
    Client for interacting with Valkey for statistics operations using GlideClient.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
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
        Create a ValkeyStatClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name for the client.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyStatClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(
            client=client,
        )

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyStatClient connection.
        """
        if self._closed:
            log.debug("ValkeyStatClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_decorator()
    async def get_keypair_query_count(self, access_key: str) -> int:
        """
        Get API query count for a keypair.

        :param access_key: The keypair access key.
        :return: The query count, or 0 if not found.
        """
        result = await self._client.client.get(self._get_keypair_query_count_key(access_key))
        if result is None:
            return 0
        try:
            return int(result.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return 0

    @valkey_decorator()
    async def get_keypair_concurrency_used(
        self, access_key: str, is_private: bool = False
    ) -> Optional[int]:
        """
        Get current concurrency usage for a keypair.

        :param access_key: The keypair access key.
        :param is_private: Whether to get SFTP concurrency (True) or regular concurrency (False).
        :return: The concurrency usage count, or None if not found in cache.
        """
        key = self._get_keypair_concurrency_key(access_key, is_private)
        result = await self._client.client.get(key)
        if result is None:
            return None
        try:
            return int(result.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    @valkey_decorator()
    async def get_keypair_last_used_time(self, access_key: str) -> Optional[float]:
        """
        Get last API call timestamp for a keypair.

        :param access_key: The keypair access key.
        :return: The timestamp as float, or None if not found.
        """
        result = await self._client.client.get(self._get_keypair_last_call_time_key(access_key))
        if result is None:
            return None
        try:
            return float(result.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    @valkey_decorator()
    async def get_gpu_allocation_map(self, agent_id: str) -> Optional[dict[str, float]]:
        """
        Get GPU allocation mapping for an agent.

        :param agent_id: The agent ID.
        :return: GPU allocation map as dict, or None if not found.
        """
        result = await self._client.client.get(f"gpu_alloc_map.{agent_id}")
        if result is None:
            return None
        try:
            return json.loads(result)
        except (json.JSONDecodeError, UnicodeDecodeError):
            log.warning(
                "Failed to decode GPU allocation map for agent {}: {}",
                agent_id,
                result.decode("utf-8"),
            )
            return None

    @valkey_decorator()
    async def get_kernel_statistics(self, kernel_id: str) -> Optional[dict[str, Any]]:
        """
        Get kernel utilization statistics.

        :param kernel_id: The kernel ID.
        :return: Kernel statistics as dict, or None if not found.
        """
        result = await self._client.client.get(str(kernel_id))
        if result is None:
            return None
        try:
            return msgpack.unpackb(result, raw=False)
        except (ExtraData, UnpackException, ValueError):
            log.warning(
                "Failed to unpack kernel statistics for ID {}: {}",
                kernel_id,
                result.decode("utf-8"),
            )
            return None

    def _get_kernel_commit_key(self, kernel_id: str) -> str:
        """
        Generate kernel commit status key.

        :param kernel_id: The kernel ID.
        :return: The generated key.
        """
        return f"{_KERNEL_COMMIT_PREFIX}.{kernel_id}.{_KERNEL_COMMIT_SUFFIX}"

    def _get_container_count_key(self, agent_id: str) -> str:
        """
        Generate container count key for an agent.

        :param agent_id: The agent ID.
        :return: The generated key.
        """
        return f"{_CONTAINER_COUNT_PREFIX}.{agent_id}"

    @valkey_decorator()
    async def get_kernel_commit_statuses(self, kernel_ids: list[str]) -> list[Optional[bytes]]:
        """
        Get commit statuses for multiple kernels efficiently.

        :param kernel_ids: List of kernel IDs to get commit statuses for.
        :return: List of commit status bytes, one for each kernel.
        """
        if not kernel_ids:
            return []

        keys = [self._get_kernel_commit_key(kernel_id) for kernel_id in kernel_ids]
        return await self._get_multiple_keys(keys)

    @valkey_decorator()
    async def get_abuse_report(self, kernel_id: str) -> Optional[str]:
        """
        Get abuse report for a specific kernel.

        :param kernel_id: The kernel ID to get abuse report for.
        :return: The abuse report string for the kernel, or None if not found.
        """
        result = await self._client.client.hget(_ABUSE_REPORT_HASH, kernel_id)
        if result is None:
            return None
        try:
            return result.decode("utf-8")
        except UnicodeDecodeError:
            return None

    @valkey_decorator()
    async def set_agent_container_count(self, agent_id: str, container_count: int) -> None:
        """
        Set the current container count for an agent.

        :param agent_id: The agent ID.
        :param container_count: The number of containers currently running on the agent.
        """
        # TODO: If Agent ID is changed, a leak may occur. (expire is needed)
        key = self._get_container_count_key(agent_id)
        await self._client.client.set(
            key, str(container_count), expiry=ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION)
        )

    @valkey_decorator()
    async def get_session_statistics_batch(self, session_ids: list[str]) -> list[Optional[dict]]:
        """
        Get statistics for multiple sessions efficiently.

        :param session_ids: List of session IDs to get statistics for.
        :return: List of session statistics, with None for non-existent sessions.
        """
        if not session_ids:
            return []

        results = await self._get_multiple_keys(session_ids)
        stats: list[Optional[dict]] = []
        for i, result in enumerate(results):
            if result is None:
                stats.append(None)
                continue
            try:
                stats.append(msgpack.unpackb(result))
            except (
                ExtraData,
                UnpackException,
                ValueError,
            ):
                log.warning(
                    "Failed to unpack session statistics for ID {}: {}",
                    session_ids[i],
                    result.decode("utf-8"),
                )
                stats.append(None)
        return stats

    @valkey_decorator()
    async def get_user_kernel_statistics_batch(
        self, kernel_ids: list[str]
    ) -> list[Optional[bytes]]:
        """
        Get raw kernel statistics for multiple kernels for user service operations.

        :param kernel_ids: List of kernel IDs to get statistics for.
        :return: List of raw kernel statistics bytes, with None for non-existent kernels.
        """
        return await self._get_multiple_keys(kernel_ids)

    @valkey_decorator()
    async def get_agent_statistics_batch(self, agent_ids: list[str]) -> list[Optional[dict]]:
        """
        Get agent statistics for multiple agents.

        :param agent_ids: List of agent IDs to get statistics for.
        :return: List of agent statistics, with None for non-existent agents.
        """
        results = await self._get_multiple_keys(agent_ids)
        stats: list[Optional[dict]] = []
        for i, result in enumerate(results):
            if result is None:
                stats.append(None)
                continue
            try:
                stats.append(msgpack.unpackb(result, ext_hook_mapping=msgpack.uuid_to_str))
            except (
                ExtraData,
                UnpackException,
                ValueError,
            ):
                log.warning(
                    "Failed to unpack agent statistics for ID {}: {}",
                    agent_ids[i],
                    result.decode("utf-8"),
                )
                stats.append(None)
        return stats

    @valkey_decorator()
    async def get_agent_container_counts_batch(self, agent_ids: list[str]) -> list[int]:
        """
        Get container counts for multiple agents.

        :param agent_ids: List of agent IDs to get container counts for.
        :return: List of container counts, with 0 for non-existent agents.
        """
        if not agent_ids:
            return []

        keys = [self._get_container_count_key(agent_id) for agent_id in agent_ids]
        results = await self._get_multiple_keys(keys)

        counts = []
        for i, result in enumerate(results):
            if result is None:
                counts.append(0)
                continue
            try:
                counts.append(int(result.decode("utf-8")))
            except (ValueError, UnicodeDecodeError):
                log.warning(
                    "Failed to decode container count for key {}: {}",
                    keys[i],
                    result.decode("utf-8"),
                )
                counts.append(0)
        return counts

    def _get_manager_status_key(self, node_id: str, pid: int) -> str:
        """
        Generate manager status key.

        :param node_id: The node ID.
        :param pid: The process ID.
        :return: The generated key.
        """
        return f"{_MANAGER_STATUS_PREFIX}.{node_id}:{pid}"

    @valkey_decorator()
    async def set_manager_status(
        self, node_id: str, pid: int, status_data: bytes, lifetime: int
    ) -> None:
        """
        Set manager status with expiration.

        :param node_id: The node ID.
        :param pid: The process ID.
        :param status_data: The status data to set.
        :param lifetime: The expiration time in seconds.
        """
        key = self._get_manager_status_key(node_id, pid)
        await self._client.client.set(
            key=key,
            value=status_data,
            expiry=ExpirySet(ExpiryType.SEC, lifetime),
        )

    def _get_inference_app_key(self, endpoint_id: str) -> str:
        """
        Generate inference app key for an endpoint.

        :param endpoint_id: The endpoint ID.
        :return: The generated key.
        """
        return f"{_INFERENCE_PREFIX}.{endpoint_id}.app"

    @valkey_decorator()
    async def get_inference_app_statistics_batch(
        self, endpoint_ids: list[str]
    ) -> list[Optional[dict]]:
        """
        Get inference app statistics for multiple endpoints.

        :param endpoint_ids: List of endpoint IDs to get statistics for.
        :return: List of inference app statistics, with None for non-existent endpoints.
        """
        if not endpoint_ids:
            return []

        keys = [self._get_inference_app_key(endpoint_id) for endpoint_id in endpoint_ids]
        results = await self._get_multiple_keys(keys)

        stats: list[Optional[dict]] = []
        for i, result in enumerate(results):
            if result is None:
                stats.append(None)
                continue
            try:
                stats.append(msgpack.unpackb(result))
            except (
                ExtraData,
                UnpackException,
                ValueError,
            ):
                log.warning(
                    "Failed to unpack inference app statistics for key {}: {}",
                    keys[i],
                    result.decode("utf-8"),
                )
                stats.append(None)
        return stats

    def _get_inference_replica_key(self, endpoint_id: str, replica_id: str) -> str:
        """
        Generate inference replica key.

        :param endpoint_id: The endpoint ID.
        :param replica_id: The replica ID.
        :return: The generated key.
        """
        return f"{_INFERENCE_PREFIX}.{endpoint_id}.replica.{replica_id}"

    @valkey_decorator()
    async def get_inference_replica_statistics_batch(
        self, endpoint_replica_pairs: list[tuple[str, str]]
    ) -> list[Optional[dict]]:
        """
        Get inference replica statistics for multiple endpoint-replica pairs.

        :param endpoint_replica_pairs: List of (endpoint_id, replica_id) tuples.
        :return: List of inference replica statistics, with None for non-existent entries.
        """
        if not endpoint_replica_pairs:
            return []

        keys = [
            self._get_inference_replica_key(endpoint_id, replica_id)
            for endpoint_id, replica_id in endpoint_replica_pairs
        ]
        results = await self._get_multiple_keys(keys)

        stats: list[Optional[dict]] = []
        for i, result in enumerate(results):
            if result is None:
                stats.append(None)
                continue
            try:
                stats.append(msgpack.unpackb(result))
            except (
                ExtraData,
                UnpackException,
                ValueError,
            ):
                log.warning(
                    "Failed to unpack inference replica statistics for key {}: {}",
                    keys[i],
                    result.decode("utf-8"),
                )
                stats.append(None)
        return stats

    @valkey_decorator()
    async def get_image_distro(self, image_id: str) -> Optional[str]:
        """
        Get cached Linux distribution for a Docker image.

        :param image_id: The Docker image ID.
        :return: The distribution name, or None if not found.
        """
        batch = self._create_batch()
        key = f"image:{image_id}:distro"
        batch.get(key)
        batch.expire(key, _DEFAULT_EXPIRATION)
        results = await self._client.client.exec(batch, raise_on_error=True)
        if not results:
            return None
        try:
            result = cast(Optional[bytes], results[0])
            if not result:
                return None
            return result.decode("utf-8")
        except UnicodeDecodeError:
            return None

    @valkey_decorator()
    async def set_image_distro(self, image_id: str, distro: str) -> None:
        """
        Cache Linux distribution for a Docker image.

        :param image_id: The Docker image ID.
        :param distro: The Linux distribution name.
        """
        await self._client.client.set(
            f"image:{image_id}:distro",
            distro,
            expiry=ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION),
        )

    @valkey_decorator()
    async def get_volume_usage(self, proxy_name: str, volume_name: str) -> Optional[bytes]:
        """
        Get volume usage information.

        :param proxy_name: The proxy name.
        :param volume_name: The volume name.
        :return: Volume usage data as dict, or None if not found.
        """
        return await self._client.client.get(f"volume.usage.{proxy_name}.{volume_name}")

    @valkey_decorator()
    async def set_volume_usage(
        self,
        proxy_name: str,
        volume_name: str,
        usage_data: bytes,
        expiry_seconds: int,
    ) -> None:
        """
        Set volume usage information with expiration.

        :param proxy_name: The proxy name.
        :param volume_name: The volume name.
        :param usage_data: The volume usage data to cache.
        :param expiry_seconds: The expiration time in seconds.
        """
        expiry = ExpirySet(ExpiryType.SEC, expiry_seconds)
        await self._client.client.set(
            f"volume.usage.{proxy_name}.{volume_name}", usage_data, expiry=expiry
        )

    @valkey_decorator()
    async def store_computer_metadata(
        self,
        metadata: Mapping[str, bytes],
    ) -> None:
        """
        Store computer metadata in the hash.

        :param metadata: Dictionary of metadata to store.
        """
        # TODO: Changed to allow setting expiration using the `set` method instead of the `hset` method.
        await self._client.client.hset(
            _COMPUTER_METADATA_KEY, cast(Mapping[str | bytes, str | bytes], metadata)
        )

    @valkey_decorator()
    async def get_computer_metadata(self) -> dict[str, bytes]:
        """
        Get all computer metadata from the hash.

        :return: Dictionary of slot name to metadata JSON string.
        """
        result = await self._client.client.hgetall(_COMPUTER_METADATA_KEY)
        if result is None:
            return {}

        # Convert bytes keys and values to strings
        metadata: dict[str, bytes] = {}
        for key, value in result.items():
            str_key: str = key.decode("utf-8")
            metadata[str_key] = value
        return metadata

    @valkey_decorator()
    async def _get_raw(self, key: str) -> Optional[bytes]:
        """
        Get raw value by key (internal use only for testing).

        :param key: The key to retrieve.
        :return: The value, or None if the key doesn't exist.
        """
        return await self._client.client.get(key)

    # Resource preset cache methods
    def _get_resource_preset_id_key(self, preset_id: str) -> str:
        """Generate resource preset key by ID."""
        return f"resource_preset:id:{preset_id}"

    def _get_resource_preset_name_key(self, name: str) -> str:
        """Generate resource preset key by name."""
        return f"resource_preset:name:{name}"

    def _get_resource_preset_list_key(self, scaling_group: Optional[str] = None) -> str:
        """Generate resource preset list key."""
        return f"resource_preset:list:{scaling_group or '_global_'}"

    def _get_resource_preset_check_key(
        self, access_key: str, group: str, domain: str, scaling_group: Optional[str] = None
    ) -> str:
        """Generate resource preset check key."""
        return f"resource_preset:check:{access_key}:{group}:{domain}:{scaling_group or '_any_'}"

    @valkey_decorator()
    async def get_resource_preset_by_id(self, preset_id: str) -> Optional[bytes]:
        """
        Get cached resource preset data by ID.

        :param preset_id: The preset ID.
        :return: The cached data, or None if not found.
        """
        key = self._get_resource_preset_id_key(preset_id)
        return await self._client.client.get(key)

    @valkey_decorator()
    async def get_resource_preset_by_name(self, name: str) -> Optional[bytes]:
        """
        Get cached resource preset data by name.

        :param name: The preset name.
        :return: The cached data, or None if not found.
        """
        key = self._get_resource_preset_name_key(name)
        return await self._client.client.get(key)

    @valkey_decorator()
    async def get_resource_preset_list(
        self, scaling_group: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get cached resource preset list.

        :param scaling_group: The scaling group name.
        :return: The cached data, or None if not found.
        """
        key = self._get_resource_preset_list_key(scaling_group)
        return await self._client.client.get(key)

    @valkey_decorator()
    async def get_resource_preset_check_data(
        self, access_key: str, group: str, domain: str, scaling_group: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get cached resource preset check data.

        :param access_key: The access key.
        :param group: The group name.
        :param domain: The domain name.
        :param scaling_group: The scaling group name.
        :return: The cached data, or None if not found.
        """
        key = self._get_resource_preset_check_key(access_key, group, domain, scaling_group)
        return await self._client.client.get(key)

    @valkey_decorator()
    async def set_resource_preset_by_id_and_name(
        self, preset_id: str, name: str, value: bytes, expire_sec: int = 60
    ) -> None:
        """
        Cache resource preset data by both ID and name.

        :param preset_id: The preset ID.
        :param name: The preset name.
        :param value: The data to cache.
        :param expire_sec: Expiration time in seconds (default 60).
        """
        batch = self._create_batch()

        # Set by ID
        id_key = self._get_resource_preset_id_key(preset_id)
        batch.set(id_key, value, expiry=ExpirySet(ExpiryType.SEC, expire_sec))

        # Set by name
        name_key = self._get_resource_preset_name_key(name)
        batch.set(name_key, value, expiry=ExpirySet(ExpiryType.SEC, expire_sec))

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def set_resource_preset_list(
        self, scaling_group: Optional[str], value: bytes, expire_sec: int = 60
    ) -> None:
        """
        Cache resource preset list.

        :param scaling_group: The scaling group name.
        :param value: The data to cache.
        :param expire_sec: Expiration time in seconds (default 60).
        """
        key = self._get_resource_preset_list_key(scaling_group)
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expire_sec),
        )

    @valkey_decorator()
    async def set_resource_preset_check_data(
        self,
        access_key: str,
        group: str,
        domain: str,
        scaling_group: Optional[str],
        value: bytes,
        expire_sec: int = 60,
    ) -> None:
        """
        Cache resource preset check data.

        :param access_key: The access key.
        :param group: The group name.
        :param domain: The domain name.
        :param value: The data to cache.
        :param scaling_group: The scaling group name.
        :param expire_sec: Expiration time in seconds (default 60).
        """
        key = self._get_resource_preset_check_key(access_key, group, domain, scaling_group)
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expire_sec),
        )

    @valkey_decorator()
    async def delete_resource_preset(
        self, preset_id: Optional[str] = None, name: Optional[str] = None
    ) -> int:
        """
        Delete resource preset cache by ID and/or name.

        :param preset_id: The preset ID.
        :param name: The preset name.
        :return: Number of keys that were deleted.
        """
        keys_to_delete: list[str | bytes] = []
        if preset_id:
            keys_to_delete.append(self._get_resource_preset_id_key(preset_id))
        if name:
            keys_to_delete.append(self._get_resource_preset_name_key(name))

        if not keys_to_delete:
            return 0
        return await self._client.client.delete(keys_to_delete)

    async def invalidate_all_resource_presets(self) -> None:
        """
        Invalidate all resource preset caches by scanning and deleting all preset-related keys.
        This includes keys for ID, name, list, and check data.
        """
        # Scan for all preset-related keys
        patterns = [
            "resource_preset:id:*",
            "resource_preset:name:*",
            "resource_preset:list:*",
            "resource_preset:check:*",
        ]

        all_keys: list[bytes] = []
        for pattern in patterns:
            keys = await self._keys(pattern)
            all_keys.extend(keys)

        # Delete all keys in batch
        if all_keys:
            batch = self._create_batch()
            batch = self._invalidate_resource_presets(batch, all_keys)
            await self._client.client.exec(batch, raise_on_error=True)

    # TODO: Remove this too generalized methods
    @valkey_decorator()
    async def set(
        self,
        key: str,
        value: bytes,
        expire_sec: Optional[int] = None,
    ) -> None:
        """
        Set the value of a key with optional expiration.

        :param key: The key to set.
        :param value: The value to set.
        :param expire_sec: Expiration time in seconds. If None, uses default expiration.
        """
        expiration = expire_sec if expire_sec is not None else _DEFAULT_EXPIRATION
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )

    @valkey_decorator()
    async def delete(self, keys: Sequence[str]) -> int:
        """
        Delete one or more keys.

        :param keys: List of keys to delete.
        :return: Number of keys that were deleted.
        """
        return await self._client.client.delete(list(keys))

    async def _time(self) -> float:
        """
        Get the current server time.

        :return: Server time as [seconds, microseconds].
        """
        result = await self._client.client.time()
        if len(result) != 2:
            raise ValueError(
                f"Unexpected result from time command: {result}. Expected a tuple of (seconds, microseconds)."
            )
        seconds_bytes, microseconds_bytes = result

        seconds = float(seconds_bytes)
        microseconds = float(microseconds_bytes)
        return seconds + (microseconds / 10**6)

    @valkey_decorator()
    async def setex(self, name: str, value: Union[str, bytes], time: int) -> None:
        """
        Set a key with an expiration time.

        :param name: Key name.
        :param value: Value to set.
        :param time: Expiration time in seconds.
        """
        await self._client.client.set(name, value, expiry=ExpirySet(ExpiryType.SEC, time))

    @valkey_decorator()
    async def incr(self, key: str) -> int:
        """
        Increment the value of a key by 1.

        :param key: The key to increment.
        :return: The new value after increment.
        """
        return await self._client.client.incr(key)

    def _get_keypair_concurrency_key(self, access_key: str, is_private: bool) -> str:
        """
        Generate keypair concurrency key.

        :param access_key: The access key.
        :param is_private: Whether this is for SFTP concurrency.
        :return: The generated key.
        """
        prefix = _KEYPAIR_SFTP_CONCURRENCY_PREFIX if is_private else _KEYPAIR_CONCURRENCY_PREFIX
        return f"{prefix}.{access_key}"

    @valkey_decorator()
    async def increment_keypair_query_count(
        self,
        access_key: str,
    ) -> None:
        now = await self._time()
        batch = self._create_batch()
        num_queries_key = self._get_keypair_query_count_key(access_key)
        batch.incr(num_queries_key)
        batch.expire(num_queries_key, 86400 * 30)  # retention: 1 month
        last_call_time_key = self._get_keypair_last_call_time_key(access_key)
        batch.set(last_call_time_key, str(now).encode())
        batch.expire(last_call_time_key, 86400 * 30)  # retention: 1 month
        await self._client.client.exec(batch, raise_on_error=True)

    # DEPRECATED: These methods are being phased out in favor of cache mirroring approach
    # Will be removed in future versions
    @valkey_decorator()
    async def increment_keypair_concurrencies(
        self,
        concurrency_to_increment: Mapping[str, int],
        sftp_concurrency_to_increment: Mapping[str, int],
    ) -> None:
        """
        DEPRECATED: Use update_compute_concurrency_by_map and update_system_concurrency_by_map instead.
        This method will be removed in future versions.

        Increment keypair concurrency counters.

        :param concurrency_to_increment: Mapping of access keys to concurrency increments.
        :param sftp_concurrency_to_increment: Mapping of access keys to SFTP concurrency increments.
        """
        log.warning(
            "increment_keypair_concurrencies is deprecated. "
            "Use update_compute_concurrency_by_map and update_system_concurrency_by_map instead."
        )
        if not concurrency_to_increment and not sftp_concurrency_to_increment:
            return

        batch = self._create_batch()
        for access_key, delta in concurrency_to_increment.items():
            key = self._get_keypair_concurrency_key(access_key, is_private=False)
            batch.incrby(key, delta)

        for access_key, delta in sftp_concurrency_to_increment.items():
            key = self._get_keypair_concurrency_key(access_key, is_private=True)
            batch.incrby(key, delta)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def decrement_keypair_concurrencies(
        self,
        concurrency_to_decrement: Mapping[str, int],
        sftp_concurrency_to_decrement: Mapping[str, int],
    ) -> None:
        """
        DEPRECATED: Use update_compute_concurrency_by_map and update_system_concurrency_by_map instead.
        This method will be removed in future versions.

        Decrement keypair concurrency counters.

        :param concurrency_to_decrement: Mapping of access keys to concurrency decrements.
        :param sftp_concurrency_to_decrement: Mapping of access keys to SFTP concurrency decrements.
        """
        log.warning(
            "decrement_keypair_concurrencies is deprecated. "
            "Use update_compute_concurrency_by_map and update_system_concurrency_by_map instead."
        )
        if not concurrency_to_decrement and not sftp_concurrency_to_decrement:
            return

        batch = self._create_batch()

        for access_key, delta in concurrency_to_decrement.items():
            key = self._get_keypair_concurrency_key(access_key, is_private=False)
            batch.decrby(key, delta)

        for access_key, delta in sftp_concurrency_to_decrement.items():
            key = self._get_keypair_concurrency_key(access_key, is_private=True)
            batch.decrby(key, delta)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def decrement_keypair_concurrency(self, access_key: str, is_private: bool = False) -> int:
        """
        Decrement keypair concurrency counter.

        :param access_key: The access key to decrement concurrency for.
        :param is_private: Whether this is for SFTP concurrency (True) or regular concurrency (False).
        :return: The new value after decrement.
        """
        key = self._get_keypair_concurrency_key(access_key, is_private)
        return await self._client.client.incrby(key, -1)

    @valkey_decorator()
    async def delete_keypair_concurrency(self, access_key: str, is_private: bool = False) -> bool:
        """
        Delete keypair concurrency counter.

        :param access_key: The access key to delete concurrency counter for.
        :param is_private: Whether this is for SFTP concurrency (True) or regular concurrency (False).
        :return: True if the key was deleted, False if it didn't exist.
        """
        key = self._get_keypair_concurrency_key(access_key, is_private)
        result = await self._client.client.delete([key])
        return result > 0

    @valkey_decorator()
    async def set_keypair_concurrency(
        self, access_key: str, concurrency_used: int, is_private: bool = False
    ) -> None:
        """
        Set keypair concurrency counter.

        :param access_key: The access key to set concurrency for.
        :param concurrency_used: The concurrency value to set.
        :param is_private: Whether this is for SFTP concurrency (True) or regular concurrency (False).
        """
        key = self._get_keypair_concurrency_key(access_key, is_private)
        await self._client.client.set(key, str(concurrency_used))

    @valkey_decorator()
    async def set_keypair_concurrencies(
        self, access_key: str, regular_concurrency: int, sftp_concurrency: int
    ) -> None:
        """
        Set both regular and SFTP keypair concurrency counters in a batch.

        :param access_key: The access key to set concurrency for.
        :param regular_concurrency: The regular concurrency value to set.
        :param sftp_concurrency: The SFTP concurrency value to set.
        """
        batch = self._create_batch()

        regular_key = self._get_keypair_concurrency_key(access_key, is_private=False)
        sftp_key = self._get_keypair_concurrency_key(access_key, is_private=True)

        batch.set(regular_key, str(regular_concurrency))
        batch.set(sftp_key, str(sftp_concurrency))

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def _get_multiple_keys(self, keys: list[str]) -> list[Optional[bytes]]:
        """
        Get multiple keys efficiently using batch operations.

        :param keys: List of keys to retrieve.
        :return: List of values, with None for non-existent keys.
        """
        if not keys:
            return []
        return await self._client.client.mget(cast(list[str | bytes], keys))

    @valkey_decorator()
    async def set_multiple_keys(
        self,
        key_value_map: Mapping[str, bytes],
        expire_sec: Optional[int] = None,
    ) -> None:
        """
        Set multiple keys efficiently using batch operations.

        :param key_value_map: Mapping of keys to values.
        :param expire_sec: Expiration time in seconds. If None, uses default expiration.
        """
        if not key_value_map:
            return

        expiration = expire_sec if expire_sec is not None else _DEFAULT_EXPIRATION
        batch = self._create_batch()

        for key, value in key_value_map.items():
            batch.set(
                key=key,
                value=value,
                expiry=ExpirySet(ExpiryType.SEC, expiration),
            )

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def update_kernel_commit_statuses(
        self,
        kernel_ids: list[str],
        expire_sec: int,
    ) -> None:
        """
        Update kernel commit statuses with expiration.

        :param kernel_ids: List of kernel IDs to update.
        :param expire_sec: Expiration time in seconds.
        """
        if not kernel_ids:
            return

        # Use batch operations to set multiple keys with same value and expiration
        batch = self._create_batch()

        for kernel_id in kernel_ids:
            key = f"kernel.{kernel_id}.commit"
            batch.set(
                key=key,
                value=b"ongoing",
                expiry=ExpirySet(ExpiryType.SEC, expire_sec),
            )

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def register_session_ids_for_status_update(
        self,
        status_set_key: str,
        session_ids: list[bytes],
    ) -> None:
        """
        Register session IDs for status updates using set operations.

        :param status_set_key: The key for the status set.
        :param session_ids: List of encoded session IDs.
        """
        if not session_ids:
            return

        # Use SADD to add session IDs to the set
        for session_id in session_ids:
            await self._client.client.sadd(status_set_key, [session_id])

    @valkey_decorator()
    async def get_and_clear_session_ids_for_status_update(
        self,
        status_set_key: str,
    ) -> list[bytes]:
        """
        Get all session IDs from the status set and clear it atomically.

        :param status_set_key: The key for the status set.
        :return: List of encoded session IDs.
        """
        count = await self._client.client.scard(status_set_key)
        if count == 0:
            return []
        # Pop all members
        results = await self._client.client.spop_count(status_set_key, count)
        return list(results)

    @valkey_decorator()
    async def remove_session_ids_from_status_update(
        self,
        status_set_key: str,
        session_ids: list[bytes],
    ) -> int:
        """
        Remove session IDs from the status update set.

        :param status_set_key: The key for the status set.
        :param session_ids: List of encoded session IDs to remove.
        :return: Number of session IDs removed.
        """
        if not session_ids:
            return 0

        # Use SREM to remove session IDs from the set
        removed_count = 0
        for session_id in session_ids:
            removed_count += await self._client.client.srem(status_set_key, [session_id])
        return removed_count

    async def _hkeys(self, hash_name: str) -> list[bytes]:
        """
        Get all keys in a hash.
        But this method uses hscan to avoid blocking.

        :param hash_name: The name of the hash.
        :return: List of keys in the hash.
        """
        cursor = b"0"
        keys: list[bytes] = []
        while True:
            result = await self._client.client.hscan(hash_name, cursor)
            cursor = cast(bytes, result[0])
            current_keys = cast(list[bytes], result[1])
            keys.extend(current_keys)
            if cursor == b"0":
                break
        return keys

    async def _keys(self, pattern: str) -> list[bytes]:
        """
        Scan for keys matching a pattern without blocking.

        :param pattern: The pattern to match keys against.
        :return: List of matching keys.
        """
        cursor = b"0"
        matched_keys: list[bytes] = []
        while True:
            result = await self._client.client.scan(cursor, match=pattern)
            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])
            matched_keys.extend(keys)
            if cursor == b"0":
                break
        return matched_keys

    @valkey_decorator()
    async def update_abuse_report(
        self,
        new_report: Mapping[str, str],
    ) -> None:
        """
        Update kernel abuse report data, removing stale entries and adding new ones.

        :param new_report: New abuse report data as a mapping.
        """
        # Use batch operations to update the report atomically
        batch = self._create_batch()
        batch.delete([_ABUSE_REPORT_HASH])
        # Add/update new entries
        for kern_id, report_val in new_report.items():
            batch.hset(_ABUSE_REPORT_HASH, {kern_id: report_val})

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def check_keypair_concurrency(
        self,
        redis_key: str,
        limit: int,
    ) -> tuple[int, int]:
        """
        Check and increment keypair concurrency usage.

        :param redis_key: The key for storing concurrency count.
        :param limit: The maximum allowed concurrent sessions.
        :return: Tuple of (ok, concurrency_used) where ok is 1 if allowed, 0 if limit exceeded.
        """
        # Set default value if key doesn't exist
        current_value = await self._client.client.get(redis_key)
        if current_value is None:
            await self._client.client.set(redis_key, "0")

        # Get current count
        result = await self._client.client.get(redis_key)
        if result is not None:
            try:
                current_count = int(str(result))
            except (ValueError, TypeError):
                current_count = 0
        else:
            current_count = 0

        # Check if limit is exceeded
        if limit > 0 and current_count >= limit:
            return (0, current_count)

        # Increment counter
        await self._client.client.incr(redis_key)
        return (1, current_count + 1)

    @valkey_decorator()
    async def scan_and_get_manager_status(
        self,
        pattern: str,
    ) -> list[Optional[bytes]]:
        """
        Scan for manager status keys and get their values.

        :param pattern: The pattern to match keys against.
        :return: List of values for matching keys.
        """
        # Use SCAN to find all matching keys
        cursor = b"0"
        matched_keys: list[bytes] = []

        while True:
            result = await self._client.client.scan(cursor, match=pattern)
            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])
            matched_keys.extend(keys)
            if cursor == b"0":
                break
        if not matched_keys:
            return []
        return await self._client.client.mget(cast(list[str | bytes], matched_keys))

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch object for batch operations.

        :param is_atomic: Whether the batch should be atomic (transaction-like).
        :return: A Batch object.
        """
        return Batch(is_atomic=is_atomic)

    def _get_keypair_query_count_key(
        self,
        access_key: str,
    ) -> str:
        return f"kp:{access_key}:num_queries"

    def _get_keypair_last_call_time_key(
        self,
        access_key: str,
    ) -> str:
        return f"kp:{access_key}:last_call_time"

    @valkey_decorator()
    async def update_compute_concurrency_by_map(
        self,
        concurrency_map: Mapping[str, int],
    ) -> None:
        """
        Update compute concurrency values from a map of access keys to concurrency counts.

        :param concurrency_map: Dictionary mapping access keys to their compute concurrency counts.
        """
        if not concurrency_map:
            return

        updates: dict[str, bytes] = {}
        for access_key, concurrency_count in concurrency_map.items():
            key = f"{_COMPUTE_CONCURRENCY_USED_KEY_PREFIX}{access_key}"
            updates[key] = str(concurrency_count).encode("utf-8")

        await self.set_multiple_keys(updates)

    @valkey_decorator()
    async def update_system_concurrency_by_map(
        self,
        concurrency_map: Mapping[str, int],
    ) -> None:
        """
        Update system (SFTP) concurrency values from a map of access keys to concurrency counts.

        :param concurrency_map: Dictionary mapping access keys to their system concurrency counts.
        """
        if not concurrency_map:
            return

        updates: dict[str, bytes] = {}
        for access_key, concurrency_count in concurrency_map.items():
            key = f"{_SYSTEM_CONCURRENCY_USED_KEY_PREFIX}{access_key}"
            updates[key] = str(concurrency_count).encode("utf-8")

        await self.set_multiple_keys(updates)

    @valkey_decorator()
    async def update_concurrency_by_fullscan(
        self,
        access_key_to_concurrency: Mapping[str, int],
    ) -> None:
        """
        Update concurrency values by doing a full scan and setting all keys.
        Used when the system has no sessions to reset all concurrency to 0.

        :param access_key_to_concurrency: Dictionary mapping access keys to their concurrency counts.
        """
        updates: dict[str, bytes] = {}

        # Scan and update compute concurrency keys
        compute_keys = await self._keys(f"{_COMPUTE_CONCURRENCY_USED_KEY_PREFIX}*")
        for key in compute_keys:
            key_str = key.decode("utf-8")
            access_key = key_str.replace(_COMPUTE_CONCURRENCY_USED_KEY_PREFIX, "")
            concurrency_count = access_key_to_concurrency.get(access_key, 0)
            updates[key_str] = str(concurrency_count).encode("utf-8")

        # Scan and update system concurrency keys
        system_keys = await self._keys(f"{_SYSTEM_CONCURRENCY_USED_KEY_PREFIX}*")
        for key in system_keys:
            key_str = key.decode("utf-8")
            access_key = key_str.replace(_SYSTEM_CONCURRENCY_USED_KEY_PREFIX, "")
            concurrency_count = access_key_to_concurrency.get(access_key, 0)
            updates[key_str] = str(concurrency_count).encode("utf-8")

        if updates:
            await self.set_multiple_keys(updates)

    @valkey_decorator()
    async def store_inference_metrics(
        self,
        app_metrics_updates: dict[Any, dict[str, Any]],
        replica_metrics_updates: dict[tuple[Any, Any], dict[str, Any]],
        cache_lifespan: int = 120,
    ) -> None:
        """
        Store inference metrics for apps and replicas with proper serialization and expiration.

        :param app_metrics_updates: Dictionary mapping endpoint_id to app metrics
        :param replica_metrics_updates: Dictionary mapping (endpoint_id, replica_id) to replica metrics
        :param cache_lifespan: TTL in seconds for the stored metrics
        """
        if not app_metrics_updates and not replica_metrics_updates:
            return

        batch = self._create_batch()

        # Store app metrics
        for endpoint_id, app_measures in app_metrics_updates.items():
            key = f"inference.{endpoint_id}.app"
            value = msgpack.packb(app_measures)
            batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, cache_lifespan))

        # Store replica metrics
        for (endpoint_id, replica_id), replica_measures in replica_metrics_updates.items():
            key = f"inference.{endpoint_id}.replica.{replica_id}"
            value = msgpack.packb(replica_measures)
            batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, cache_lifespan))

        await self._client.client.exec(batch, raise_on_error=True)

    async def get_total_resource_slots(self) -> Optional[TotalResourceData]:
        """
        Get total resource slots data from cache.

        :return: TotalResourceData if cached, None if not in cache
        """
        result = await self._client.client.get(_TOTAL_RESOURCE_SLOTS_KEY)
        if result is None:
            return None

        try:
            data = load_json(result.decode("utf-8"))
            return TotalResourceData.from_json(data)
        except (json.JSONDecodeError, ValueError, KeyError, UnicodeDecodeError) as e:
            log.warning("Failed to deserialize TotalResourceData from cache: {}", e)
            return None

    async def set_total_resource_slots(
        self, total_slots: TotalResourceData, ttl_seconds: int = 300
    ) -> None:
        """
        Set the total number of resource slots available in the system.

        :param total_slots: The TotalResourceData to cache
        :param ttl_seconds: TTL in seconds (default: 300 = 5 minutes)
        """
        try:
            total_slots_obj = total_slots.to_json()
            serialized = dump_json_str(total_slots_obj)
            await self._client.client.set(
                _TOTAL_RESOURCE_SLOTS_KEY, serialized, expiry=ExpirySet(ExpiryType.SEC, ttl_seconds)
            )
        except Exception as e:
            log.warning("Failed to serialize TotalResourceData to cache: {}", e)
            raise

    def _invalidate_keypair_concurrencies(
        self, batch: Batch, access_keys: list[AccessKey]
    ) -> Batch:
        """
        Delete concurrency counters for multiple access keys in a batch.
        Removes both regular and SFTP concurrency values for all provided keys.

        :param access_keys: List of access keys to delete concurrency for.
        """
        if not access_keys:
            return batch

        # Prepare all keys for deletion
        keys_to_delete = []
        for access_key in access_keys:
            regular_key = self._get_keypair_concurrency_key(access_key, is_private=False)
            sftp_key = self._get_keypair_concurrency_key(access_key, is_private=True)
            keys_to_delete.extend([regular_key, sftp_key])

        # Delete all keys in a single operation
        if keys_to_delete:
            batch.delete(cast(list[str | bytes], keys_to_delete))
        return batch

    def _invalidate_total_resource_slots(self, batch: Batch) -> Batch:
        """
        Invalidate (delete) the total resource slots cache.
        """
        return batch.delete([_TOTAL_RESOURCE_SLOTS_KEY])

    def _invalidate_resource_presets(self, batch: Batch, keys: list[bytes]) -> Batch:
        """
        Invalidate (delete) all resource preset check caches.
        """
        if keys:
            return batch.delete(cast(list[str | bytes], keys))
        return batch

    async def invalidate_kernel_related_cache(self, access_keys: list[AccessKey]) -> None:
        """
        Invalidate all kernel-related caches including resource presets, total resource slots,
        and keypair concurrencies for the given access keys.
        """

        # There is no batch `scan` operation, so we need to get all keys first
        pattern = "resource_preset:check:*"
        resource_preset_keys = await self._keys(pattern)

        batch = self._create_batch()
        batch = self._invalidate_resource_presets(batch, resource_preset_keys)
        batch = self._invalidate_total_resource_slots(batch)
        batch = self._invalidate_keypair_concurrencies(batch, access_keys)

        await self._client.client.exec(batch, raise_on_error=True)
