import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import EndpointData, RoutingData
from ai.backend.manager.models.endpoint import EndpointLifecycle


@pytest.mark.asyncio
async def test_get_endpoint_by_id_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force retrieval of endpoint by ID without access checks."""
    # Arrange
    endpoint_id = sample_endpoint.id

    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.get_endpoint_by_id_force(endpoint_id)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id
    assert result.name == sample_endpoint.name
    patch_endpoint_get.assert_called_once_with(
        mock_session, endpoint_id, load_routes=True, load_session_owner=True, load_model=True
    )


@pytest.mark.asyncio
async def test_get_endpoint_by_id_force_not_found(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    patch_endpoint_get,
):
    """Test admin force retrieval returns None for non-existent endpoint."""
    # Arrange
    endpoint_id = uuid.uuid4()

    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.side_effect = NoResultFound()

    # Act
    result = await admin_model_serving_repository.get_endpoint_by_id_force(endpoint_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force update of endpoint lifecycle without access checks."""
    # Arrange
    endpoint_id = sample_endpoint.id
    new_lifecycle = EndpointLifecycle.DESTROYING

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_endpoint_lifecycle_force(
        endpoint_id, new_lifecycle
    )

    # Assert
    assert result is True

    # Verify the update query was executed
    mock_session.execute.assert_called()
    executed_query = mock_session.execute.call_args[0][0]
    assert isinstance(executed_query, sa.sql.dml.Update)


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_force_with_replicas(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force update with replica count."""
    # Arrange
    endpoint_id = sample_endpoint.id
    new_lifecycle = EndpointLifecycle.CREATED
    new_replicas = 10

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_endpoint_lifecycle_force(
        endpoint_id, new_lifecycle, replicas=new_replicas
    )

    # Assert
    assert result is True
    mock_session.execute.assert_called()


@pytest.mark.asyncio
async def test_clear_endpoint_errors_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force clear of endpoint errors."""
    # Arrange
    endpoint_id = sample_endpoint.id

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.clear_endpoint_errors_force(endpoint_id)

    # Assert
    assert result is True

    # Verify two queries were executed (delete failed routes, reset retries)
    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_route_by_id_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_route,
    patch_routing_get,
):
    """Test admin force retrieval of route by ID."""
    # Arrange
    route_id = sample_route.id
    service_id = sample_route.endpoint

    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    patch_routing_get.return_value = sample_route

    # Act
    result = await admin_model_serving_repository.get_route_by_id_force(route_id, service_id)

    # Assert
    assert result is not None
    assert isinstance(result, RoutingData)
    assert result.id == route_id


@pytest.mark.asyncio
async def test_get_route_by_id_force_wrong_service(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_route,
    patch_routing_get,
):
    """Test admin force retrieval returns None when route doesn't belong to service."""
    # Arrange
    route_id = sample_route.id
    wrong_service_id = uuid.uuid4()

    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    patch_routing_get.return_value = sample_route

    # Act
    result = await admin_model_serving_repository.get_route_by_id_force(route_id, wrong_service_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_route_traffic_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_route,
    sample_endpoint,
    patch_routing_get,
    patch_endpoint_get,
):
    """Test admin force update of route traffic ratio."""
    # Arrange
    route_id = sample_route.id
    service_id = sample_route.endpoint
    new_traffic_ratio = 0.5

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_routing_get.return_value = sample_route
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_route_traffic_force(
        route_id, service_id, new_traffic_ratio
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)

    # Verify update query was executed
    mock_session.execute.assert_called()


@pytest.mark.asyncio
async def test_decrease_endpoint_replicas_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force decrease of endpoint replicas."""
    # Arrange
    service_id = sample_endpoint.id
    sample_endpoint.replicas = 5

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.decrease_endpoint_replicas_force(service_id)

    # Assert
    assert result is True

    # Verify update query was executed with correct value
    mock_session.execute.assert_called()
    executed_query = mock_session.execute.call_args[0][0]
    assert "replicas" in str(executed_query)


@pytest.mark.asyncio
async def test_update_endpoint_replicas_force_success(
    admin_model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test admin force update of endpoint replicas to specific value."""
    # Arrange
    endpoint_id = sample_endpoint.id
    new_replicas = 8

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await admin_model_serving_repository.update_endpoint_replicas_force(
        endpoint_id, new_replicas
    )

    # Assert
    assert result is True

    # Verify update query was executed
    mock_session.execute.assert_called()
    executed_query = mock_session.execute.call_args[0][0]
    assert "replicas" in str(executed_query)
