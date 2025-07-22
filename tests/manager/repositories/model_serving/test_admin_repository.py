import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import EndpointData, RoutingData
from ai.backend.manager.models.endpoint import EndpointLifecycle

from .conftest import assert_update_query_executed


@pytest.fixture
def mock_valkey_live():
    mock = AsyncMock()
    mock.store_live_data = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_get_endpoint_by_id_force_success(
    admin_model_serving_repository,
    setup_readonly_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force retrieval of endpoint by ID without access checks."""
    # Arrange
    endpoint_id = sample_endpoint.id
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.get_endpoint_by_id_force(endpoint_id)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id
    assert result.name == sample_endpoint.name
    patch_endpoint_get.assert_called_once_with(
        setup_readonly_session,
        endpoint_id,
        load_routes=True,
        load_session_owner=True,
        load_model=True,
        load_image=True,
    )


@pytest.mark.asyncio
async def test_get_endpoint_by_id_force_not_found(
    admin_model_serving_repository,
    setup_readonly_session,
    patch_endpoint_get,
):
    """Test admin force retrieval returns None for non-existent endpoint."""
    # Arrange
    endpoint_id = uuid.uuid4()
    patch_endpoint_get.side_effect = NoResultFound()

    # Act
    result = await admin_model_serving_repository.get_endpoint_by_id_force(endpoint_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "new_lifecycle,new_replicas",
    [
        (EndpointLifecycle.DESTROYING, None),
        (EndpointLifecycle.CREATED, 10),
    ],
)
async def test_update_endpoint_lifecycle_force(
    admin_model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    patch_endpoint_get,
    new_lifecycle,
    new_replicas,
):
    """Test admin force update of endpoint lifecycle with optional replicas."""
    # Arrange
    endpoint_id = sample_endpoint.id
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_endpoint_lifecycle_force(
        endpoint_id, new_lifecycle, replicas=new_replicas
    )

    # Assert
    assert result is True
    assert_update_query_executed(setup_writable_session)


@pytest.mark.asyncio
async def test_clear_endpoint_errors_force_success(
    admin_model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force clear of endpoint errors."""
    # Arrange
    endpoint_id = sample_endpoint.id
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.clear_endpoint_errors_force(endpoint_id)

    # Assert
    assert result is True
    # Verify two queries were executed (delete failed routes, reset retries)
    assert setup_writable_session.execute.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route_belongs_to_service,expected_result",
    [
        (True, "should_return_route"),
        (False, None),
    ],
)
async def test_get_route_by_id_force(
    admin_model_serving_repository,
    setup_readonly_session,
    sample_route,
    patch_routing_get,
    route_belongs_to_service,
    expected_result,
):
    """Test admin force retrieval of route by ID with service validation."""
    # Arrange
    route_id = sample_route.id
    service_id = sample_route.endpoint if route_belongs_to_service else uuid.uuid4()
    patch_routing_get.return_value = sample_route

    # Act
    result = await admin_model_serving_repository.get_route_by_id_force(route_id, service_id)

    # Assert
    if expected_result == "should_return_route":
        assert result is not None
        assert isinstance(result, RoutingData)
        assert result.id == route_id
    else:
        assert result is None


@pytest.mark.asyncio
async def test_update_route_traffic_force_success(
    admin_model_serving_repository,
    setup_writable_session,
    sample_route,
    sample_endpoint,
    patch_routing_get,
    patch_endpoint_get,
    mock_valkey_live,
):
    """Test admin force update of route traffic ratio."""
    # Arrange
    route_id = sample_route.id
    service_id = sample_route.endpoint
    new_traffic_ratio = 0.5
    patch_routing_get.return_value = sample_route
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_route_traffic_force(
        mock_valkey_live, route_id, service_id, new_traffic_ratio
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert_update_query_executed(setup_writable_session)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation,new_value",
    [
        ("decrease", None),
        ("update", 8),
    ],
)
async def test_endpoint_replicas_force_operations(
    admin_model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    patch_endpoint_get,
    operation,
    new_value,
):
    """Test admin force operations on endpoint replicas."""
    # Arrange
    endpoint_id = sample_endpoint.id
    if operation == "decrease":
        sample_endpoint.replicas = 5
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    if operation == "decrease":
        result = await admin_model_serving_repository.decrease_endpoint_replicas_force(endpoint_id)
    else:  # update
        result = await admin_model_serving_repository.update_endpoint_replicas_force(
            endpoint_id, new_value
        )

    # Assert
    assert result is True
    assert_update_query_executed(setup_writable_session, "replicas")
