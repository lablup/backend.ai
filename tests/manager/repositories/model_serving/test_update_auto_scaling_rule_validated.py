import uuid

import pytest
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test successful update of auto scaling rule."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    fields_to_update = {
        "threshold": 90.0,
        "step_size": 2,
        "cooldown_seconds": 600,
    }

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointAutoScalingRuleRow)
    assert result.id == rule_id

    # Verify fields were updated
    for key, value in fields_to_update.items():
        assert getattr(result, key) == value


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_not_found(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    patch_auto_scaling_rule_get,
):
    """Test update returns None when rule not found."""
    # Arrange
    rule_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user_role = UserRole.USER
    domain_name = "default"
    fields_to_update = {"threshold": 90.0}

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.side_effect = NoResultFound()

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, user_role, domain_name
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_access_denied(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test update returns None when user doesn't have access."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    wrong_user_id = uuid.uuid4()  # Different user
    user_role = UserRole.USER
    domain_name = "default"
    fields_to_update = {"threshold": 90.0}

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule

    # Mock user query - returns original owner
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, wrong_user_id, user_role, domain_name
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_inactive_endpoint(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test update returns None when endpoint is inactive."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    fields_to_update = {"threshold": 90.0}

    # Set endpoint to inactive state
    sample_endpoint.lifecycle_stage = EndpointLifecycle.DESTROYED
    sample_auto_scaling_rule.endpoint_row = sample_endpoint

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, user_role, domain_name
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_multiple_fields(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test update of multiple fields at once."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    fields_to_update = {
        "metric_source": AutoScalingMetricSource.KERNEL,
        "metric_name": "memory_util",
        "threshold": 85.0,
        "comparator": AutoScalingMetricComparator.LESS_THAN,
        "step_size": 3,
        "cooldown_seconds": 900,
        "min_replicas": 2,
        "max_replicas": 15,
    }

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, user_role, domain_name
    )

    # Assert
    assert result is not None

    # Verify all fields were updated
    for key, value in fields_to_update.items():
        assert getattr(result, key) == value


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_admin_access(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_admin_user,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test admin can update rules for endpoints in their domain."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    admin_id = sample_admin_user.uuid
    user_role = UserRole.ADMIN
    domain_name = "default"
    fields_to_update = {"threshold": 95.0}

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule

    # Mock user query for owner check
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, admin_id, user_role, domain_name
    )

    # Assert
    assert result is not None
    assert result.threshold == 95.0
