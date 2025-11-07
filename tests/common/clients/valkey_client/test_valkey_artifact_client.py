from __future__ import annotations

import asyncio
import random

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)


@pytest.mark.redis
async def test_init_artifact_download(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test initializing artifact download tracking"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"
    total_files = 10
    total_bytes = 1000000

    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=total_files,
        total_bytes=total_bytes,
    )

    # Verify artifact data was stored
    artifact_data = await test_valkey_artifact.get_artifact_progress(
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


@pytest.mark.redis
async def test_update_file_progress(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test updating file download progress"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"
    file_path = "model.bin"

    # Initialize artifact first
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=1,
        total_bytes=1000,
    )

    # Update file progress
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
        current_bytes=500,
        total_bytes=1000,
    )

    # Verify file progress
    file_data = await test_valkey_artifact.get_file_progress(
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


@pytest.mark.redis
async def test_update_file_progress_aggregation(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test that file progress updates are aggregated to artifact level"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"
    total_files = 3
    total_bytes = 3000

    # Initialize artifact
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=total_files,
        total_bytes=total_bytes,
    )

    # Update first file partially
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file1.bin",
        current_bytes=500,
        total_bytes=1000,
    )

    # Check artifact progress
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is not None
    assert artifact_data.downloaded_bytes == 500
    assert artifact_data.completed_files == 0

    # Complete first file
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file1.bin",
        current_bytes=1000,
        total_bytes=1000,
        success=True,
    )

    # Check artifact progress after completion
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is not None
    assert artifact_data.downloaded_bytes == 1000
    assert artifact_data.completed_files == 1

    # Update second file
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file2.bin",
        current_bytes=1000,
        total_bytes=1000,
        success=True,
    )

    # Check final artifact progress
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is not None
    assert artifact_data.downloaded_bytes == 2000
    assert artifact_data.completed_files == 2


@pytest.mark.redis
async def test_update_file_progress_with_error(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test updating file progress with error message"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"
    file_path = "model.bin"
    error_msg = "Connection timeout"

    # Initialize artifact
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=1,
        total_bytes=1000,
    )

    # Update with error
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
        current_bytes=300,
        total_bytes=1000,
        success=False,
        error_message=error_msg,
    )

    # Verify error was recorded
    file_data = await test_valkey_artifact.get_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
    )

    assert file_data is not None
    assert file_data.success is False
    assert file_data.error_message == error_msg


@pytest.mark.redis
async def test_file_progress_ttl_preservation(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test that TTL is preserved across updates (KEEP_TTL behavior)"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"
    file_path = "model.bin"

    # Initialize artifact
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=1,
        total_bytes=1000,
    )

    # First update
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
        current_bytes=500,
        total_bytes=1000,
    )

    # Get initial TTL (should be close to 24 hours = 86400 seconds)
    artifact_key = test_valkey_artifact._get_artifact_key(model_id, revision)
    initial_ttl = await test_valkey_artifact._client.client.ttl(artifact_key)
    assert initial_ttl is not None
    assert initial_ttl > 86000  # Should be close to 24 hours

    # Wait a bit
    await asyncio.sleep(2)

    # Second update
    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
        current_bytes=800,
        total_bytes=1000,
    )

    # Check TTL again - should be roughly 2 seconds less, not reset
    updated_ttl = await test_valkey_artifact._client.client.ttl(artifact_key)
    assert updated_ttl is not None
    # TTL should have decreased, not reset to 86400
    assert updated_ttl < initial_ttl
    assert abs(updated_ttl - (initial_ttl - 2)) < 5  # Allow 5 second margin


@pytest.mark.redis
async def test_cleanup_artifact_download(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test cleaning up artifact download tracking data"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"

    # Initialize artifact and add some file progress
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=2,
        total_bytes=2000,
    )

    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file1.bin",
        current_bytes=1000,
        total_bytes=1000,
        success=True,
    )

    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file2.bin",
        current_bytes=500,
        total_bytes=1000,
    )

    # Verify data exists
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is not None

    # Cleanup
    await test_valkey_artifact.cleanup_artifact_download(
        model_id=model_id,
        revision=revision,
    )

    # Verify data was deleted
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is None

    file_data = await test_valkey_artifact.get_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file1.bin",
    )
    assert file_data is None


@pytest.mark.redis
async def test_get_nonexistent_artifact(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test querying nonexistent artifact returns None"""
    model_id = f"nonexistent-{random.randint(1000, 9999)}"
    revision = "main"

    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is None

    file_data = await test_valkey_artifact.get_file_progress(
        model_id=model_id,
        revision=revision,
        file_path="file.bin",
    )
    assert file_data is None


@pytest.mark.redis
async def test_client_lifecycle(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test client lifecycle management"""
    model_id = f"test-model-{random.randint(1000, 9999)}"
    revision = "main"

    # Client should be working
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=1,
        total_bytes=1000,
    )

    result = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert result is not None

    # Close should work without errors
    await test_valkey_artifact.close()

    # Second close should not raise an error
    await test_valkey_artifact.close()


@pytest.mark.redis
async def test_special_characters_in_model_id(
    test_valkey_artifact: ValkeyArtifactDownloadTrackingClient,
) -> None:
    """Test handling model IDs with special characters (e.g., slashes)"""
    model_id = f"organization/model-name-{random.randint(1000, 9999)}"
    revision = "v1.0/beta"
    file_path = "subfolder/model.bin"

    # Initialize and update
    await test_valkey_artifact.init_artifact_download(
        model_id=model_id,
        revision=revision,
        total_files=1,
        total_bytes=1000,
    )

    await test_valkey_artifact.update_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
        current_bytes=1000,
        total_bytes=1000,
        success=True,
    )

    # Verify data can be retrieved
    artifact_data = await test_valkey_artifact.get_artifact_progress(
        model_id=model_id,
        revision=revision,
    )
    assert artifact_data is not None
    assert artifact_data.model_id == model_id

    file_data = await test_valkey_artifact.get_file_progress(
        model_id=model_id,
        revision=revision,
        file_path=file_path,
    )
    assert file_data is not None
    assert file_data.file_path == file_path
