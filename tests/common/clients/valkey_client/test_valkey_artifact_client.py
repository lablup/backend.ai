from __future__ import annotations

import asyncio
import random
from typing import AsyncGenerator, cast

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.exception import ClientNotConnectedError


class TestValkeyArtifactDownloadTrackingClient:
    """Test cases for ValkeyArtifactDownloadTrackingClient"""

    @pytest.fixture
    async def valkey_client_with_cleanup(
        self,
        test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
    ) -> AsyncGenerator[ValkeyArtifactDownloadTrackingClient, None]:
        """Valkey client that auto-cleans artifact tracking data after each test"""
        yield test_valkey_artifact

        # Cleanup all artifact tracking data after test
        # Skip if client is already closed (e.g., in test_client_lifecycle)
        try:
            cursor = b"0"
            while cursor:
                result = await test_valkey_artifact._client.client.scan(
                    cursor, match="artifact:*", count=100
                )
                cursor = cast(bytes, result[0])
                keys = cast(list[bytes], result[1])
                if keys:
                    await test_valkey_artifact._client.client.delete(cast(list[str | bytes], keys))
                if cursor == b"0":
                    break
        except ClientNotConnectedError:
            # Client already closed, skip cleanup
            pass

    async def test_init_artifact_download(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test initializing artifact download tracking"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"
        total_files = 10
        total_bytes = 1000000
        file_info_list = [(f"file{i}.bin", 100000) for i in range(10)]

        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=file_info_list,
        )

        # Verify artifact data was stored
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )

        assert artifact_data is not None
        assert artifact_data.model_id == model_id
        assert artifact_data.revision == revision
        assert artifact_data.total_files == total_files
        assert artifact_data.total_bytes == total_bytes
        assert artifact_data.completed_files == 0
        assert artifact_data.downloaded_bytes == 0
        assert artifact_data.start_time > 0
        assert artifact_data.last_updated > 0
        assert artifact_data.last_updated == artifact_data.start_time

    async def test_update_file_progress(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test updating file download progress"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"
        file_path = "model.bin"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[(file_path, 1000)],
        )

        # Update file progress
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
            current_bytes=500,
            total_bytes=1000,
        )

        # Verify file progress
        file_data = await valkey_client_with_cleanup.get_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
        )

        assert file_data is not None
        assert file_data.file_path == file_path
        assert file_data.current_bytes == 500
        assert file_data.total_bytes == 1000
        assert file_data.success is False
        assert file_data.last_updated > 0

    async def test_update_file_progress_aggregation(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test that file progress updates are aggregated to artifact level"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[("file1.bin", 1000), ("file2.bin", 1000), ("file3.bin", 1000)],
        )

        # Update first file partially
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
            current_bytes=500,
            total_bytes=1000,
        )

        # Check artifact progress
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is not None
        assert artifact_data.downloaded_bytes == 500
        assert artifact_data.completed_files == 0
        start_last_updated = artifact_data.last_updated

        # Complete first file
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
            current_bytes=1000,
            total_bytes=1000,
            success=True,
        )

        # Check artifact progress after completion
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is not None
        assert artifact_data.downloaded_bytes == 1000
        assert artifact_data.completed_files == 1

        # Update second file
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file2.bin",
            current_bytes=1000,
            total_bytes=1000,
            success=True,
        )

        # Check final artifact progress
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is not None
        assert artifact_data.downloaded_bytes == 2000
        assert artifact_data.completed_files == 2
        assert artifact_data.last_updated > start_last_updated  # Should be updated

    async def test_update_file_progress_with_error(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test recording file download errors"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"
        file_path = "model.bin"
        error_msg = "Connection timeout"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[(file_path, 1000)],
        )

        # Update with error
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
            current_bytes=300,
            total_bytes=1000,
            success=False,
            error_message=error_msg,
        )

        # Verify error was recorded
        file_data = await valkey_client_with_cleanup.get_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
        )

        assert file_data is not None
        assert file_data.success is False
        assert file_data.current_bytes == 300
        assert file_data.error_message == error_msg

    async def test_file_progress_ttl_preservation(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test that TTL is preserved across updates (KEEP_TTL behavior)"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"
        file_path = "model.bin"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[(file_path, 1000)],
        )

        # First update
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
            current_bytes=500,
            total_bytes=1000,
        )

        # Get initial TTL (should be close to 24 hours = 86400 seconds)
        artifact_key = valkey_client_with_cleanup._get_artifact_key(model_id, revision)
        initial_ttl = await valkey_client_with_cleanup._client.client.ttl(artifact_key)
        assert initial_ttl is not None
        assert initial_ttl > 86000  # Should be close to 24 hours

        # Wait a bit
        await asyncio.sleep(2)

        # Second update
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
            current_bytes=800,
            total_bytes=1000,
        )

        # Check TTL again - should be roughly 2 seconds less, not reset
        updated_ttl = await valkey_client_with_cleanup._client.client.ttl(artifact_key)
        assert updated_ttl is not None
        # TTL should have decreased by ~2 seconds (with some tolerance)
        assert abs((initial_ttl - updated_ttl) - 2) < 2  # Within 2 second tolerance

    async def test_cleanup_artifact_download(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test cleaning up artifact download data"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"

        # Initialize and add some data
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[("file1.bin", 1000), ("file2.bin", 1000)],
        )

        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
            current_bytes=500,
            total_bytes=1000,
        )

        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file2.bin",
            current_bytes=1000,
            total_bytes=1000,
            success=True,
        )

        # Verify data exists
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is not None

        # Cleanup
        await valkey_client_with_cleanup.cleanup_artifact_download(
            model_id=model_id,
            revision=revision,
        )

        # Verify data was deleted
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is None

        file_data = await valkey_client_with_cleanup.get_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
        )
        assert file_data is None

    async def test_get_nonexistent_artifact(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test querying nonexistent artifact returns None"""
        model_id = f"nonexistent-{random.randint(1000, 9999)}"
        revision = "main"

        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is None

        file_data = await valkey_client_with_cleanup.get_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file.bin",
        )
        assert file_data is None

    async def test_client_lifecycle(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test client lifecycle management"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"

        # Client should be working
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[("model.bin", 1000)],
        )

        result = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert result is not None

        # Close should work without errors
        await valkey_client_with_cleanup.close()

        # Second close should not raise an error
        await valkey_client_with_cleanup.close()

    async def test_special_characters_in_model_id(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test handling model IDs with special characters"""
        model_id = f"org/model-name_{random.randint(1000, 9999)}"
        revision = "v1.0.0"
        file_path = "subfolder/model.bin"

        # Initialize with special characters
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[(file_path, 1000)],
        )

        # Update file progress
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
            current_bytes=500,
            total_bytes=1000,
            success=True,
        )

        # Verify data can be retrieved
        artifact_data = await valkey_client_with_cleanup.get_artifact_progress(
            model_id=model_id,
            revision=revision,
        )
        assert artifact_data is not None
        assert artifact_data.model_id == model_id

        file_data = await valkey_client_with_cleanup.get_file_progress(
            model_id=model_id,
            revision=revision,
            file_path=file_path,
        )
        assert file_data is not None
        assert file_data.file_path == file_path

    async def test_get_all_file_progress(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test retrieving all file progress for an artifact"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[("file1.bin", 1000), ("file2.bin", 1000), ("file3.bin", 1000)],
        )

        # Add progress for multiple files
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
            current_bytes=100,
            total_bytes=1000,
        )
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file2.bin",
            current_bytes=200,
            total_bytes=1000,
        )
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file3.bin",
            current_bytes=300,
            total_bytes=1000,
            success=True,
        )

        # Get all file progress
        all_progress = await valkey_client_with_cleanup.get_all_file_progress(
            model_id=model_id,
            revision=revision,
        )

        assert len(all_progress) == 3
        file_paths = {fp.file_path for fp in all_progress}
        assert "file1.bin" in file_paths
        assert "file2.bin" in file_paths
        assert "file3.bin" in file_paths

        file1 = next(fp for fp in all_progress if fp.file_path == "file1.bin")
        file2 = next(fp for fp in all_progress if fp.file_path == "file2.bin")
        file3 = next(fp for fp in all_progress if fp.file_path == "file3.bin")

        assert file1.current_bytes == 100
        assert file2.current_bytes == 200
        assert file3.current_bytes == 300
        assert file3.success is True

    async def test_get_download_progress(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test retrieving download progress (artifact + all files)"""
        model_id = f"test-model-{random.randint(1000, 9999)}"
        revision = "main"

        # Initialize artifact
        await valkey_client_with_cleanup.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=[("file1.bin", 1000), ("file2.bin", 1000)],
        )

        # Add progress for multiple files
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file1.bin",
            current_bytes=500,
            total_bytes=1000,
        )
        await valkey_client_with_cleanup.update_file_progress(
            model_id=model_id,
            revision=revision,
            file_path="file2.bin",
            current_bytes=1000,
            total_bytes=1000,
            success=True,
        )

        # Get complete progress in one call
        progress = await valkey_client_with_cleanup.get_download_progress(
            model_id=model_id,
            revision=revision,
        )

        # Verify artifact-level progress
        assert progress.artifact_progress is not None
        assert progress.artifact_progress.model_id == model_id
        assert progress.artifact_progress.revision == revision
        assert progress.artifact_progress.total_files == 2
        assert progress.artifact_progress.total_bytes == 2000
        assert progress.artifact_progress.downloaded_bytes == 1500
        assert progress.artifact_progress.completed_files == 1

        # Verify file-level progress
        assert len(progress.file_progress) == 2
        file_paths = {fp.file_path for fp in progress.file_progress}
        assert "file1.bin" in file_paths
        assert "file2.bin" in file_paths

        file1 = next(fp for fp in progress.file_progress if fp.file_path == "file1.bin")
        file2 = next(fp for fp in progress.file_progress if fp.file_path == "file2.bin")

        assert file1.current_bytes == 500
        assert file1.success is False
        assert file2.current_bytes == 1000
        assert file2.success is True

    async def test_get_download_progress_nonexistent(
        self,
        valkey_client_with_cleanup: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        """Test retrieving progress for nonexistent artifact"""
        model_id = f"nonexistent-{random.randint(1000, 9999)}"
        revision = "main"

        progress = await valkey_client_with_cleanup.get_download_progress(
            model_id=model_id,
            revision=revision,
        )

        assert progress.artifact_progress is None
        assert len(progress.file_progress) == 0
