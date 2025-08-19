import dataclasses
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.artifact.types import ArtifactType
from ai.backend.manager.repositories.artifact.repository import (
    ArtifactFilterOptions,
    ArtifactOffsetBasedPaginationOptions,
    ArtifactOrderingField,
    ArtifactOrderingOptions,
    ForwardPaginationOptions,
)
from ai.backend.manager.services.artifact.actions.list import (
    ListArtifactsAction,
    ListArtifactsActionResult,
)
from ai.backend.manager.services.artifact.service import ArtifactService

from ..fixtures import (
    ARTIFACT_FIXTURE_DATA_1,
    ARTIFACT_FIXTURE_DATA_2,
    ARTIFACT_FIXTURE_DATA_3,
)


# Tests with repository mocked but service logic executed
@pytest.mark.asyncio
async def test_list_artifacts_with_repository_mock():
    """Test list artifacts with mocked repository but real service logic"""
    # Create mock repository
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        [ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
        2,
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service with mocked repository
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test the action - this executes REAL service logic
    action = ListArtifactsAction(pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2))
    result = await service.list(action)

    # Verify repository was called with correct parameters
    mock_artifact_repository.list_artifacts_paginated.assert_called_once()
    call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
    assert call_kwargs["pagination"].offset == 0
    assert call_kwargs["pagination"].limit == 2

    # Verify results
    assert len(result.data) == 2
    assert result.total_count == 2
    assert result.data[0].id == ARTIFACT_FIXTURE_DATA_1.id
    assert result.data[1].id == ARTIFACT_FIXTURE_DATA_2.id


@pytest.mark.asyncio
async def test_list_artifacts_with_filtering_logic():
    """Test list artifacts filtering logic with real service"""
    # Create mock repository that returns BERT model when filtered
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        [ARTIFACT_FIXTURE_DATA_3],  # Only BERT model matches filter
        1,
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Create action with filtering - tests REAL service filtering logic
    action = ListArtifactsAction(filters=ArtifactFilterOptions(name_filter="bert"))

    # Execute REAL service logic
    result = await service.list(action)

    # Verify repository was called with correct filter parameters
    mock_artifact_repository.list_artifacts_paginated.assert_called_once()
    call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
    assert call_kwargs["filters"].name_filter == "bert"

    # Verify results
    assert len(result.data) == 1
    assert result.total_count == 1
    assert result.data[0].name == "google/bert-base-uncased"


@pytest.mark.asyncio
async def test_list_artifacts_with_database_error():
    """Test list artifacts handling database errors through real service"""
    # Create mock repository that raises an exception
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.side_effect = RuntimeError(
        "Database connection failed"
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service with failing repository
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # The service should propagate the database error
    action = ListArtifactsAction()
    with pytest.raises(RuntimeError, match="Database connection failed"):
        await service.list(action)


@pytest.mark.asyncio
async def test_list_artifacts_with_large_dataset():
    """Test list artifacts with large dataset using real service"""
    # Create a large mock dataset
    large_dataset = []
    for i in range(1000):
        artifact_data = dataclasses.replace(
            ARTIFACT_FIXTURE_DATA_1, id=uuid.UUID(int=i), name=f"test-artifact-{i}"
        )
        large_dataset.append(artifact_data)

    # Mock repository to return large dataset
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        large_dataset[:100],  # First 100 items
        1000,  # Total count
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test pagination with large dataset - tests REAL service logic
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=100)
    )
    result = await service.list(action)

    # Verify repository was called with correct pagination
    mock_artifact_repository.list_artifacts_paginated.assert_called_once()
    call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
    assert call_kwargs["pagination"].offset == 0
    assert call_kwargs["pagination"].limit == 100

    # Verify pagination works with large dataset
    assert len(result.data) == 100
    assert result.total_count == 1000
    assert result.data[0].name == "test-artifact-0"
    assert result.data[99].name == "test-artifact-99"


# Error handling tests with real service logic
@pytest.mark.asyncio
async def test_list_artifacts_invalid_pagination_parameters():
    """Test error handling for invalid pagination parameters with real service"""

    # Mock repository that handles edge cases
    mock_artifact_repository = AsyncMock()

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test negative offset - repository returns empty result
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 3)

    result = await service.list(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=-1, limit=10),
        )
    )
    assert isinstance(result, ListArtifactsActionResult)
    assert len(result.data) == 0

    # Test zero limit - repository returns empty results
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 3)

    result = await service.list(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=0),
        )
    )
    assert len(result.data) == 0

    # Test very large offset - repository returns empty results
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 3)

    result = await service.list(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=10000, limit=10),
        )
    )
    assert len(result.data) == 0
    assert result.total_count == 3  # Total count should still be accurate


@pytest.mark.asyncio
async def test_list_artifacts_invalid_connection_parameters():
    """Test error handling for invalid connection pagination parameters with real service"""

    # Mock repository that handles edge cases gracefully
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = ([ARTIFACT_FIXTURE_DATA_1], 1)

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test invalid cursor (non-UUID string) - real service handles this
    result = await service.list(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(after="invalid-cursor", first=2),
        )
    )
    # Should handle gracefully and return results (ignoring invalid cursor)
    assert isinstance(result, ListArtifactsActionResult)

    # Test negative first parameter - real service handles this
    result = await service.list(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(first=-1),
        )
    )
    # Should handle gracefully
    assert isinstance(result, ListArtifactsActionResult)

    # Test non-existent cursor UUID - real service handles this
    non_existent_uuid = str(uuid.uuid4())
    result = await service.list(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(after=non_existent_uuid, first=2),
        )
    )
    # Should return results (cursor not found, so pagination starts from beginning)
    assert isinstance(result, ListArtifactsActionResult)


