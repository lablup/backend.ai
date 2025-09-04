from __future__ import annotations

import enum
import logging
import textwrap
import uuid
from collections.abc import Collection
from typing import Optional, Self, cast

from glide import (
    Batch,
    ExpirySet,
    ExpiryType,
    Script,
)

from ai.backend.common.bgtask.exception import InvalidTaskMetadataError
from ai.backend.common.bgtask.types import (
    BackgroundTaskMetadata,
    TaskID,
)
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.data.bgtask.defs import (
    TASK_METADATA_TTL,
    TASK_TTL_THRESHOLD,
)
from ai.backend.common.defs import REDIS_BGTASK_DB
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_bgtask client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_BGTASK)

_KEY_PREFIX = "bgtask"
_TASK_KEY_PREFIX = f"{_KEY_PREFIX}:task"  # bgtask:task:{task_id}
_TAG_KEY_PREFIX = f"{_KEY_PREFIX}:tag"  # bgtask:tag:{tag}
_SERVER_KEY_PREFIX = f"{_KEY_PREFIX}:server"  # bgtask:server:{server_id}


class _ScriptResult(enum.StrEnum):
    KEY_NOT_EXIST = "key_not_exist"
    NO_EXPIRY = "no_expiry"
    TTL_SUFFICIENT = "ttl_sufficient"
    TTL_INSUFFICIENT = "ttl_insufficient"

    @classmethod
    def from_bytes(cls, value: bytes) -> _ScriptResult:
        return cls(value.decode())


