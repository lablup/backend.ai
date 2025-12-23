import uuid

import pytest

from ai.backend.manager.models.endpoint import EndpointLifecycle
from ai.backend.manager.models.user import UserRole

from .conftest import assert_update_query_executed, setup_mock_query_result


@pytest.mark.asyncio
async def test_update_endpoint_lifecycle_validated_success(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test successful update of endpoint lifecycle stage."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid
    new_lifecycle = EndpointLifecycle.DESTROYING

    patch_endpoint_get.return_value = sample_endpoint
    setup_mock_query_result(setup_writable_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, UserRole.USER, "default"
    )

    # Assert
    assert result is True
    assert_update_query_executed(setup_writable_session)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "lifecycle,replicas,should_have_timestamp",
    [
        (EndpointLifecycle.CREATED, 5, False),
        (EndpointLifecycle.DESTROYING, None, False),
        (EndpointLifecycle.DESTROYED, None, True),
    ],
)
async def test_update_endpoint_lifecycle_validated_with_options(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
    lifecycle,
    replicas,
    should_have_timestamp,
):
    """Test lifecycle update with various options."""
    # Arrange
    endpoint_id = sample_endpoint.id
    user_id = sample_user.uuid

    patch_endpoint_get.return_value = sample_endpoint
    setup_mock_query_result(setup_writable_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, lifecycle, user_id, UserRole.USER, "default", replicas=replicas
    )

    # Assert
    assert result is True
    setup_writable_session.execute.assert_called()
    executed_query = setup_writable_session.execute.call_args[0][0]

    if should_have_timestamp:
        assert "destroyed_at" in str(executed_query)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario,user_role,expected_result",
    [
        ("endpoint_not_found", UserRole.USER, False),
        ("access_denied", UserRole.USER, False),
        ("admin_access", UserRole.ADMIN, True),
    ],
)
async def test_update_endpoint_lifecycle_validated_access_scenarios(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    sample_admin_user,
    patch_endpoint_get,
    scenario,
    user_role,
    expected_result,
):
    """Test various access scenarios for endpoint lifecycle update."""
    # Arrange
    endpoint_id = sample_endpoint.id
    new_lifecycle = EndpointLifecycle.DESTROYING

    if scenario == "endpoint_not_found":
        patch_endpoint_get.return_value = None
        user_id = sample_user.uuid
    elif scenario == "access_denied":
        patch_endpoint_get.return_value = sample_endpoint
        setup_mock_query_result(setup_writable_session, scalar_result=sample_user)
        user_id = uuid.uuid4()  # Different user
    else:  # admin_access
        patch_endpoint_get.return_value = sample_endpoint
        setup_mock_query_result(setup_writable_session, scalar_result=sample_user)
        user_id = sample_admin_user.uuid

    # Act
    result = await model_serving_repository.update_endpoint_lifecycle_validated(
        endpoint_id, new_lifecycle, user_id, user_role, "default"
    )

    # Assert
    assert result is expected_result

    if scenario == "endpoint_not_found":
        setup_writable_session.execute.assert_not_called()
    elif scenario == "access_denied":
        # Only access check query, no update
        assert setup_writable_session.execute.call_count == 1
