from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.creator import EndpointCreator
from ai.backend.manager.data.model_serving.types import EndpointData


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry for testing."""
    mock = MagicMock()
    mock.create_appproxy_endpoint = AsyncMock(return_value="https://test-endpoint.example.com")
    return mock


def assert_creator_result(creator: EndpointCreator, result) -> None:
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.name == creator.name
    assert result.domain == creator.domain
    assert result.resource_group == creator.resource_group
    assert result.resource_slots == creator.resource_slots
    assert result.model == creator.model
    assert result.model_definition_path == creator.model_definition_path
    assert result.model_mount_destination == creator.model_mount_destination
    assert result.created_user_id == creator.created_user
    assert result.session_owner_id == creator.session_owner
    assert result.image is not None
    assert result.image.id == creator.image


@pytest.mark.asyncio
async def test_create_endpoint_validated_success(
    model_serving_repository,
    patch_endpoint_get,
    sample_endpoint_creator,
    sample_endpoint,
    mock_agent_registry,
):
    """Test successful creation of an endpoint."""
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await model_serving_repository.create_endpoint_validated(
        sample_endpoint_creator, mock_agent_registry
    )

    # Assert
    assert_creator_result(sample_endpoint_creator, result)
