from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.model_serving import EndpointCreatorSpec


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry for testing."""
    mock = MagicMock()
    mock.create_appproxy_endpoint = AsyncMock(return_value="https://test-endpoint.example.com")
    return mock


def assert_creator_result(creator: Creator[EndpointRow], result: EndpointData) -> None:
    spec = cast(EndpointCreatorSpec, creator.spec)
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.name == spec.name
    assert result.domain == spec.domain
    assert result.resource_group == spec.resource_group
    assert result.resource_slots == spec.resource_slots
    assert result.model == spec.model
    assert result.model_definition_path == spec.model_definition_path
    assert result.model_mount_destination == spec.model_mount_destination
    assert result.created_user_id == spec.created_user
    assert result.session_owner_id == spec.session_owner
    assert result.image is not None
    assert result.image.id == spec.image


@pytest.mark.asyncio
async def test_create_endpoint_validated_success(
    model_serving_repository,
    patch_endpoint_get,
    sample_endpoint_creator: Creator[EndpointRow],
    sample_endpoint,
    mock_agent_registry,
) -> None:
    """Test successful creation of an endpoint."""
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await model_serving_repository.create_endpoint_validated(
        sample_endpoint_creator, mock_agent_registry
    )

    # Assert
    assert_creator_result(sample_endpoint_creator, result)
