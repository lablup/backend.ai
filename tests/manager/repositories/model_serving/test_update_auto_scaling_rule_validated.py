import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.model_serving.updaters import (
    EndpointAutoScalingRuleUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState

from .conftest import setup_mock_query_result


def create_updater_from_fields(rule_id: uuid.UUID, fields: dict) -> Updater:
    """Helper function to create an Updater from a dict of fields."""
    spec = EndpointAutoScalingRuleUpdaterSpec(
        metric_source=OptionalState.update(fields["metric_source"])
        if "metric_source" in fields
        else OptionalState.nop(),
        metric_name=OptionalState.update(fields["metric_name"])
        if "metric_name" in fields
        else OptionalState.nop(),
        threshold=OptionalState.update(Decimal(str(fields["threshold"])))
        if "threshold" in fields
        else OptionalState.nop(),
        comparator=OptionalState.update(fields["comparator"])
        if "comparator" in fields
        else OptionalState.nop(),
        step_size=OptionalState.update(fields["step_size"])
        if "step_size" in fields
        else OptionalState.nop(),
        cooldown_seconds=OptionalState.update(fields["cooldown_seconds"])
        if "cooldown_seconds" in fields
        else OptionalState.nop(),
        min_replicas=TriState.update(fields["min_replicas"])
        if "min_replicas" in fields
        else TriState.nop(),
        max_replicas=TriState.update(fields["max_replicas"])
        if "max_replicas" in fields
        else TriState.nop(),
    )
    return Updater(spec=spec, pk_value=rule_id)


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
    updater = create_updater_from_fields(rule_id, fields_to_update)

    # Apply the expected updates to the sample rule for the mock return value
    for key, value in fields_to_update.items():
        if key == "threshold":
            setattr(sample_auto_scaling_rule, key, Decimal(str(value)))
        else:
            setattr(sample_auto_scaling_rule, key, value)

    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
    # Mock both scalar (for user lookup) and scalar_one_or_none (for execute_updater)
    setup_mock_query_result(
        setup_writable_session,
        scalar_result=sample_user,
        scalar_one_or_none_result=sample_auto_scaling_rule,
    )

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        updater, user_id, UserRole.USER, "default"
    )

    # Assert
    assert result is not None
    assert isinstance(result, EndpointAutoScalingRuleData)
    assert result.id == rule_id

    # Verify fields were updated
    for key, value in fields_to_update.items():
        if key == "threshold":
            assert float(result.threshold) == value
        else:
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
    updater = create_updater_from_fields(rule_id, fields_to_update)

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
        updater, user_id, UserRole.USER, "default"
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
    updater = create_updater_from_fields(rule_id, update_fields)

    # Apply the expected updates to the sample rule for the mock return value
    for key, value in update_fields.items():
        if key == "threshold":
            setattr(sample_auto_scaling_rule, key, Decimal(str(value)))
        else:
            setattr(sample_auto_scaling_rule, key, value)

    patch_auto_scaling_rule_get.return_value = sample_auto_scaling_rule
    # Mock both scalar (for user lookup) and scalar_one_or_none (for execute_updater)
    setup_mock_query_result(
        setup_writable_session,
        scalar_result=sample_user,
        scalar_one_or_none_result=sample_auto_scaling_rule,
    )

    # Act
    result = await model_serving_repository.update_auto_scaling_rule_validated(
        updater, user_id, user_role, "default"
    )

    # Assert
    assert result is not None

    # Verify all fields were updated
    for key, value in update_fields.items():
        if key == "threshold":
            assert float(result.threshold) == value
        else:
            assert getattr(result, key) == value
