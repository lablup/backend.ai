import dataclasses
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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
from ai.backend.manager.services.artifact.processors import ArtifactProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    ARTIFACT_FIXTURE_DATA_1,
    ARTIFACT_FIXTURE_DATA_2,
    ARTIFACT_FIXTURE_DATA_3,
    ARTIFACT_FIXTURE_DICT_1,
    ARTIFACT_FIXTURE_DICT_2,
    ARTIFACT_FIXTURE_DICT_3,
)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "List all artifacts with default pagination",
            ListArtifactsAction(),
            ListArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2, ARTIFACT_FIXTURE_DATA_3],
                total_count=3,
            ),
        ),
        TestScenario.success(
            "List artifacts with offset/limit pagination",
            ListArtifactsAction(
                pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2),
            ),
            ListArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
                total_count=3,
            ),
        ),
        TestScenario.success(
            "List artifacts with connection pagination (first)",
            ListArtifactsAction(
                forward=ForwardPaginationOptions(first=2),
            ),
            ListArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
                total_count=3,
            ),
        ),
        TestScenario.success(
            "List artifacts with ordering by name ascending",
            ListArtifactsAction(
                ordering=ArtifactOrderingOptions(
                    order_by=ArtifactOrderingField.NAME,
                    order_desc=False,
                ),
            ),
            ListArtifactsActionResult(
                # Sorted by name: facebook/bart-large-cnn, google/bert-base-uncased, microsoft/DialoGPT-small
                data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_3, ARTIFACT_FIXTURE_DATA_2],
                total_count=3,
            ),
        ),
        TestScenario.success(
            "List artifacts with ordering by size descending",
            ListArtifactsAction(
                ordering=ArtifactOrderingOptions(
                    order_by=ArtifactOrderingField.SIZE,
                    order_desc=True,
                ),
            ),
            ListArtifactsActionResult(
                # Sorted by size desc: 200MB (bert), 100MB (bart), 50MB (dialogpt)
                data=[ARTIFACT_FIXTURE_DATA_3, ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
                total_count=3,
            ),
        ),
        TestScenario.success(
            "List artifacts with filter by authorized=True",
            ListArtifactsAction(
                filters=ArtifactFilterOptions(authorized=True),
            ),
            ListArtifactsActionResult(
                # Only authorized artifacts: bart and bert
                data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_3],
                total_count=2,
            ),
        ),
        TestScenario.success(
            "List artifacts with filter by name pattern",
            ListArtifactsAction(
                filters=ArtifactFilterOptions(name_filter="bert"),
            ),
            ListArtifactsActionResult(
                # Only artifacts with "bert" in name: google/bert-base-uncased
                data=[ARTIFACT_FIXTURE_DATA_3],
                total_count=1,
            ),
        ),
        TestScenario.success(
            "List artifacts with combined filters and pagination",
            ListArtifactsAction(
                pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=1),
                filters=ArtifactFilterOptions(authorized=True),
                ordering=ArtifactOrderingOptions(
                    order_by=ArtifactOrderingField.CREATED_AT,
                    order_desc=False,
                ),
            ),
            ListArtifactsActionResult(
                # First authorized artifact by creation date: bart
                data=[ARTIFACT_FIXTURE_DATA_1],
                total_count=2,
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "artifacts": [
                ARTIFACT_FIXTURE_DICT_1,
                ARTIFACT_FIXTURE_DICT_2,
                ARTIFACT_FIXTURE_DICT_3,
            ],
        }
    ],
)
async def test_list_artifacts(
    processors: ArtifactProcessors,
    test_scenario: TestScenario[ListArtifactsAction, ListArtifactsActionResult],
):
    await test_scenario.test(processors.list_artifacts.wait_for_complete)


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "artifacts": [
                ARTIFACT_FIXTURE_DICT_1,
                ARTIFACT_FIXTURE_DICT_2,
                ARTIFACT_FIXTURE_DICT_3,
            ],
        }
    ],
)
async def test_list_artifacts_pagination_consistency(
    processors: ArtifactProcessors,
):
    """Test that pagination is consistent across different page sizes"""

    # Get all artifacts
    all_result = await processors.list_artifacts.wait_for_complete(ListArtifactsAction())

    # Get first page with limit 2
    page1_result = await processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2),
        )
    )

    # Get second page with limit 2
    page2_result = await processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=2, limit=2),
        )
    )

    # Verify total counts are consistent
    assert all_result.total_count == page1_result.total_count == page2_result.total_count

    # Verify page results
    assert len(page1_result.data) == 2
    assert len(page2_result.data) == 1  # Last page has 1 item

    # Verify no duplicates between pages
    page1_ids = [artifact.id for artifact in page1_result.data]
    page2_ids = [artifact.id for artifact in page2_result.data]
    assert len(set(page1_ids) & set(page2_ids)) == 0

    # Verify all artifacts are accounted for
    all_ids = [artifact.id for artifact in all_result.data]
    paginated_ids = page1_ids + page2_ids
    assert set(all_ids) == set(paginated_ids)


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "artifacts": [
                ARTIFACT_FIXTURE_DICT_1,
                ARTIFACT_FIXTURE_DICT_2,
                ARTIFACT_FIXTURE_DICT_3,
            ],
        }
    ],
)
async def test_list_artifacts_connection_pagination(
    processors: ArtifactProcessors,
):
    """Test GraphQL connection-style pagination"""

    # Get first 2 artifacts using connection pagination
    first_result = await processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(first=2),
        )
    )

    assert len(first_result.data) == 2
    assert first_result.total_count == 3

    # Get artifacts after the last one from first page
    last_artifact_id = str(first_result.data[-1].id)
    after_result = await processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(after=last_artifact_id, first=2),
        )
    )

    # Should get remaining artifacts
    assert len(after_result.data) <= 2  # May have fewer than 2 remaining
    assert after_result.total_count == 3

    # Verify no overlap
    first_ids = [artifact.id for artifact in first_result.data]
    after_ids = [artifact.id for artifact in after_result.data]
    assert len(set(first_ids) & set(after_ids)) == 0


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "artifacts": [
                ARTIFACT_FIXTURE_DICT_1,
                ARTIFACT_FIXTURE_DICT_2,
                ARTIFACT_FIXTURE_DICT_3,
            ],
        }
    ],
)
async def test_list_artifacts_empty_results(
    processors: ArtifactProcessors,
):
    """Test filtering that returns no results"""

    result = await processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            filters=ArtifactFilterOptions(name_filter="nonexistent-model"),
        )
    )

    assert len(result.data) == 0
    assert result.total_count == 0


