import uuid

import pytest

from ai.backend.manager.data.model_serving.types import EndpointData

from .conftest import setup_db_session_mock, setup_mock_query_result


@pytest.mark.asyncio
async def test_get_endpoint_by_name_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
):
    """Test successful retrieval of endpoint by name with ownership validation."""
    # Arrange
    endpoint_name = sample_endpoint.name
    user_id = sample_user.uuid

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution
    setup_mock_query_result(mock_session, scalar_result=sample_endpoint)

    # Act
    result = await model_serving_repository.get_endpoint_by_name_validated(endpoint_name, user_id)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == sample_endpoint.id
    assert result.name == endpoint_name

    # Verify the query
    mock_session.execute.assert_called_once()
    executed_query = mock_session.execute.call_args[0][0]
    # Check that the query includes both name and owner conditions
    assert "name" in str(executed_query)
    assert "session_owner" in str(executed_query)


@pytest.mark.asyncio
async def test_get_endpoint_by_name_validated_not_found(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_user,
):
    """Test retrieval returns None when endpoint doesn't exist."""
    # Arrange
    endpoint_name = "non-existent-endpoint"
    user_id = sample_user.uuid

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution - no result found
    setup_mock_query_result(mock_session, scalar_result=None)

    # Act
    result = await model_serving_repository.get_endpoint_by_name_validated(endpoint_name, user_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_endpoint_by_name_validated_wrong_owner(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
):
    """Test retrieval returns None when user doesn't own the endpoint."""
    # Arrange
    endpoint_name = sample_endpoint.name
    wrong_user_id = uuid.uuid4()  # Different user

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution - no match due to different owner
    setup_mock_query_result(mock_session, scalar_result=None)

    # Act
    result = await model_serving_repository.get_endpoint_by_name_validated(
        endpoint_name, wrong_user_id
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_endpoint_by_name_validated_multiple_same_name(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
):
    """Test retrieval returns only the endpoint owned by the user."""
    # Arrange
    endpoint_name = "shared-endpoint-name"
    user_id = sample_user.uuid
    sample_endpoint.name = endpoint_name

    setup_db_session_mock(mock_db_engine, mock_session)

    # Mock the query execution
    setup_mock_query_result(mock_session, scalar_result=sample_endpoint)

    # Act
    result = await model_serving_repository.get_endpoint_by_name_validated(endpoint_name, user_id)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == sample_endpoint.id
    assert result.name == endpoint_name
