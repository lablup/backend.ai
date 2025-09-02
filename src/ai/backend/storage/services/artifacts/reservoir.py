"""HuggingFace model scanner implementation for Backend.AI storage."""

import asyncio
import logging
import mimetypes
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional

import aioboto3

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.unified import (
    ObjectStorageConfig,
    ReservoirConfig,
)
from ai.backend.storage.exception import (
    StorageBucketNotFoundError,
    StorageNotFoundError,
)
from ai.backend.storage.services.storages import StorageService
from ai.backend.storage.types import BucketCopyOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_dir_marker(key: str) -> bool:
    # Return True if the given object key represents a "directory marker".
    # In S3/MinIO, folders do not really exist; some tools create zero-byte
    # objects whose keys end with "/" to simulate directories.
    return key.endswith("/")


@dataclass
class ReservoirServiceArgs:
    background_task_manager: BackgroundTaskManager
    storage_service: StorageService
    event_producer: EventProducer
    storage_configs: list[ObjectStorageConfig]


class ReservoirService:
    """Service for Reservoir model operations"""

    _storages_service: StorageService
    _background_task_manager: BackgroundTaskManager
    _event_producer: EventProducer
    _storage_configs: dict[str, ObjectStorageConfig]

    def __init__(self, args: ReservoirServiceArgs):
        self._storages_service = args.storage_service
        self._background_task_manager = args.background_task_manager
        self._event_producer = args.event_producer
        self._storage_configs = {cfg.name: cfg for cfg in args.storage_configs}

    def _get_s3_client(self, storage_name: str, bucket_name: str) -> S3Client:
        storage_config = self._storage_configs.get(storage_name)
        if not storage_config:
            raise StorageNotFoundError(
                f"No storage configuration found for storage: {storage_name}"
            )

        if bucket_name not in storage_config.buckets:
            raise StorageBucketNotFoundError(
                f"Bucket '{bucket_name}' not found in storage '{storage_name}'"
            )

        return S3Client(
            bucket_name=bucket_name,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

    async def _list_all_keys_and_sizes(
        self,
        *,
        endpoint_url: str,
        access_key: Optional[str],
        secret_key: Optional[str],
        region: Optional[str],
        bucket: str,
    ) -> tuple[list[str], dict[str, int], int]:
        """List all non-marker object keys in the bucket and return (keys, size_map, total_bytes)."""
        session = aioboto3.Session()
        keys: list[str] = []
        size_map: dict[str, int] = {}
        total = 0

        async with session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        ) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if _is_dir_marker(key):
                        continue
                    size = int(obj.get("Size", 0))
                    keys.append(key)
                    size_map[key] = size
                    total += size

        return keys, size_map, total

    async def stream_bucket_to_bucket(
        self,
        src: ReservoirConfig,
        storage_name: str,
        bucket_name: str,
        options: BucketCopyOptions,
        progress_reporter: ProgressReporter,
    ) -> int:
        """
        Stream-copy ALL objects from the source bucket (no prefix) to the destination bucket.
        Returns the number of copied objects.
        """
        dst_client = self._get_s3_client(storage_name, bucket_name)
        download_chunk_size = self._storage_configs[storage_name].remote_storage_download_chunk_size

        # List all objects up front
        target_keys, size_map, total_bytes = await self._list_all_keys_and_sizes(
            endpoint_url=src.endpoint,
            access_key=src.object_storage_access_key,
            secret_key=src.object_storage_secret_key,
            region=src.object_storage_region,
            bucket=bucket_name,
        )

        if not target_keys:
            log.trace("[stream_bucket_to_bucket] no objects to copy; nothing to do")
            return 0

        log.trace(
            "[stream_bucket_to_bucket] start src_endpoint={} src_bucket={} dst_storage={} dst_bucket={} objects={} total_bytes={} concurrency={}",
            src.endpoint,
            bucket_name,
            storage_name,
            bucket_name,
            len(target_keys),
            total_bytes,
            options.concurrency,
        )

        copied = 0
        sem = asyncio.Semaphore(options.concurrency)

        src_s3_client = S3Client(
            bucket_name=bucket_name,
            endpoint_url=src.endpoint,
            region_name=src.object_storage_region,
            aws_access_key_id=src.object_storage_access_key,
            aws_secret_access_key=src.object_storage_secret_key,
        )

        async def _copy_single_object(key: str) -> None:
            async with sem:
                size = size_map.get(key, -1)
                log.trace("[stream_bucket_to_bucket] begin key={} size={}", key, size)

                async def _data_stream() -> AsyncIterator[bytes]:
                    sent = 0
                    next_mark = options.progress_log_interval_bytes
                    async for chunk in src_s3_client.download_stream(
                        key, chunk_size=download_chunk_size
                    ):
                        sent += len(chunk)
                        if next_mark and sent >= next_mark:
                            log.trace(
                                "[stream_bucket_to_bucket] progress key={} sent={}/{}",
                                key,
                                sent,
                                size,
                            )
                            next_mark += options.progress_log_interval_bytes
                        yield chunk

                # Get object metadata to determine content type
                object_meta = await src_s3_client.get_object_meta(key)
                ctype = (
                    (object_meta.content_type if object_meta else None)
                    or mimetypes.guess_type(key)[0]
                    or "application/octet-stream"
                )

                part_size = self._storage_configs[storage_name].upload_chunk_size
                await dst_client.upload_stream(
                    _data_stream(),
                    key,  # same key at destination
                    content_type=ctype,
                    part_size=part_size,
                )

                log.trace("[stream_bucket_to_bucket] done key={} bytes={}", key, size)

        await asyncio.gather(*(_copy_single_object(k) for k in target_keys))
        copied = len(target_keys)

        log.trace(
            "[stream_bucket_to_bucket] all done objects={} total_bytes={}", copied, total_bytes
        )
        return copied
