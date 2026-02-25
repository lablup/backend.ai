from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auto_scaling_rule import (
    AutoScalingRuleFilter,
    CreateAutoScalingRuleRequest,
    DeleteAutoScalingRuleRequest,
    SearchAutoScalingRulesRequest,
    UpdateAutoScalingRuleRequest,
)
from ai.backend.common.types import AutoScalingMetricSource


@pytest.mark.integration
class TestAutoScalingRuleLifecycle:
    @pytest.mark.asyncio
    async def test_full_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Full CRUD lifecycle: create → get → update → get → search → delete → get (404)."""
        # 1. Create
        create_result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
                min_replicas=1,
                max_replicas=5,
            )
        )
        rule_id = create_result.auto_scaling_rule.id
        assert create_result.auto_scaling_rule.metric_name == "cpu"
        assert create_result.auto_scaling_rule.max_threshold == Decimal("80.0")

        # 2. Get
        get_result = await admin_registry.auto_scaling_rule.get(rule_id)
        assert get_result.auto_scaling_rule.id == rule_id
        assert get_result.auto_scaling_rule.metric_name == "cpu"
        assert get_result.auto_scaling_rule.model_deployment_id == model_deployment_fixture

        # 3. Update
        update_result = await admin_registry.auto_scaling_rule.update(
            rule_id,
            UpdateAutoScalingRuleRequest(
                metric_name="memory",
                step_size=2,
                max_threshold=Decimal("95.0"),
            ),
        )
        assert update_result.auto_scaling_rule.metric_name == "memory"
        assert update_result.auto_scaling_rule.step_size == 2
        assert update_result.auto_scaling_rule.max_threshold == Decimal("95.0")

        # 4. Get (verify update)
        get_updated = await admin_registry.auto_scaling_rule.get(rule_id)
        assert get_updated.auto_scaling_rule.metric_name == "memory"
        assert get_updated.auto_scaling_rule.step_size == 2

        # 5. Search
        search_result = await admin_registry.auto_scaling_rule.search(
            SearchAutoScalingRulesRequest(
                filter=AutoScalingRuleFilter(
                    model_deployment_id=model_deployment_fixture,
                )
            )
        )
        rule_ids = [r.id for r in search_result.auto_scaling_rules]
        assert rule_id in rule_ids

        # 6. Delete
        delete_result = await admin_registry.auto_scaling_rule.delete(
            DeleteAutoScalingRuleRequest(rule_id=rule_id)
        )
        assert delete_result.deleted is True

        # 7. Get (verify 404)
        with pytest.raises(NotFoundError):
            await admin_registry.auto_scaling_rule.get(rule_id)
