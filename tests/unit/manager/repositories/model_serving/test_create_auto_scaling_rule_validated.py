import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole


@pytest.fixture
def setup_auto_scaling_test_base(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    patch_endpoint_get,
):
    # default user and endpoint setup
    setup_writable_session.execute.return_value.scalar.return_value = sample_user

    return {
        "repository": model_serving_repository,
        "session": setup_writable_session,
        "endpoint": sample_endpoint,
        "user": sample_user,
        "endpoint_mock": patch_endpoint_get,
    }


def setup_auto_scaling_rule_creation(endpoint, auto_scaling_rule):
    """Auto scaling rule creation mock setup"""
    endpoint.create_auto_scaling_rule = AsyncMock(return_value=auto_scaling_rule)
    return endpoint.create_auto_scaling_rule


def get_default_auto_scaling_params():
    return {
        "metric_source": AutoScalingMetricSource.KERNEL,
        "metric_name": "cpu_util",
        "threshold": 80.0,
        "comparator": AutoScalingMetricComparator.GREATER_THAN,
        "step_size": 1,
        "cooldown_seconds": 300,
    }


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_success(
    setup_auto_scaling_test_base,
    sample_auto_scaling_rule,
):
    """Test successful creation of auto scaling rule."""
    # Arrange
    test_setup = setup_auto_scaling_test_base
    user_id = test_setup["user"].uuid
    endpoint_id = test_setup["endpoint"].id

    test_setup["endpoint_mock"].return_value = test_setup["endpoint"]
    mock_create = setup_auto_scaling_rule_creation(test_setup["endpoint"], sample_auto_scaling_rule)

    params = get_default_auto_scaling_params()
    params.update({"min_replicas": 1, "max_replicas": 10})

    # Act
    result = await test_setup["repository"].create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=UserRole.USER,
        domain_name="default",
        endpoint_id=endpoint_id,
        **params,
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointAutoScalingRuleData)
    assert result.id == sample_auto_scaling_rule.id

    mock_create.assert_called_once_with(
        test_setup["session"],
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
    setup_auto_scaling_test_base,
):
    """Test creation returns None when endpoint not found."""
    # Arrange
    test_setup = setup_auto_scaling_test_base
    test_setup["endpoint_mock"].return_value = None

    user_id = test_setup["user"].uuid
    endpoint_id = test_setup["endpoint"].id
    params = get_default_auto_scaling_params()

    # Act
    result = await test_setup["repository"].create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=UserRole.USER,
        domain_name="default",
        endpoint_id=endpoint_id,
        **params,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_access_denied(
    setup_auto_scaling_test_base,
):
    """Test creation returns None when user doesn't have access."""
    # Arrange
    test_setup = setup_auto_scaling_test_base
    test_setup["endpoint_mock"].return_value = test_setup["endpoint"]

    wrong_user_id = uuid.uuid4()  # 다른 유저 ID
    endpoint_id = test_setup["endpoint"].id
    params = get_default_auto_scaling_params()

    # Act
    result = await test_setup["repository"].create_auto_scaling_rule_validated(
        user_id=wrong_user_id,
        user_role=UserRole.USER,
        domain_name="default",
        endpoint_id=endpoint_id,
        **params,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_auto_scaling_rule_validated_inactive_endpoint(
    setup_auto_scaling_test_base,
):
    """Test creation returns None when endpoint is inactive."""
    # Arrange
    test_setup = setup_auto_scaling_test_base
    test_setup["endpoint"].lifecycle_stage = EndpointLifecycle.DESTROYED
    test_setup["endpoint_mock"].return_value = test_setup["endpoint"]

    user_id = test_setup["user"].uuid
    endpoint_id = test_setup["endpoint"].id
    params = get_default_auto_scaling_params()

    # Act
    result = await test_setup["repository"].create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=UserRole.USER,
        domain_name="default",
        endpoint_id=endpoint_id,
        **params,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metric_params",
    [
        {
            "metric_name": "cpu_util",
            "threshold": 80.0,
            "step_size": 1,
            "cooldown_seconds": 300,
            "min_replicas": 1,
            "max_replicas": 10,
        },
        {
            "metric_name": "memory_util",
            "threshold": 90.0,
            "step_size": 2,
            "cooldown_seconds": 600,
            "min_replicas": 2,
            "max_replicas": 20,
        },
    ],
)
async def test_create_auto_scaling_rule_validated_with_various_params(
    setup_auto_scaling_test_base,
    sample_auto_scaling_rule,
    metric_params,
):
    """Test creation with various parameter combinations."""
    # Arrange
    test_setup = setup_auto_scaling_test_base
    user_id = test_setup["user"].uuid
    endpoint_id = test_setup["endpoint"].id

    test_setup["endpoint_mock"].return_value = test_setup["endpoint"]
    mock_create = setup_auto_scaling_rule_creation(test_setup["endpoint"], sample_auto_scaling_rule)

    base_params = {
        "metric_source": AutoScalingMetricSource.KERNEL,
        "comparator": AutoScalingMetricComparator.GREATER_THAN,
    }
    base_params.update(metric_params)

    # Act
    result = await test_setup["repository"].create_auto_scaling_rule_validated(
        user_id=user_id,
        user_role=UserRole.USER,
        domain_name="default",
        endpoint_id=endpoint_id,
        **base_params,
    )

    # Assert
    assert result is not None

    # Verify parameters were passed correctly
    mock_create.assert_called_once_with(
        test_setup["session"],
        AutoScalingMetricSource.KERNEL,
        metric_params["metric_name"],
        metric_params["threshold"],
        AutoScalingMetricComparator.GREATER_THAN,
        metric_params["step_size"],
        cooldown_seconds=metric_params["cooldown_seconds"],
        min_replicas=metric_params["min_replicas"],
        max_replicas=metric_params["max_replicas"],
    )
