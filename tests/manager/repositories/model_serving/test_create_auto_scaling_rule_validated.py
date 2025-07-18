import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_endpoint_get,
):
    """Test successful creation of auto scaling rule."""
    # Arrange
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    endpoint_id = sample_endpoint.id

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Mock endpoint's create_auto_scaling_rule method
    sample_endpoint.create_auto_scaling_rule = AsyncMock(return_value=sample_auto_scaling_rule)

    # Act
    result = await model_serving_repository.create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=user_role,
        domain_name=domain_name,
        endpoint_id=endpoint_id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="cpu_util",
        threshold=80.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=1,
        cooldown_seconds=300,
        min_replicas=1,
        max_replicas=10,
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointAutoScalingRuleRow)
    assert result.id == sample_auto_scaling_rule.id

    # Verify the method was called with correct parameters
    sample_endpoint.create_auto_scaling_rule.assert_called_once_with(
        mock_session,
        AutoScalingMetricSource.KERNEL,
        "cpu_util",
        80.0,
        AutoScalingMetricComparator.GREATER_THAN,
        1,
        cooldown_seconds=300,
        min_replicas=1,
        max_replicas=10,
    )


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_endpoint_not_found(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    patch_endpoint_get,
):
    """Test creation returns None when endpoint not found."""
    # Arrange
    user_id = uuid.uuid4()
    user_role = UserRole.USER
    domain_name = "default"
    endpoint_id = uuid.uuid4()

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = None

    # Act
    result = await model_serving_repository.create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=user_role,
        domain_name=domain_name,
        endpoint_id=endpoint_id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="cpu_util",
        threshold=80.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=1,
        cooldown_seconds=300,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_access_denied(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test creation returns None when user doesn't have access."""
    # Arrange
    wrong_user_id = uuid.uuid4()  # Different user
    user_role = UserRole.USER
    domain_name = "default"
    endpoint_id = sample_endpoint.id

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query - returns original owner
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.create_auto_scaling_rule_validated(
        user_id=wrong_user_id,
        user_role=user_role,
        domain_name=domain_name,
        endpoint_id=endpoint_id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="cpu_util",
        threshold=80.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=1,
        cooldown_seconds=300,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_inactive_endpoint(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    """Test creation returns None when endpoint is inactive."""
    # Arrange
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    endpoint_id = sample_endpoint.id

    # Set endpoint to inactive state
    sample_endpoint.lifecycle_stage = EndpointLifecycle.DESTROYED

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Act
    result = await model_serving_repository.create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=user_role,
        domain_name=domain_name,
        endpoint_id=endpoint_id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="cpu_util",
        threshold=80.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=1,
        cooldown_seconds=300,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_with_optional_params(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_endpoint_get,
):
    """Test creation with optional min/max replicas parameters."""
    # Arrange
    user_id = sample_user.uuid
    user_role = UserRole.USER
    domain_name = "default"
    endpoint_id = sample_endpoint.id

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    patch_endpoint_get.return_value = sample_endpoint

    # Mock user query for access validation
    mock_session.execute.return_value.scalar.return_value = sample_user

    # Mock endpoint's create_auto_scaling_rule method
    sample_endpoint.create_auto_scaling_rule = AsyncMock(return_value=sample_auto_scaling_rule)

    # Act
    result = await model_serving_repository.create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=user_role,
        domain_name=domain_name,
        endpoint_id=endpoint_id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="memory_util",
        threshold=90.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=2,
        cooldown_seconds=600,
        min_replicas=2,
        max_replicas=20,
    )

    # Assert
    assert result is not None

    # Verify optional parameters were passed
    sample_endpoint.create_auto_scaling_rule.assert_called_once_with(
        mock_session,
        AutoScalingMetricSource.KERNEL,
        "memory_util",
        90.0,
        AutoScalingMetricComparator.GREATER_THAN,
        2,
        cooldown_seconds=600,
        min_replicas=2,
        max_replicas=20,
    )