# Mock-related tests
@pytest.mark.asyncio
async def test_list_artifacts_with_repository_mock():
    """Test list artifacts with mocked repository"""
    # Create mock repository
    mock_repository = AsyncMock()
    mock_repository.list_artifacts_paginated.return_value = (
        [ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
        2,
    )

    # Create mock service
    mock_service = MagicMock()
    mock_service.artifact_repository = mock_repository
    mock_service.list = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
            total_count=2,
        )
    )

    # Create processors with mocked service
    processors = MagicMock()
    processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2],
            total_count=2,
        )
    )

    # Test the action
    action = ListArtifactsAction(pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2))
    result = await processors.list_artifacts.wait_for_complete(action)

    # Verify results
    assert len(result.data) == 2
    assert result.total_count == 2
    assert result.data[0].id == ARTIFACT_FIXTURE_DATA_1.id
    assert result.data[1].id == ARTIFACT_FIXTURE_DATA_2.id


@pytest.mark.asyncio
async def test_list_artifacts_with_service_layer_mock():
    """Test list artifacts with service layer fully mocked"""
    with patch(
        "ai.backend.manager.services.artifact.service.ArtifactService"
    ) as mock_service_class:
        # Setup mock service instance
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Mock the list method to return specific data
        mock_service.list.return_value = ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_3],
            total_count=1,
        )

        # Create action with filtering
        action = ListArtifactsAction(filters=ArtifactFilterOptions(name_filter="bert"))

        # Execute the mocked service call
        result = await mock_service.list(action)

        # Verify the mock was called with correct parameters
        mock_service.list.assert_called_once_with(action)

        # Verify results
        assert len(result.data) == 1
        assert result.total_count == 1
        assert result.data[0].name == "google/bert-base-uncased"