@pytest.mark.asyncio
async def test_list_artifacts_with_conflicting_pagination_params():
    """Test behavior when both pagination and connection params are provided"""
    # Mock repository
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = ([ARTIFACT_FIXTURE_DATA_1], 1)

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Action with both pagination types - real service decides which to use
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2),
        forward=ForwardPaginationOptions(first=3),
    )

    result = await service.list(action)

    # Should handle gracefully and return results
    assert isinstance(result, ListArtifactsActionResult)

    # Verify repository was called (service logic executed)
    mock_artifact_repository.list_artifacts_paginated.assert_called_once()


# Edge case tests with real service logic
@pytest.mark.asyncio
async def test_list_artifacts_empty_database():
    """Test listing artifacts when database is empty"""

    # Mock repository returning empty results
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 0)

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    result = await service.list(ListArtifactsAction())

    assert len(result.data) == 0
    assert result.total_count == 0


@pytest.mark.asyncio
async def test_list_artifacts_single_item_database():
    """Test listing artifacts when database has only one item"""

    # Mock repository
    mock_artifact_repository = AsyncMock()

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test default pagination - return single item
    mock_artifact_repository.list_artifacts_paginated.return_value = ([ARTIFACT_FIXTURE_DATA_1], 1)

    result = await service.list(ListArtifactsAction())
    assert len(result.data) == 1
    assert result.total_count == 1

    # Test with offset beyond single item - return empty
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 1)

    result = await service.list(
        ListArtifactsAction(pagination=ArtifactOffsetBasedPaginationOptions(offset=1, limit=10))
    )
    assert len(result.data) == 0
    assert result.total_count == 1  # Total count should still be 1


@pytest.mark.asyncio
async def test_list_artifacts_all_ordering_fields():
    """Test all available ordering fields with real service"""

    # Test each ordering field
    ordering_fields = [
        ArtifactOrderingField.CREATED_AT,
        ArtifactOrderingField.UPDATED_AT,
        ArtifactOrderingField.NAME,
        ArtifactOrderingField.SIZE,
        ArtifactOrderingField.TYPE,
    ]

    # Mock repository
    mock_artifact_repository = AsyncMock()
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        [ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2, ARTIFACT_FIXTURE_DATA_3],
        3,
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    for field in ordering_fields:
        for desc in [True, False]:
            result = await service.list(
                ListArtifactsAction(
                    ordering=ArtifactOrderingOptions(
                        order_by=field,
                        order_desc=desc,
                    )
                )
            )

            # Verify repository was called with correct ordering parameters
            call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
            assert call_kwargs["ordering"].order_by == field
            assert call_kwargs["ordering"].order_desc == desc

            # Should return all artifacts with specified ordering
            assert len(result.data) == 3
            assert result.total_count == 3

            # Verify ordering is consistent (all results returned)
            artifact_ids = [artifact.id for artifact in result.data]
            assert len(set(artifact_ids)) == 3  # No duplicates


@pytest.mark.asyncio
async def test_list_artifacts_complex_filter_combinations():
    """Test complex combinations of filters with real service"""

    # Mock repository
    mock_artifact_repository = AsyncMock()

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test multiple filters combined - return matching artifact
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        [ARTIFACT_FIXTURE_DATA_3],  # BERT model which matches filters
        1,
    )

    result = await service.list(
        ListArtifactsAction(
            filters=ArtifactFilterOptions(
                artifact_type=ArtifactType.MODEL,
                authorized=True,
                name_filter="bert",
            )
        )
    )

    # Verify repository was called with correct filter parameters
    call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
    assert call_kwargs["filters"].artifact_type == ArtifactType.MODEL
    assert call_kwargs["filters"].authorized is True
    assert call_kwargs["filters"].name_filter == "bert"

    # Should return only artifacts that match all filters
    for artifact in result.data:
        assert artifact.type == ArtifactType.MODEL
        assert artifact.authorized is True
        assert "bert" in artifact.name.lower()

    # Test empty result from restrictive filters
    mock_artifact_repository.list_artifacts_paginated.return_value = ([], 0)

    result = await service.list(
        ListArtifactsAction(
            filters=ArtifactFilterOptions(
                authorized=True,
                name_filter="nonexistent",
            )
        )
    )

    assert len(result.data) == 0
    assert result.total_count == 0


@pytest.mark.asyncio
async def test_list_artifacts_performance_with_large_limit():
    """Test performance considerations with very large limits"""
    # Mock repository to simulate large dataset performance
    mock_artifact_repository = AsyncMock()

    # Simulate a large dataset response
    large_data = [ARTIFACT_FIXTURE_DATA_1] * 10000
    mock_artifact_repository.list_artifacts_paginated.return_value = (
        large_data[:5000],  # Return first 5000
        10000,
    )

    # Mock other dependencies
    mock_storage_manager = MagicMock()
    mock_object_storage_repository = AsyncMock()
    mock_huggingface_registry_repository = AsyncMock()

    # Create REAL service
    service = ArtifactService(
        artifact_repository=mock_artifact_repository,
        storage_manager=mock_storage_manager,
        object_storage_repository=mock_object_storage_repository,
        huggingface_registry_repository=mock_huggingface_registry_repository,
    )

    # Test with very large limit - real service handles this
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=5000)
    )

    result = await service.list(action)

    # Verify repository was called with correct parameters
    call_kwargs = mock_artifact_repository.list_artifacts_paginated.call_args[1]
    assert call_kwargs["pagination"].offset == 0
    assert call_kwargs["pagination"].limit == 5000

    # Verify large dataset handling
    assert len(result.data) == 5000
    assert result.total_count == 10000
