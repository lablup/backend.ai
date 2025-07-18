import uuid

import pytest
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.user import UserRole

from .conftest import setup_db_session_mock, setup_mock_query_result


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test successful retrieval of endpoint by ID with valid access."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    setup_mock_query_result(mock_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, user_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id
    assert result.name == sample_endpoint.name
    patch_endpoint_get.assert_called_once_with(
        mock_session, endpoint_id, load_routes=True, load_session_owner=True, load_model=True
    )


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_not_found(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    patch_endpoint_get,
):
    """Test retrieval of non-existent endpoint returns None."""
    # Arrange
    endpoint_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user_role = UserRole.USER
    domain_name = "default"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.side_effect = NoResultFound()

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, user_id, user_role, domain_name
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_access_denied_wrong_owner(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test access denied when user is not the owner."""
    # Arrange
    endpoint_id = sample_endpoint.id
    wrong_user_id = uuid.uuid4()  # Different user
    user_role = UserRole.USER
    domain_name = "default"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query - returns original owner
    setup_mock_query_result(mock_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, wrong_user_id, user_role, domain_name
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_admin_access_same_domain(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_admin_user,
    sample_user,
    patch_endpoint_get,
):
    """Test admin can access endpoints in their domain."""
    # Arrange
    endpoint_id = sample_endpoint.id
    admin_id = sample_admin_user.uuid
    user_role = UserRole.ADMIN
    domain_name = "default"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for owner check
    setup_mock_query_result(mock_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, admin_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_admin_access_different_domain(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_admin_user,
    sample_user,
    patch_endpoint_get,
):
    """Test admin cannot access endpoints in different domain."""
    # Arrange
    endpoint_id = sample_endpoint.id
    admin_id = sample_admin_user.uuid
    user_role = UserRole.ADMIN
    different_domain = "other-domain"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query
    setup_mock_query_result(mock_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, admin_id, user_role, different_domain
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_superadmin_access(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_superadmin_user,
    patch_endpoint_get,
):
    """Test superadmin can access any endpoint."""
    # Arrange
    endpoint_id = sample_endpoint.id
    superadmin_id = sample_superadmin_user.uuid
    user_role = UserRole.SUPERADMIN
    domain_name = "any-domain"

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, superadmin_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id


@pytest.mark.asyncio
async def test_get_endpoint_by_id_validated_no_session_owner(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    patch_endpoint_get,
):
    """Test endpoint with no session owner is accessible by anyone."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = uuid.uuid4()
    user_role = UserRole.USER
    domain_name = "default"

    # Set endpoint session_owner to None
    sample_endpoint.session_owner = None

    setup_db_session_mock(mock_db_engine, mock_session)
    patch_endpoint_get.return_value = sample_endpoint

    # Act
    result = await model_serving_repository.get_endpoint_by_id_validated(
        endpoint_id, user_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id
