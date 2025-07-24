import uuid

import pytest
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole

from .conftest import setup_mock_query_result


@pytest.mark.asyncio
async def test_update_auto_scaling_rule_validated_success(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
):
    """Test successful update of auto scaling rule."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    user_id = sample_user.uuid
    fields_to_update = {"threshold": 90.0, "step_size": 2, "cooldown_seconds": 600}

    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
    setup_mock_query_result(setup_writable_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, UserRole.USER, "default"
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointAutoScalingRuleData)
    assert result.id == rule_id

    # Verify fields were updated
    for key, value in fields_to_update.items():
        assert getattr(result, key) == value


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["rule_not_found", "access_denied", "inactive_endpoint"])
async def test_update_auto_scaling_rule_validated_failure_cases(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
    scenario,
):
    """Test various failure scenarios for auto scaling rule update."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    fields_to_update = {"threshold": 90.0}

    if scenario == "rule_not_found":
        patch_auto_scaling_rule_get.side_effect = NoResultFound()
        user_id = sample_user.uuid
    elif scenario == "access_denied":
        patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
        setup_mock_query_result(setup_writable_session, scalar_result=sample_user)
        user_id = uuid.uuid4()  # Different user
    else:  # inactive_endpoint
        sample_endpoint.lifecycle_stage = EndpointLifecycle.DESTROYED
        sample_auto_scaling_rule.endpoint_row = sample_endpoint
        patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
        setup_mock_query_result(setup_writable_session, scalar_result=sample_user)
        user_id = sample_user.uuid

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, fields_to_update, user_id, UserRole.USER, "default"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_fields,user_role",
    [
        (
            {
                "metric_source": AutoScalingMetricSource.KERNEL,
                "metric_name": "memory_util",
                "threshold": 85.0,
                "comparator": AutoScalingMetricComparator.LESS_THAN,
                "step_size": 3,
                "cooldown_seconds": 900,
                "min_replicas": 2,
                "max_replicas": 15,
            },
            UserRole.USER,
        ),
        ({"threshold": 95.0}, UserRole.ADMIN),
    ],
)
async def test_update_auto_scaling_rule_validated_field_variations(
    model_serving_repository,
    setup_writable_session,
    sample_endpoint,
    sample_user,
    sample_admin_user,
    sample_auto_scaling_rule,
    patch_auto_scaling_rule_get,
    update_fields,
    user_role,
):
    """Test update with various field combinations and user roles."""
    # Arrange
    rule_id = sample_auto_scaling_rule.id
    user_id = sample_user.uuid if user_role == UserRole.USER else sample_admin_user.uuid

    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
    setup_mock_query_result(setup_writable_session, scalar_result=sample_user)

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        rule_id, update_fields, user_id, user_role, "default"
    )

    # Assert
    assert result is not None

    # Verify all fields were updated
    for key, value in update_fields.items():
        assert getattr(result, key) == value
