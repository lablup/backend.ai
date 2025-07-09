import logging
from typing import Any, Awaitable, Callable, List, Mapping, Optional, Self, Sequence, Union, cast

from glide import (
    Batch,
    ExpirySet,
    ExpiryType,
)

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
    valkey_decorator,
)
from ai.backend.common.types import RedisHelperConfig, RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_EXPIRATION = 86400  # 24 hours default expiration


class ValkeyStatClient:
    """
    Client for interacting with Valkey for statistics operations using GlideClient.
    """

    _client: AbstractValkeyClient
    _closed: bool
    name: str
    service_name: Optional[str]
    redis_helper_config: RedisHelperConfig

    def __init__(
        self,
        client: AbstractValkeyClient,
        name: str = "valkey_stat",
        service_name: Optional[str] = None,
        redis_helper_config: Optional[RedisHelperConfig] = None,
    ) -> None:
        self._client = client
        self._closed = False
        self.name = name
        self.service_name = service_name
        self.redis_helper_config = redis_helper_config or {}

    @classmethod
    async def create(
        cls,
        redis_target: RedisTarget,
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
            target=redis_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(
            client=client,
            name=human_readable_name,
            service_name=human_readable_name,
            redis_helper_config={},
        )

    async def close(self) -> None:
        """
        Close the ValkeyStatClient connection.
        """
        if self._closed:
            log.warning("ValkeyStatClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_decorator()
    async def get(self, key: str) -> Optional[bytes]:
        """
        Get the value of a key.

        :param key: The key to retrieve.
        :return: The value of the key, or None if the key doesn't exist.
        """
        return await self._client.client.get(key)

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

    @valkey_decorator()
    async def time(self) -> List[int]:
        """
        Get the current server time.

        :return: Server time as [seconds, microseconds].
        """
        time_result = await self._client.client.time()
        return [int(time_result[0]), int(time_result[1])]

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

    @valkey_decorator()
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set the expiration time for a key.

        :param key: The key to expire.
        :param seconds: Expiration time in seconds.
        :return: True if the expiration was set successfully.
        """
        return await self._client.client.expire(key, seconds)

    @valkey_decorator()
    async def mget(self, keys: Sequence[str]) -> List[Optional[bytes]]:
        """
        Get multiple keys in a single operation.

        :param keys: List of keys to retrieve.
        :return: List of values, with None for non-existent keys.
        """
        if not keys:
            return []
        return await self._client.client.mget(list(keys))

    @valkey_decorator()
    async def hset(
        self,
        key: str,
        field_value_map: Mapping[str, bytes],
        expire_sec: Optional[int] = None,
    ) -> None:
        """
        Set multiple hash fields to multiple values.

        :param key: The hash key.
        :param field_value_map: Mapping of field names to values.
        :param expire_sec: Expiration time in seconds. If None, uses default expiration.
        """
        expiration = expire_sec if expire_sec is not None else _DEFAULT_EXPIRATION

        # Use batch operation to set hash fields and expiration atomically
        batch = self._create_batch(is_atomic=True)

        # Convert mapping to proper format for hset
        batch.hset(key, cast(Mapping[Union[str, bytes], Union[str, bytes]], field_value_map))
        batch.expire(key, expiration)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def hget(self, key: str, field: str) -> Optional[bytes]:
        """
        Get the value of a hash field.

        :param key: The hash key.
        :param field: The field name.
        :return: The value of the field, or None if it doesn't exist.
        """
        return await self._client.client.hget(key, field)

    @valkey_decorator()
    async def execute_batch(self, batch_operations: List[dict]) -> List[Any]:
        """
        Execute multiple operations in a batch.

        :param batch_operations: List of operations to execute.
        :return: List of results from each operation.
        """
        batch = self._create_batch(is_atomic=False)

        for operation in batch_operations:
            op_type = operation["operation"]
            if op_type == "get":
                batch.get(operation["key"])
            elif op_type == "set":
                expire_sec = operation.get("expire_sec", _DEFAULT_EXPIRATION)
                batch.set(
                    key=operation["key"],
                    value=operation["value"],
                    expiry=ExpirySet(ExpiryType.SEC, expire_sec),
                )
            elif op_type == "delete":
                batch.delete(operation["keys"])
            elif op_type == "hset":
                batch.hset(operation["key"], operation["field_value_map"])
                if "expire_sec" in operation:
                    batch.expire(operation["key"], operation["expire_sec"])
            elif op_type == "hget":
                batch.hget(operation["key"], operation["field"])
            else:
                raise ValueError(f"Unsupported operation type: {op_type}")

        results = await self._client.client.exec(batch, raise_on_error=True)
        return results if results is not None else []

    @valkey_decorator()
    async def get_multiple_keys(self, keys: List[str]) -> List[Optional[bytes]]:
        """
        Get multiple keys efficiently using batch operations.

        :param keys: List of keys to retrieve.
        :return: List of values, with None for non-existent keys.
        """
        if not keys:
            return []

        batch = self._create_batch(is_atomic=False)
        for key in keys:
            batch.get(key)

        results = await self._client.client.exec(batch, raise_on_error=True)
        return cast(List[Optional[bytes]], results)

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
        batch = self._create_batch(is_atomic=True)

        for key, value in key_value_map.items():
            batch.set(
                key=key,
                value=value,
                expiry=ExpirySet(ExpiryType.SEC, expiration),
            )

        await self._client.client.exec(batch, raise_on_error=True)

    # Compatibility methods for redis_helper interface
    async def execute(
        self,
        func: Callable[[Any], Awaitable[Any]],
        *,
        encoding: Optional[str] = None,
        command_timeout: Optional[float] = None,
    ) -> Any:
        """
        Execute a function with ValkeyStatClient for redis_helper compatibility.

        :param func: Function that takes a client and returns an awaitable
        :param encoding: Optional encoding for response (for compatibility)
        :param command_timeout: Optional timeout (for compatibility)
        :return: Result of the function execution
        """
        try:
            result = await func(self)

            # Handle encoding if specified and result is bytes
            if encoding and isinstance(result, bytes):
                return result.decode(encoding)
            elif encoding and isinstance(result, list):
                # Handle list of bytes responses
                return [
                    item.decode(encoding) if isinstance(item, bytes) else item for item in result
                ]

            return result
        except Exception as e:
            # Re-raise with original exception for compatibility
            raise e

    @property
    def client(self) -> "ValkeyStatClient":
        """
        Property to provide client access for redis_helper compatibility.
        """
        return self

    @property
    def sentinel(self) -> None:
        """
        Property to provide sentinel compatibility (ValkeyStatClient doesn't use sentinel).
        """
        return None

    # Additional Redis-compatible methods
    @valkey_decorator()
    async def ping(self) -> bytes:
        """
        Ping the Redis server (redis_helper compatibility).
        """
        # Use time as a simple ping equivalent
        return await self.ping()

    @valkey_decorator()
    async def pipeline(self) -> "ValkeyStatPipeline":
        """
        Create a pipeline-like object for batch operations (redis_helper compatibility).
        """
        return ValkeyStatPipeline(self)

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch object for batch operations.

        :param is_atomic: Whether the batch should be atomic (transaction-like).
        :return: A Batch object.
        """
        return Batch(is_atomic=is_atomic)


class ValkeyStatPipeline:
    """
    Pipeline-like wrapper for ValkeyStatClient to provide redis_helper compatibility.
    """

    def __init__(self, client: ValkeyStatClient) -> None:
        self._client = client
        self._operations: List[dict] = []

    def get(self, key: str) -> "ValkeyStatPipeline":
        """Add get operation to pipeline."""
        self._operations.append({"operation": "get", "key": key})
        return self

    def set(self, key: str, value: bytes, ex: Optional[int] = None) -> "ValkeyStatPipeline":
        """Add set operation to pipeline."""
        operation: dict = {"operation": "set", "key": key, "value": value}
        if ex is not None:
            operation["expire_sec"] = ex
        self._operations.append(operation)
        return self

    def delete(self, *keys: str) -> "ValkeyStatPipeline":
        """Add delete operation to pipeline."""
        self._operations.append({"operation": "delete", "keys": list(keys)})
        return self

    def hset(self, key: str, field: str, value: bytes) -> "ValkeyStatPipeline":
        """Add hset operation to pipeline."""
        self._operations.append({
            "operation": "hset",
            "key": key,
            "field_value_map": {field: value},
        })
        return self

    def hget(self, key: str, field: str) -> "ValkeyStatPipeline":
        """Add hget operation to pipeline."""
        self._operations.append({"operation": "hget", "key": key, "field": field})
        return self

    def expire(self, key: str, time: int) -> "ValkeyStatPipeline":
        """Add expire operation to pipeline."""
        # For simplicity, we'll set expire_sec on the last operation if it's a set/hset
        if self._operations and self._operations[-1]["operation"] in ["set", "hset"]:
            self._operations[-1]["expire_sec"] = time
        return self

    async def execute(self) -> List[Any]:
        """Execute all pipeline operations."""
        if not self._operations:
            return []
        return await self._client.execute_batch(self._operations)