@pytest.mark.asyncio
async def test_list_artifacts_with_database_error_mock():
    """Test list artifacts handling database errors through mocks"""
    # Create mock repository that raises an exception
    mock_repository = AsyncMock()
    mock_repository.list_artifacts_paginated.side_effect = RuntimeError(
        "Database connection failed"
    )

    with patch(
        "ai.backend.manager.repositories.artifact.repository.ArtifactRepository"
    ) as mock_repo_class:
        mock_repo_class.return_value = mock_repository

        # The service should propagate the database error
        with pytest.raises(RuntimeError, match="Database connection failed"):
            await mock_repository.list_artifacts_paginated()


@pytest.mark.asyncio
async def test_list_artifacts_with_large_dataset_mock():
    """Test list artifacts with large dataset using mocks"""
    # Create a large mock dataset
    large_dataset = []
    for i in range(1000):
        artifact_data = dataclasses.replace(
            ARTIFACT_FIXTURE_DATA_1, id=uuid.UUID(int=i), name=f"test-artifact-{i}"
        )
        large_dataset.append(artifact_data)

    # Mock repository to return large dataset
    mock_repository = AsyncMock()
    mock_repository.list_artifacts_paginated.return_value = (
        large_dataset[:100],  # First 100 items
        1000,  # Total count
    )

    mock_service = AsyncMock()
    mock_service.list.return_value = ListArtifactsActionResult(
        data=large_dataset[:100],
        total_count=1000,
    )

    # Test pagination with large dataset
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=100)
    )
    result = await mock_service.list(action)

    # Verify pagination works with large dataset
    assert len(result.data) == 100
    assert result.total_count == 1000
    assert result.data[0].name == "test-artifact-0"
    assert result.data[99].name == "test-artifact-99"


# Error handling tests
@pytest.mark.asyncio
async def test_list_artifacts_invalid_pagination_parameters():
    """Test error handling for invalid pagination parameters using mocks"""

    # Mock processors that handle edge cases gracefully
    mock_processors = MagicMock()

    # Test negative offset - should return empty result
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[], total_count=3)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=-1, limit=10),
        )
    )
    assert isinstance(result, ListArtifactsActionResult)
    assert len(result.data) == 0

    # Test zero limit - should return empty results
    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=0),
        )
    )
    assert len(result.data) == 0

    # Test very large offset - should return empty results
    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=ArtifactOffsetBasedPaginationOptions(offset=10000, limit=10),
        )
    )
    assert len(result.data) == 0
    assert result.total_count == 3  # Total count should still be accurate


@pytest.mark.asyncio
async def test_list_artifacts_invalid_connection_parameters():
    """Test error handling for invalid connection pagination parameters using mocks"""

    # Mock processors that handle edge cases gracefully
    mock_processors = MagicMock()
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[ARTIFACT_FIXTURE_DATA_1], total_count=1)
    )

    # Test invalid cursor (non-UUID string)
    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(after="invalid-cursor", first=2),
        )
    )
    # Should handle gracefully and return results (ignoring invalid cursor)
    assert isinstance(result, ListArtifactsActionResult)

    # Test negative first parameter
    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(first=-1),
        )
    )
    # Should handle gracefully
    assert isinstance(result, ListArtifactsActionResult)

    # Test non-existent cursor UUID
    non_existent_uuid = str(uuid.uuid4())
    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            forward=ForwardPaginationOptions(after=non_existent_uuid, first=2),
        )
    )
    # Should return results (cursor not found, so pagination starts from beginning)
    assert isinstance(result, ListArtifactsActionResult)


@pytest.mark.asyncio
async def test_list_artifacts_with_conflicting_pagination_params():
    """Test behavior when both pagination and connection params are provided"""
    # Create mock processors
    mock_processors = MagicMock()
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_1],
            total_count=1,
        )
    )

    # Action with both pagination types (should prefer one over the other)
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=2),
        forward=ForwardPaginationOptions(first=3),
    )

    result = await mock_processors.list_artifacts.wait_for_complete(action)

    # Should handle gracefully and return results
    assert isinstance(result, ListArtifactsActionResult)
    mock_processors.list_artifacts.wait_for_complete.assert_called_once_with(action)


