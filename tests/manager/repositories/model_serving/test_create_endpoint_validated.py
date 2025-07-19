from unittest.mock import AsyncMock, MagicMock

import pytest

from .conftest import (
    assert_basic_endpoint_result,
    assert_endpoint_creation_operations,
    create_full_featured_endpoint,
    setup_db_session_mock,
)


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry for testing."""
    mock = MagicMock()
    mock.create_appproxy_endpoint = AsyncMock(return_value="https://test-endpoint.example.com")
    return mock


@pytest.mark.asyncio
async def test_create_endpoint_validated_success(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    mock_agent_registry,
):
    """Test successful creation of an endpoint."""
    # Act
    result = await model_serving_repository.create_endpoint_validated(
        sample_endpoint, mock_agent_registry
    )

    # Assert
    assert_basic_endpoint_result(result, sample_endpoint)
    assert_endpoint_creation_operations(setup_writable_session, sample_endpoint)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint_config,expected_attrs",
    [
        ("basic", {"name": "test-endpoint", "replicas": 1}),
        (
            "full_featured",
            {
                "name": "full-featured-endpoint",
                "replicas": 3,
                "cluster_mode": "multi-node",
                "runtime_variant": "custom",
            },
        ),
    ],
)
async def test_create_endpoint_validated_with_configurations(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    sample_image,
    sample_vfolder,
    endpoint_config,
    expected_attrs,
    mock_agent_registry,
):
    """Test creation of endpoints with different configurations."""
    # Arrange
    if endpoint_config == "basic":
        endpoint_row = sample_endpoint
    else:  # full_featured
        endpoint_row = create_full_featured_endpoint(sample_user, sample_image, sample_vfolder)

    # Act
    result = await model_serving_repository.create_endpoint_validated(
        endpoint_row, mock_agent_registry
    )

    # Assert
    assert_basic_endpoint_result(result, endpoint_row)

    # Check specific attributes
    for attr_name, expected_value in expected_attrs.items():
        assert getattr(result, attr_name) == expected_value

    assert_endpoint_creation_operations(setup_writable_session, endpoint_row)


@pytest.mark.asyncio
async def test_create_endpoint_validated_transaction_handling(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    mock_agent_registry,
):
    """Test that creation properly handles database transactions."""
    # Arrange
    setup_db_session_mock(mock_db_engine, mock_session)

    # Act
    result = await model_serving_repository.create_endpoint_validated(
        sample_endpoint, mock_agent_registry
    )

    # Assert
    assert_basic_endpoint_result(result, sample_endpoint)

    # Verify transaction management
    mock_db_engine.begin_session.assert_called_once()
    assert_endpoint_creation_operations(mock_session, sample_endpoint)