class ValkeyBgtaskClient:
    """
    Client for background task management using Valkey/Glide.
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
        db_id: int = REDIS_BGTASK_DB,
        human_readable_name: str = "bgtask",
    ) -> Self:
        """
        Create a ValkeyBgtaskClient instance.
        """
        client = create_valkey_client(
            valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client)

    async def close(self) -> None:
        """Close the client connection."""
        if not self._closed:
            await self._client.disconnect()
            self._closed = True

    def _get_tag_key(self, tag: str) -> str:
        return f"{_TAG_KEY_PREFIX}:{tag}"

    def _get_server_key(self, server_id: str) -> str:
        return f"{_SERVER_KEY_PREFIX}:{server_id}"

    def _get_task_key(self, task_id: TaskID) -> str:
        return f"{_TASK_KEY_PREFIX}:{task_id}"

    # Task metadata operations
    @valkey_decorator()
    async def register_task(self, metadata: BackgroundTaskMetadata) -> None:
        """
        Register a background task with 24-hour TTL and index it by tags and server ID.
        """
        batch = self._create_batch()
        key = self._get_task_key(metadata.task_id)
        value = metadata.to_json()
        batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, TASK_METADATA_TTL))

        for tag in metadata.tags:
            tag_key = self._get_tag_key(tag)
            batch.sadd(tag_key, [metadata.task_id.hex])
            batch.expire(tag_key, TASK_METADATA_TTL)

        server_key = self._get_server_key(metadata.server_id)
        batch.sadd(server_key, [metadata.task_id.hex])
        batch.expire(server_key, TASK_METADATA_TTL)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def unregister_task(self, metadata: BackgroundTaskMetadata) -> None:
        """
        Remove task and all its index references. Idempotent operation.
        """
        batch = self._create_batch()
        key = self._get_task_key(metadata.task_id)
        batch.delete([key])

        for tag in metadata.tags:
            tag_key = self._get_tag_key(tag)
            batch.srem(tag_key, [metadata.task_id.hex])

        server_key = self._get_server_key(metadata.server_id)
        batch.srem(server_key, [metadata.task_id.hex])
        await self._client.client.exec(batch, raise_on_error=True)

    async def _get_registered_task_ids(self, keys: Collection[str]) -> set[TaskID]:
        if not keys:
            return set()
        batch = self._create_batch()
        for key in keys:
            batch.smembers(key)
        raw_results = await self._client.client.exec(batch, raise_on_error=True)
        if raw_results is None:
            raise RuntimeError("Failed to retrieve members from keys")
        results = cast(list[Optional[set[bytes]]], raw_results)
        task_ids: set[TaskID] = set()
        for raw_result in results:
            if raw_result is not None:
                task_ids |= {TaskID(uuid.UUID(hex=hex_id.decode())) for hex_id in raw_result}
        return task_ids

    @valkey_decorator()
    async def list_timeout_tasks_by_tags(
        self, tags: Collection[str]
    ) -> list[BackgroundTaskMetadata]:
        """
        List tasks with insufficient TTL filtered by tags.
        """
        if not tags:
            return []
        keys = [self._get_tag_key(tag) for tag in tags]
        task_ids = await self._get_registered_task_ids(keys)
        results = await self._list_timeout_tasks(task_ids)
        return results

    @valkey_decorator()
    async def list_timeout_tasks_by_server_id(self, server_id: str) -> list[BackgroundTaskMetadata]:
        """
        List tasks with insufficient TTL owned by a specific server.
        """
        key = self._get_server_key(server_id)
        task_ids = await self._get_registered_task_ids([key])
        results = await self._list_timeout_tasks(task_ids)
        return results

    async def _list_timeout_tasks(
        self, task_ids: Collection[TaskID]
    ) -> list[BackgroundTaskMetadata]:
        if not task_ids:
            return []
        script = self._task_getter_script()
        results: list[BackgroundTaskMetadata] = []
        for task_id in task_ids:
            key = self._get_task_key(task_id)
            raw_result = await self._client.client.invoke_script(
                script,
                keys=[key],
                args=[
                    str(TASK_TTL_THRESHOLD),
                    str(TASK_METADATA_TTL),
                ],
            )
            result = cast(list[bytes], raw_result)
            result_type, metadata = self._resolve_script_result(result)
            match result_type:
                case _ScriptResult.TTL_SUFFICIENT:
                    log.debug(
                        "Task TTL sufficient, skipping (id: {})",
                        task_id,
                    )
                    continue
                case _ScriptResult.KEY_NOT_EXIST | _ScriptResult.NO_EXPIRY:
                    log.warning(
                        "Task key not exist or no expiry, skipping (id: {}, result: {})",
                        task_id,
                        result_type,
                    )
                    continue
                case _ScriptResult.TTL_INSUFFICIENT:
                    log.info(
                        "Task TTL insufficient, fetching metadata (id: {}, metadata: {})",
                        task_id,
                        metadata,
                    )
                    if metadata is None:
                        continue

            results.append(metadata)

        return results

    def _resolve_script_result(
        self, raw_result: list[bytes]
    ) -> tuple[_ScriptResult, Optional[BackgroundTaskMetadata]]:
        result_type = _ScriptResult.from_bytes(raw_result[0])
        metadata: Optional[BackgroundTaskMetadata] = None
        if len(raw_result) == 2:
            raw_metadata = raw_result[1]
            try:
                metadata = BackgroundTaskMetadata.from_json(raw_metadata)
            except InvalidTaskMetadataError:
                log.exception("Invalid bgtask metadata (data: {})", raw_metadata)
        return result_type, metadata

    @valkey_decorator()
    async def heartbeat(
        self,
        task_ids: Collection[TaskID],
        server_id: Optional[str],
        tags: Collection[str],
    ) -> None:
        """
        Extend TTL to 24 hours for active tasks. Non-existent tasks are ignored.
        """
        keys: list[str] = []

        task_keys = [self._get_task_key(task_id) for task_id in task_ids]
        keys.extend(task_keys)
        if server_id is not None:
            server_key = self._get_server_key(server_id)
            keys.append(server_key)
        tag_keys = [self._get_tag_key(tag) for tag in tags]
        keys.extend(tag_keys)

        if not keys:
            return
        batch = self._create_batch()
        for key in keys:
            batch.expire(key, TASK_METADATA_TTL)
        await self._client.client.exec(batch, raise_on_error=True)

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)

    def _task_getter_script(self) -> Script:
        code = textwrap.dedent(f"""
        -- KEYS[1]: Key
        -- ARGV[1]: TTL threshold (in seconds)
        -- ARGV[2]: New TTL value to set (in seconds)

        local target_key = KEYS[1]
        local ttl_threshold = tonumber(ARGV[1])
        local new_ttl = tonumber(ARGV[2])

        -- Check if key exists and get current TTL
        local current_ttl = redis.call('TTL', target_key)

        -- Handle non-existent key (-2)
        if current_ttl == -2 then
            -- Key doesn't exist
            return {{'{_ScriptResult.KEY_NOT_EXIST}'}}
        end

        -- Key exists, set new TTL
        redis.call('EXPIRE', target_key, new_ttl)

        -- Handle key without expiration (-1) - treat as infinite TTL
        if current_ttl == -1 then
            -- Key exists but has no expiration, TTL is sufficient
            return {{'{_ScriptResult.NO_EXPIRY}'}}
        end

        -- Key exists and has TTL, check threshold
        if current_ttl < ttl_threshold then
            -- TTL is below threshold, return true with value
            local value = redis.call('GET', target_key)
            return {{'{_ScriptResult.TTL_INSUFFICIENT}', value}}
        else
            -- TTL is sufficient, return false with nil
            return {{'{_ScriptResult.TTL_SUFFICIENT}'}}
        end
        """)
        return Script(code)
