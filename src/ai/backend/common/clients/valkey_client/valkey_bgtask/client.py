from __future__ import annotations

import asyncio
import enum
import logging
import textwrap
import uuid
from collections.abc import Collection
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Self, Sequence, cast

from glide import (
    Batch,
    Script,
)

from ai.backend.common.bgtask.exception import InvalidTaskMetadataError
from ai.backend.common.bgtask.types import (
    TaskID,
    TaskInfo,
    TaskStatus,
    TaskSubKeyInfo,
    TaskTotalInfo,
)
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.data.bgtask.defs import (
    TASK_FINISHED_TTL,
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
_TASK_KEY_PREFIX = f"{_KEY_PREFIX}:meta"  # bgtask:meta:{task_id}
_TASK_SUBKEY_SET_PREFIX = f"{_KEY_PREFIX}:subkey"  # bgtask:subkey:{task_id}:{subkey}
_TASK_SUBTASK_KEY_PREFIX = f"{_KEY_PREFIX}:subtask"  # bgtask:subtask:{task_id}:{subkey}
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


@dataclass
class TaskSetKey:
    server_id: str
    tags: Collection[str]


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

    def _get_task_subkey_set_key(self, task_id: TaskID) -> str:
        return f"{_TASK_SUBKEY_SET_PREFIX}:{task_id}"

    def _get_subtask_key(self, task_id: TaskID, subkey: str) -> str:
        return f"{_TASK_SUBTASK_KEY_PREFIX}:{task_id}:{subkey}"

    # Task metadata operations
    @valkey_decorator()
    async def register_task(self, task_total_info: TaskTotalInfo, task_set_key: TaskSetKey) -> None:
        """
        Register a background task with 24-hour TTL and index it by tags and server ID.
        """
        batch = self._create_batch()
        task_info = task_total_info.task_info
        # task metadata
        task_meta_key = self._get_task_key(task_info.task_id)
        batch.hset(task_meta_key, task_info.to_valkey_hash_fields())
        batch.expire(task_meta_key, TASK_METADATA_TTL)
        # subkey set for tracking all subkeys of a task
        task_subkey_set_key = self._get_task_subkey_set_key(task_info.task_id)
        log.info(
            "Registering task (id: {}, subkeys: {})",
            task_info.task_id,
            len(task_total_info.task_key_list),
        )
        batch.sadd(task_subkey_set_key, task_total_info.subkeys())
        batch.expire(task_subkey_set_key, TASK_METADATA_TTL)
        # individual subtask keys
        for subkey_info in task_total_info.task_key_list:
            subtask_key = self._get_subtask_key(subkey_info.task_id, subkey_info.key)
            batch.hset(subtask_key, subkey_info.to_valkey_hash_fields())
            batch.expire(subtask_key, TASK_METADATA_TTL)
        batch = await self._build_claim_task(batch, task_info.task_id, task_set_key)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def claim_task(self, task_id: TaskID, task_set_key: TaskSetKey) -> None:
        """
        Claim an existing task by adding index references. Idempotent operation.
        """
        batch = self._create_batch()
        batch = await self._build_claim_task(batch, task_id, task_set_key)
        await self._client.client.exec(batch, raise_on_error=True)

    async def _build_claim_task(
        self, batch: Batch, task_id: TaskID, task_set_key: TaskSetKey
    ) -> Batch:
        for tag in task_set_key.tags:
            tag_key = self._get_tag_key(tag)
            batch.sadd(tag_key, [task_id.hex])
            batch.expire(tag_key, TASK_METADATA_TTL)

        server_key = self._get_server_key(task_set_key.server_id)
        batch.sadd(server_key, [task_id.hex])
        batch.expire(server_key, TASK_METADATA_TTL)
        return batch

    @valkey_decorator()
    async def heartbeat(
        self,
        all_total_info: Sequence[TaskTotalInfo],
        task_set_key: TaskSetKey,
    ) -> None:
        """
        Extend TTL to 24 hours for active tasks. Non-existent tasks are ignored.
        """
        keys: list[str] = []
        task_keys = [
            self._get_task_key(total_info.task_info.task_id) for total_info in all_total_info
        ]
        keys.extend(task_keys)
        subtask_set_keys = [
            self._get_task_subkey_set_key(total_info.task_info.task_id)
            for total_info in all_total_info
        ]
        keys.extend(subtask_set_keys)
        subtask_keys = []
        for total_info in all_total_info:
            for subkey_info in total_info.task_key_list:
                subtask_key = self._get_subtask_key(subkey_info.task_id, subkey_info.key)
                subtask_keys.append(subtask_key)
        keys.extend(subtask_keys)
        server_key = self._get_server_key(task_set_key.server_id)
        keys.append(server_key)
        tag_keys = [self._get_tag_key(tag) for tag in task_set_key.tags]
        keys.extend(tag_keys)
        if not keys:
            return
        batch = self._create_batch()
        for key in keys:
            batch.expire(key, TASK_METADATA_TTL)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def finish_subtask(
        self, task_id: TaskID, subkey: str, status: TaskStatus, last_message: str
    ) -> bool:
        """
        Mark a subtask as finished by updating its status and task_info counters.
        Updates ongoing_count, success_count, or failure_count atomically.

        Returns:
            True if all subtasks are completed (ongoing_count == 0), False otherwise.
        """
        from ai.backend.common.bgtask.types import TaskStatus

        batch = self._create_batch()

        # Update subtask status
        subtask_key = self._get_subtask_key(task_id, subkey)
        batch.hset(
            subtask_key,
            {
                b"status": status.value,
                b"last_message": last_message,
            },
        )

        # Update task_info success/failure counters
        task_key = self._get_task_key(task_id)
        match status:
            case TaskStatus.SUCCESS:
                batch.hincrby(task_key, b"success_count", 1)
            case TaskStatus.FAILURE:
                batch.hincrby(task_key, b"failure_count", 1)

        # Decrement ongoing_count last to get its final value
        batch.hincrby(task_key, b"ongoing_count", -1)

        results = await self._client.client.exec(batch, raise_on_error=True)
        if results is None:
            raise RuntimeError("Failed to execute finish_subtask batch")

        # Last result is the updated ongoing_count
        ongoing_count = cast(int, results[-1])
        return ongoing_count == 0

    @valkey_decorator()
    async def unregister_task(self, task_id: TaskID, task_set_key: TaskSetKey) -> None:
        """
        Mark task as finished by setting short TTL for query purposes.
        Task metadata remains accessible for a short period before automatic cleanup.
        Removes from index references immediately. Idempotent operation.
        """
        # First, get subtask keys before modifying anything
        task_subkey_set_key = self._get_task_subkey_set_key(task_id)
        subkeys_result = await self._client.client.smembers(task_subkey_set_key)

        batch = self._create_batch()

        # Set short TTL on task metadata
        task_key = self._get_task_key(task_id)
        batch.expire(task_key, TASK_FINISHED_TTL)

        # Set short TTL on subkey set
        batch.expire(task_subkey_set_key, TASK_FINISHED_TTL)

        # Set short TTL on all subtasks
        if subkeys_result:
            for subkey in subkeys_result:
                subtask_key = self._get_subtask_key(task_id, subkey.decode())
                batch.expire(subtask_key, TASK_FINISHED_TTL)

        # Remove from index references immediately
        for tag in task_set_key.tags:
            tag_key = self._get_tag_key(tag)
            batch.srem(tag_key, [task_id.hex])

        server_key = self._get_server_key(task_set_key.server_id)
        batch.srem(server_key, [task_id.hex])

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def fetch_unmanaged_tasks(self, task_set_key: TaskSetKey) -> list[TaskTotalInfo]:
        """
        Fetch unmanaged tasks with insufficient TTL for a specific TaskSetKey.
        """
        keys = []
        keys.append(self._get_server_key(task_set_key.server_id))
        tag_keys = [self._get_tag_key(tag) for tag in task_set_key.tags]
        keys.extend(tag_keys)
        task_ids = await self._fetch_task_ids_by_groups(keys)
        return await self._fetch_unmanaged_tasks(task_ids, task_set_key)

    async def _fetch_task_ids_by_groups(self, keys: Collection[str]) -> set[TaskID]:
        if not keys:
            return set()
        batch = self._create_batch()
        for key in keys:
            batch.smembers(key)
        raw_results = await self._client.client.exec(batch, raise_on_error=True)
        if raw_results is None:
            raise RuntimeError("Failed to retrieve members from keys")
        results = cast(list[set[bytes]], raw_results)
        task_ids: set[TaskID] = set()
        for raw_result in results:
            if raw_result:
                task_ids |= {TaskID(uuid.UUID(hex=hex_id.decode())) for hex_id in raw_result}
        return task_ids

    async def _fetch_unmanaged_tasks(
        self, task_ids: Collection[TaskID], task_set_key: TaskSetKey
    ) -> list[TaskTotalInfo]:
        if not task_ids:
            return []
        fetch_results = await asyncio.gather(
            *[self._fetch_unmanaged_task(task_id, task_set_key) for task_id in task_ids],
            return_exceptions=True,
        )
        results: list[TaskTotalInfo] = []
        for fetch_result in fetch_results:
            if isinstance(fetch_result, BaseException):
                log.warning("Failed to fetch unmanaged task: {}", fetch_result)
                continue
            if fetch_result is not None:
                results.append(fetch_result)
        return results

    async def _check_and_refresh_ttl(self, task_id: TaskID) -> bool:
        """
        Check if task TTL is below threshold and refresh it.
        Returns True if TTL was insufficient (task needs to be fetched), False otherwise.
        """
        task_key = self._get_task_key(task_id)
        script = self._conditional_ttl_refresh_script()
        raw_result = await self._client.client.invoke_script(
            script,
            keys=[task_key],
            args=[
                str(TASK_TTL_THRESHOLD),
                str(TASK_METADATA_TTL),
            ],
        )

        result = cast(bytes, raw_result)
        result_type = _ScriptResult.from_bytes(result)

        match result_type:
            case _ScriptResult.TTL_SUFFICIENT:
                log.debug("Task TTL sufficient, skipping (id: {})", task_id)
                return False
            case _ScriptResult.KEY_NOT_EXIST | _ScriptResult.NO_EXPIRY:
                log.warning(
                    "Task key not exist or no expiry, skipping (id: {}, result: {})",
                    task_id,
                    result_type,
                )
                return False
            case _ScriptResult.TTL_INSUFFICIENT:
                log.debug("Task TTL insufficient (id: {})", task_id)
                return True

    async def _fetch_total_info(self, task_id: TaskID) -> Optional[TaskTotalInfo]:
        """
        Fetch complete task information including task metadata and all subtask metadata.
        Returns None if metadata is missing or corrupted.
        """
        # Fetch task metadata
        task_key = self._get_task_key(task_id)
        raw_task_metadata_dict = await self._client.client.hgetall(task_key)
        if not raw_task_metadata_dict:
            log.warning("Task metadata not found (id: {})", task_id)
            return None
        task_info = TaskInfo.from_valkey_hash_fields(raw_task_metadata_dict)
        # Fetch subkeys
        task_subkey_set_key = self._get_task_subkey_set_key(task_id)
        subkeys_result = await self._client.client.smembers(task_subkey_set_key)
        subkeys = {subkey.decode() for subkey in subkeys_result} if subkeys_result else set()

        # Fetch all subtask metadata
        task_key_set = []
        if subkeys:
            batch = self._create_batch()
            for subkey in subkeys:
                subtask_key = self._get_subtask_key(task_id, subkey)
                batch.hgetall(subtask_key)

            subtask_results = await self._client.client.exec(batch, raise_on_error=True)
            if subtask_results is None:
                log.warning("Failed to fetch subtask metadata (id: {})", task_id)
                return None

            raw_subtask_results = cast(list[dict[bytes, bytes]], subtask_results)

            # Parse subtask metadata
            for raw_subtask_dict in raw_subtask_results:
                try:
                    subtask_info = TaskSubKeyInfo.from_valkey_hash_fields(raw_subtask_dict)
                    task_key_set.append(subtask_info)
                except InvalidTaskMetadataError:
                    log.warning("Invalid subtask metadata (id: {})", task_id)
                    return None
        log.info(
            "Fetched task total info (id: {}, task_info: {}, subtasks: {})",
            task_id,
            task_info,
            len(task_key_set),
        )
        return TaskTotalInfo(task_info=task_info, task_key_list=task_key_set)

    async def _fetch_unmanaged_task(
        self, task_id: TaskID, task_set_key: TaskSetKey
    ) -> Optional[TaskTotalInfo]:
        """
        Check if task TTL is below threshold and fetch complete task info if needed.
        If fetching fails (metadata missing or corrupted), unregister the task.
        """
        needs_fetch = await self._check_and_refresh_ttl(task_id)
        if not needs_fetch:
            return None

        total_info = await self._fetch_total_info(task_id)
        if total_info is None:
            # Metadata is missing or corrupted, clean up the task references
            log.warning(
                "Failed to fetch task info, unregistering task (id: {})",
                task_id,
            )
            try:
                await self.unregister_task(task_id, task_set_key)
            except Exception:
                log.exception("Failed to unregister corrupted task (id: {})", task_id)
            return None

        return total_info

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)

    @classmethod
    @lru_cache(maxsize=1)
    def _conditional_ttl_refresh_script(cls) -> Script:
        code = textwrap.dedent(f"""
        -- KEYS[1]: Task metadata key
        -- ARGV[1]: TTL threshold (in seconds)
        -- ARGV[2]: New TTL value to set (in seconds)

        local task_key = KEYS[1]
        local ttl_threshold = tonumber(ARGV[1])
        local new_ttl = tonumber(ARGV[2])

        -- Check if task key exists and get current TTL
        local current_ttl = redis.call('TTL', task_key)

        -- Handle non-existent key (-2)
        if current_ttl == -2 then
            return '{_ScriptResult.KEY_NOT_EXIST}'
        end

        -- Key exists, set new TTL
        redis.call('EXPIRE', task_key, new_ttl)

        -- Handle key without expiration (-1)
        if current_ttl == -1 then
            return '{_ScriptResult.NO_EXPIRY}'
        end

        -- Key exists and has TTL, check threshold
        if current_ttl < ttl_threshold then
            return '{_ScriptResult.TTL_INSUFFICIENT}'
        else
            return '{_ScriptResult.TTL_SUFFICIENT}'
        end
        """)
        return Script(code)