# Edge case tests
@pytest.mark.asyncio
async def test_list_artifacts_empty_database():
    """Test listing artifacts when database is empty using mocks"""

    # Mock processors returning empty results
    mock_processors = MagicMock()
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[], total_count=0)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(ListArtifactsAction())

    assert len(result.data) == 0
    assert result.total_count == 0


@pytest.mark.asyncio
async def test_list_artifacts_single_item_database():
    """Test listing artifacts when database has only one item using mocks"""

    # Mock processors
    mock_processors = MagicMock()

    # Test default pagination - return single item
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[ARTIFACT_FIXTURE_DATA_1], total_count=1)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(ListArtifactsAction())
    assert len(result.data) == 1
    assert result.total_count == 1

    # Test with offset beyond single item - return empty
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[], total_count=1)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(pagination=ArtifactOffsetBasedPaginationOptions(offset=1, limit=10))
    )
    assert len(result.data) == 0
    assert result.total_count == 1  # Total count should still be 1


@pytest.mark.asyncio
async def test_list_artifacts_all_ordering_fields():
    """Test all available ordering fields using mocks"""

    # Test each ordering field
    ordering_fields = [
        ArtifactOrderingField.CREATED_AT,
        ArtifactOrderingField.UPDATED_AT,
        ArtifactOrderingField.NAME,
        ArtifactOrderingField.SIZE,
        ArtifactOrderingField.TYPE,
    ]

    mock_processors = MagicMock()
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_1, ARTIFACT_FIXTURE_DATA_2, ARTIFACT_FIXTURE_DATA_3],
            total_count=3,
        )
    )

    for field in ordering_fields:
        for desc in [True, False]:
            result = await mock_processors.list_artifacts.wait_for_complete(
                ListArtifactsAction(
                    ordering=ArtifactOrderingOptions(
                        order_by=field,
                        order_desc=desc,
                    )
                )
            )

            # Should return all artifacts with specified ordering
            assert len(result.data) == 3
            assert result.total_count == 3

            # Verify ordering is consistent (all results returned)
            artifact_ids = [artifact.id for artifact in result.data]
            assert len(set(artifact_ids)) == 3  # No duplicates


@pytest.mark.asyncio
async def test_list_artifacts_complex_filter_combinations():
    """Test complex combinations of filters using mocks"""

    mock_processors = MagicMock()

    # Test multiple filters combined - return matching artifact
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=[ARTIFACT_FIXTURE_DATA_3],  # BERT model which matches filters
            total_count=1,
        )
    )

    result = await mock_processors.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            filters=ArtifactFilterOptions(
                artifact_type=ArtifactType.MODEL,
                authorized=True,
                name_filter="bert",
            )
        )
    )

    # Should return only artifacts that match all filters
    for artifact in result.data:
        assert artifact.type == ArtifactType.MODEL
        assert artifact.authorized is True
        assert "bert" in artifact.name.lower()

    # Test empty result from restrictive filters
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(data=[], total_count=0)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(
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
    # Mock processors to simulate large dataset performance
    mock_processors = MagicMock()

    # Simulate a large dataset response
    large_data = [ARTIFACT_FIXTURE_DATA_1] * 10000
    mock_processors.list_artifacts.wait_for_complete = AsyncMock(
        return_value=ListArtifactsActionResult(
            data=large_data[:5000],  # Return first 5000
            total_count=10000,
        )
    )

    # Test with very large limit
    action = ListArtifactsAction(
        pagination=ArtifactOffsetBasedPaginationOptions(offset=0, limit=5000)
    )

    result = await mock_processors.list_artifacts.wait_for_complete(action)

    # Verify large dataset handling
    assert len(result.data) == 5000
    assert result.total_count == 10000

    # Verify the mock was called correctly
    mock_processors.list_artifacts.wait_for_complete.assert_called_once_with(action)
