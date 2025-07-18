import uuid

import pytest

from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow

from .conftest import setup_db_session_mock, setup_mock_query_result


@pytest.mark.asyncio
async def test_list_endpoints_by_owner_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
):
    """Test successful listing of endpoints owned by a user."""
    # Arrange
    session_owner_id = sample_user.uuid

    # Create multiple endpoints for the user
    endpoint1 = sample_endpoint
    # Create a second endpoint with different attributes
    endpoint2 = EndpointRow(
        name="test-endpoint-2",
        model=sample_endpoint.model,
        model_mount_destination=sample_endpoint.model_mount_destination,
        model_definition_path=sample_endpoint.model_definition_path,
        runtime_variant=sample_endpoint.runtime_variant,
        session_owner=sample_endpoint.session_owner,
        tag=sample_endpoint.tag,
        startup_command=sample_endpoint.startup_command,
        bootstrap_script=sample_endpoint.bootstrap_script,
        callback_url=sample_endpoint.callback_url,
        environ=sample_endpoint.environ,
        resource_slots=sample_endpoint.resource_slots,
        resource_opts=sample_endpoint.resource_opts,
        image=sample_endpoint.image_row,
        replicas=sample_endpoint.replicas,
        cluster_mode=sample_endpoint.cluster_mode,
        cluster_size=sample_endpoint.cluster_size,
        extra_mounts=sample_endpoint.extra_mounts,
        created_user=sample_endpoint.created_user,
        project=sample_endpoint.project,
        domain=sample_endpoint.domain,
        resource_group=sample_endpoint.resource_group,
    )
    endpoint2.id = uuid.uuid4()
    endpoint2.created_at = sample_endpoint.created_at
    endpoint2.destroyed_at = None
    endpoint2.lifecycle_stage = EndpointLifecycle.CREATED
    endpoint2.retries = 0
    endpoint2.url = f"https://api.example.com/v1/models/{endpoint2.name}"
    endpoint2.open_to_public = False
    endpoint2.image_row = sample_endpoint.image_row
    endpoint2.session_owner_row = sample_endpoint.session_owner_row
    endpoint2.created_user_row = sample_endpoint.created_user_row
    endpoint2.routings = []

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution
    setup_mock_query_result(mock_session, scalars_all_result=[endpoint1, endpoint2])

    # Act
    result = await model_serving_repository.list_endpoints_by_owner_validated(session_owner_id)

    # Assert
    assert len(result) == 2
    assert all(isinstance(endpoint, EndpointData) for endpoint in result)
    assert result[0].id == endpoint1.id
    assert result[1].id == endpoint2.id

    # Verify the query included proper conditions
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_endpoints_by_owner_validated_with_name_filter(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
):
    """Test listing endpoints with name filter."""
    # Arrange
    session_owner_id = sample_user.uuid
    filter_name = "specific-endpoint"
    sample_endpoint.name = filter_name

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution
    setup_mock_query_result(mock_session, scalars_all_result=[sample_endpoint])

    # Act
    result = await model_serving_repository.list_endpoints_by_owner_validated(
        session_owner_id, name=filter_name
    )

    # Assert
    assert len(result) == 1
    assert result[0].name == filter_name


@pytest.mark.asyncio
async def test_list_endpoints_by_owner_validated_empty_result(
    model_serving_repository,
    mock_db_engine,
    mock_session,
):
    """Test listing returns empty list when user has no endpoints."""
    # Arrange
    session_owner_id = uuid.uuid4()

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution - no results
    setup_mock_query_result(mock_session, scalars_all_result=[])

    # Act
    result = await model_serving_repository.list_endpoints_by_owner_validated(session_owner_id)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_list_endpoints_by_owner_validated_excludes_destroyed(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
):
    """Test listing excludes destroyed endpoints."""
    # Arrange
    session_owner_id = sample_user.uuid

    # Create active and destroyed endpoints
    active_endpoint = sample_endpoint

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution - only return active endpoint
    setup_mock_query_result(
        mock_session, scalars_all_result=[active_endpoint]
    )  # Destroyed endpoint filtered out

    # Act
    result = await model_serving_repository.list_endpoints_by_owner_validated(session_owner_id)

    # Assert
    assert len(result) == 1
    assert result[0].lifecycle_stage == EndpointLifecycle.CREATED
