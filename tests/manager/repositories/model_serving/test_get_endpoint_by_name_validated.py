import pytest

from ai.backend.manager.data.model_serving.types import EndpointData

from .conftest import setup_mock_query_result


@pytest.mark.asyncio
async def test_get_endpoint_by_name_validated_success(
    model_serving_repository,
    setup_readonly_session,
    sample_endpoint,
    sample_user,
):
    """Test successful retrieval of endpoint by name with ownership validation."""
    # Arrange
    endpoint_name = sample_endpoint.name
    user_id = sample_user.uuid
    setup_mock_query_result(setup_readonly_session, scalar_result=sample_endpoint)

    # Act
    result = await model_serving_repository.get_endpoint_by_name_validated(endpoint_name, user_id)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == sample_endpoint.id
    assert result.name == endpoint_name

    # Verify query conditions
    setup_readonly_session.execute.assert_called_once()
    executed_query = setup_readonly_session.execute.call_args[0][0]
    query_str = str(executed_query)
    assert "name" in query_str
    assert "session_owner" in query_str
