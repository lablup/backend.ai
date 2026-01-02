from __future__ import annotations

import hashlib
import logging
import time
from typing import Final, Optional, Self, cast

from glide import Batch, ExpirySet, ExpiryType
from pydantic import ValidationError

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.artifact.types import (
    ArtifactDownloadTrackingData,
    DownloadProgressData,
    FileDownloadProgressData,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Resilience instance for valkey_artifact layer
valkey_artifact_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_ARTIFACT)),
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

_ARTIFACT_DOWNLOAD_PREFIX: Final[str] = "artifact:download"
_ARTIFACT_DOWNLOAD_EXPIRATION: Final[int] = 86400  # 24 hours


class ValkeyArtifactDownloadTrackingClient:
    """
    Client for managing artifact download tracking using Valkey.
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
        Create a ValkeyArtifactDownloadTrackingClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name of the client.
        :return: An instance of ValkeyArtifactDownloadTrackingClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_artifact_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyArtifactDownloadTrackingClient connection.
        """
        if self._closed:
            log.debug("ValkeyArtifactDownloadTrackingClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch for transaction operations.

        :param is_atomic: Whether the batch should be atomic.
        :return: A Batch instance.
        """
        return Batch(is_atomic=is_atomic)

    def _get_artifact_key(self, model_id: str, revision: str) -> str:
        """
        Generate Redis key for artifact-level tracking.

        :param model_id: Model identifier
        :param revision: Model revision
        :return: Redis key string
        """
        # URL-encode model_id and revision to handle special characters
        safe_model_id = model_id.replace("/", ":")
        safe_revision = revision.replace("/", ":")
        return f"{_ARTIFACT_DOWNLOAD_PREFIX}:{safe_model_id}:{safe_revision}"

    def _get_file_key(self, model_id: str, revision: str, file_path: str) -> str:
        """
        Generate Redis key for file-level tracking.

        :param model_id: Model identifier
        :param revision: Model revision
        :param file_path: File path within the model
        :return: Redis key string
        """
        # Hash the file path to handle special characters and length
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        artifact_key = self._get_artifact_key(model_id, revision)
        return f"{artifact_key}:file:{file_hash}"

    def _get_file_pattern(self, model_id: str, revision: str) -> str:
        """
        Generate Redis key pattern for all files in an artifact.

        :param model_id: Model identifier
        :param revision: Model revision
        :return: Redis key pattern string
        """
        artifact_key = self._get_artifact_key(model_id, revision)
        return f"{artifact_key}:file:*"

    @valkey_artifact_resilience.apply()
    async def init_artifact_download(
        self,
        model_id: str,
        revision: str,
        file_info_list: list[tuple[str, int]],
    ) -> None:
        """
        Initialize artifact download tracking in Redis.
        Pre-registers all files with initial progress (0 bytes downloaded).

        :param model_id: Model identifier
        :param revision: Model revision
        :param file_info_list: List of (file_path, file_size) tuples
        """
        artifact_key = self._get_artifact_key(model_id, revision)
        current_time = time.time()

        total_files = len(file_info_list)
        total_bytes = sum(size for _, size in file_info_list)

        batch = self._create_batch(is_atomic=False)

        # Set artifact-level data as Hash for atomic field updates
        batch.hset(
            artifact_key,
            {
                "model_id": model_id,
                "revision": revision,
                "start_time": str(current_time),
                "last_updated": str(current_time),
                "total_files": str(total_files),
                "total_bytes": str(total_bytes),
                "completed_files": "0",
                "downloaded_bytes": "0",
            },
        )
        # Set TTL for artifact hash
        batch.expire(artifact_key, _ARTIFACT_DOWNLOAD_EXPIRATION)

        # Pre-register all files with initial progress (0 bytes)
        for file_path, file_size in file_info_list:
            file_key = self._get_file_key(model_id, revision, file_path)
            file_data = FileDownloadProgressData(
                file_path=file_path,
                success=False,
                current_bytes=0,
                total_bytes=file_size,
                last_updated=current_time,
                error_message=None,
            )
            batch.set(
                file_key,
                file_data.model_dump_json(),
                expiry=ExpirySet(
                    expiry_type=ExpiryType.SEC,
                    value=_ARTIFACT_DOWNLOAD_EXPIRATION,
                ),
            )

        await self._client.client.exec(batch, raise_on_error=True)
        log.debug(
            "Initialized artifact download tracking: model_id={}, revision={}, total_files={}, total_bytes={}",
            model_id,
            revision,
            total_files,
            total_bytes,
        )

    @valkey_artifact_resilience.apply()
    async def update_file_progress(
        self,
        model_id: str,
        revision: str,
        file_path: str,
        current_bytes: int,
        total_bytes: int,
        success: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update file download progress in Redis.

        :param model_id: Model identifier
        :param revision: Model revision
        :param file_path: File path within the model
        :param current_bytes: Current bytes downloaded for this file
        :param total_bytes: Total bytes for this file
        :param success: Whether the download completed successfully
        :param error_message: Error message if download failed
        """
        file_key = self._get_file_key(model_id, revision, file_path)
        artifact_key = self._get_artifact_key(model_id, revision)

        # Get previous file data to calculate delta for artifact aggregation
        previous_data_bytes = await self._client.client.get(file_key)
        previous_current_bytes = 0
        if previous_data_bytes:
            try:
                previous_data = FileDownloadProgressData.model_validate_json(previous_data_bytes)
                previous_current_bytes = previous_data.current_bytes
            except (ValidationError, UnicodeDecodeError):
                log.warning("Failed to parse previous file data for progress update")

        # Calculate bytes delta for artifact aggregation
        bytes_delta = current_bytes - previous_current_bytes

        file_data = FileDownloadProgressData(
            file_path=file_path,
            success=success,
            current_bytes=current_bytes,
            total_bytes=total_bytes,
            last_updated=time.time(),
            error_message=error_message,
        )

        # Update file progress (file key should already exist from init_artifact_download)
        batch = self._create_batch(is_atomic=False)
        batch.set(
            file_key,
            file_data.model_dump_json(),
            expiry=ExpirySet(expiry_type=ExpiryType.KEEP_TTL, value=None),
        )

        await self._client.client.exec(batch, raise_on_error=True)

        # Update artifact aggregates atomically using HINCRBY
        if bytes_delta != 0 or (success and previous_current_bytes < total_bytes):
            current_time_str = str(time.time())

            # Use HINCRBY for atomic increments
            if bytes_delta != 0:
                await self._client.client.hincrby(artifact_key, "downloaded_bytes", bytes_delta)

            if success and previous_current_bytes < total_bytes:
                await self._client.client.hincrby(artifact_key, "completed_files", 1)

            # Update last_updated timestamp
            await self._client.client.hset(artifact_key, {"last_updated": current_time_str})

        log.trace(
            "Updated file progress: file_path={}, current={}, total={}, success={}",
            file_path,
            current_bytes,
            total_bytes,
            success,
        )

    @valkey_artifact_resilience.apply()
    async def get_artifact_progress(
        self,
        model_id: str,
        revision: str,
    ) -> Optional[ArtifactDownloadTrackingData]:
        """
        Get overall artifact download progress.

        :param model_id: Model identifier
        :param revision: Model revision
        :return: Artifact progress data or None if not found
        """
        artifact_key = self._get_artifact_key(model_id, revision)
        hash_data = await self._client.client.hgetall(artifact_key)

        if not hash_data:
            return None

        try:
            # Convert Hash data (bytes keys/values) to proper types
            return ArtifactDownloadTrackingData(
                model_id=hash_data[b"model_id"].decode(),
                revision=hash_data[b"revision"].decode(),
                start_time=float(hash_data[b"start_time"].decode()),
                last_updated=float(hash_data[b"last_updated"].decode()),
                total_files=int(hash_data[b"total_files"].decode()),
                total_bytes=int(hash_data[b"total_bytes"].decode()),
                completed_files=int(hash_data[b"completed_files"].decode()),
                downloaded_bytes=int(hash_data[b"downloaded_bytes"].decode()),
            )
        except (KeyError, ValueError, UnicodeDecodeError) as e:
            log.warning("Failed to parse artifact progress data from hash: {}", str(e))
            return None

    @valkey_artifact_resilience.apply()
    async def get_file_progress(
        self,
        model_id: str,
        revision: str,
        file_path: str,
    ) -> Optional[FileDownloadProgressData]:
        """
        Get specific file download progress.

        :param model_id: Model identifier
        :param revision: Model revision
        :param file_path: File path within the model
        :return: File progress data or None if not found
        """
        file_key = self._get_file_key(model_id, revision, file_path)
        data_bytes = await self._client.client.get(file_key)

        if not data_bytes:
            return None

        try:
            return FileDownloadProgressData.model_validate_json(data_bytes)
        except (ValidationError, UnicodeDecodeError):
            log.warning("Failed to parse file progress data")
            return None

    @valkey_artifact_resilience.apply()
    async def get_all_file_progress(
        self,
        model_id: str,
        revision: str,
    ) -> list[FileDownloadProgressData]:
        """
        Get all file download progress for an artifact.

        :param model_id: Model identifier
        :param revision: Model revision
        :return: List of file progress data
        """
        file_pattern = self._get_file_pattern(model_id, revision)
        file_progress_list: list[FileDownloadProgressData] = []

        cursor = b"0"
        while cursor:
            result = await self._client.client.scan(cursor, match=file_pattern, count=100)
            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])

            if keys:
                # Get all file progress data
                values = await self._client.client.mget(cast(list[str | bytes], keys))
                for key_bytes, value_bytes in zip(keys, values, strict=False):
                    if value_bytes:
                        try:
                            file_progress = FileDownloadProgressData.model_validate_json(
                                value_bytes
                            )
                            file_progress_list.append(file_progress)
                        except (ValidationError, UnicodeDecodeError):
                            log.warning("Failed to parse file progress data for key: {}", key_bytes)

            if cursor == b"0":
                break

        return file_progress_list

    @valkey_artifact_resilience.apply()
    async def get_download_progress(
        self,
        model_id: str,
        revision: str,
    ) -> DownloadProgressData:
        """
        Get download progress including artifact-level and all file-level data.

        This is a convenience method that combines get_artifact_progress() and
        get_all_file_progress() into a single call.

        :param model_id: Model identifier
        :param revision: Model revision
        :return: Download progress data
        """
        artifact_progress = await self.get_artifact_progress(model_id, revision)
        file_progress = await self.get_all_file_progress(model_id, revision)
        return DownloadProgressData(
            artifact_progress=artifact_progress,
            file_progress=file_progress,
        )

    @valkey_artifact_resilience.apply()
    async def cleanup_artifact_download(
        self,
        model_id: str,
        revision: str,
    ) -> None:
        """
        Clean up all Redis keys for an artifact download.

        :param model_id: Model identifier
        :param revision: Model revision
        """
        artifact_key = self._get_artifact_key(model_id, revision)
        file_pattern = self._get_file_pattern(model_id, revision)

        # Delete artifact key
        await self._client.client.delete([artifact_key])

        # Find and delete all file keys
        # Note: SCAN is more efficient than KEYS for production use
        cursor = b"0"
        while True:
            result = await self._client.client.scan(cursor, match=file_pattern, count=100)
            if result is None or len(result) != 2:
                break

            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])
            if keys:
                await self._client.client.delete(cast(list[str | bytes], keys))

            if cursor == b"0":
                break

        log.debug(
            "Cleaned up artifact download tracking: model_id={}, revision={}",
            model_id,
            revision,
        )
