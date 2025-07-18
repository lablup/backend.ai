import uuid

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.endpoint import EndpointLifecycle
from ai.backend.manager.models.user import UserRole


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test successful update of endpoint lifecycle stage."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.DESTROYING

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, user_role, domain_name
    )

    # Assert
    assert result is True

    # Verify the update query was executed
    mock_session.execute.assert_called()
    executed_query = mock_session.execute.call_args[0][0]
    assert isinstance(executed_query, sa.sql.dml.Update)


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_with_replicas(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test update of lifecycle stage with replica count."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.CREATED
    new_replicas = 5

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, user_role, domain_name, replicas=new_replicas
    )

    # Assert
    assert result is True

    # Verify the update included replicas
    mock_session.execute.assert_called()


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_destroyed_with_timestamp(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test that DESTROYED lifecycle sets destroyed_at timestamp."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.DESTROYED

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, user_role, domain_name
    )

    # Assert
    assert result is True

    # Verify the update query included destroyed_at timestamp
    mock_session.execute.assert_called()
    executed_query = mock_session.execute.call_args[0][0]
    # The query should include sa.func.now() for destroyed_at
    assert "destroyed_at" in str(executed_query)


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_not_found(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    patch_endpoint_get,
):
    """Test update returns False when endpoint not found."""
    # Arrange
    endpoint_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user_role = UserRole.USER
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.DESTROYING

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = None

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, user_role, domain_name
    )

    # Assert
    assert result is False

    # Verify no update was attempted
    mock_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_access_denied(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test update returns False when user doesn't have access."""
    # Arrange
    endpoint_id = sample_endpoint.id
    wrong_user_id = uuid.uuid4()  # Different user
    user_role = UserRole.USER
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.DESTROYING

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query - returns original owner
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, wrong_user_id, user_role, domain_name
    )

    # Assert
    assert result is False

    # Verify no update was attempted
    assert mock_session.execute.call_count == 1  # Only for access check


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_admin_access(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_admin_user,
    sample_user,
    patch_endpoint_get,
):
    """Test admin can update endpoints in their domain."""
    # Arrange
    endpoint_id = sample_endpoint.id
    admin_id = sample_admin_user.uuid
    user_role = UserRole.ADMIN
    domain_name = "default"
    new_lifecycle = EndpointLifecycle.DESTROYING

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for owner check
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, admin_id, user_role, domain_name
    )

    # Assert
    assert result is True
