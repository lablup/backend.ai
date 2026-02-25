from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auto_scaling_rule import (
    AutoScalingRuleFilter,
    CreateAutoScalingRuleRequest,
    CreateAutoScalingRuleResponse,
    DeleteAutoScalingRuleRequest,
    DeleteAutoScalingRuleResponse,
    GetAutoScalingRuleResponse,
    SearchAutoScalingRulesRequest,
    SearchAutoScalingRulesResponse,
    UpdateAutoScalingRuleRequest,
    UpdateAutoScalingRuleResponse,
)
from ai.backend.common.types import AutoScalingMetricSource


class TestAutoScalingRuleCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_rule(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin creates an auto-scaling rule with max_threshold."""
        result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
            )
        )
        assert isinstance(result, CreateAutoScalingRuleResponse)
        rule = result.auto_scaling_rule
        assert rule.model_deployment_id == model_deployment_fixture
        assert rule.metric_source == AutoScalingMetricSource.KERNEL
        assert rule.metric_name == "cpu"
        assert rule.max_threshold == Decimal("80.0")
        assert rule.step_size == 1
        assert rule.time_window == 300

    @pytest.mark.asyncio
    async def test_admin_creates_rule_with_min_threshold(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin creates an auto-scaling rule with min_threshold only."""
        result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK,
                metric_name="requests_per_second",
                min_threshold=Decimal("10.0"),
                step_size=2,
                time_window=600,
                min_replicas=1,
                max_replicas=10,
            )
        )
        assert isinstance(result, CreateAutoScalingRuleResponse)
        rule = result.auto_scaling_rule
        assert rule.min_threshold == Decimal("10.0")
        assert rule.min_replicas == 1
        assert rule.max_replicas == 10

    @pytest.mark.asyncio
    async def test_create_with_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Creating a rule for a non-existent deployment raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.auto_scaling_rule.create(
                CreateAutoScalingRuleRequest(
                    model_deployment_id=uuid.uuid4(),
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name="cpu",
                    max_threshold=Decimal("80.0"),
                    step_size=1,
                    time_window=300,
                )
            )


class TestAutoScalingRuleGet:
    @pytest.mark.asyncio
    async def test_admin_gets_rule(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin retrieves a previously created auto-scaling rule by ID."""
        create_result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="memory",
                max_threshold=Decimal("90.0"),
                step_size=1,
                time_window=300,
            )
        )
        rule_id = create_result.auto_scaling_rule.id

        get_result = await admin_registry.auto_scaling_rule.get(rule_id)
        assert isinstance(get_result, GetAutoScalingRuleResponse)
        assert get_result.auto_scaling_rule.id == rule_id
        assert get_result.auto_scaling_rule.metric_name == "memory"

    @pytest.mark.asyncio
    async def test_get_nonexistent_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Getting a rule with a random UUID raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.auto_scaling_rule.get(uuid.uuid4())


class TestAutoScalingRuleSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_rules(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin searches all auto-scaling rules and receives a paginated response."""
        await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
            )
        )

        result = await admin_registry.auto_scaling_rule.search(SearchAutoScalingRulesRequest())
        assert isinstance(result, SearchAutoScalingRulesResponse)
        assert len(result.auto_scaling_rules) >= 1
        assert result.pagination.total >= 1

    @pytest.mark.asyncio
    async def test_search_with_deployment_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Search with model_deployment_id filter returns only matching rules."""
        await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
            )
        )

        result = await admin_registry.auto_scaling_rule.search(
            SearchAutoScalingRulesRequest(
                filter=AutoScalingRuleFilter(
                    model_deployment_id=model_deployment_fixture,
                )
            )
        )
        assert isinstance(result, SearchAutoScalingRulesResponse)
        for rule in result.auto_scaling_rules:
            assert rule.model_deployment_id == model_deployment_fixture

    @pytest.mark.asyncio
    async def test_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with a non-matching filter returns an empty list."""
        result = await admin_registry.auto_scaling_rule.search(
            SearchAutoScalingRulesRequest(
                filter=AutoScalingRuleFilter(
                    model_deployment_id=uuid.uuid4(),
                )
            )
        )
        assert isinstance(result, SearchAutoScalingRulesResponse)
        assert len(result.auto_scaling_rules) == 0
        assert result.pagination.total == 0


class TestAutoScalingRuleUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_rule(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin updates metric_name and step_size of an existing rule."""
        create_result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
            )
        )
        rule_id = create_result.auto_scaling_rule.id

        update_result = await admin_registry.auto_scaling_rule.update(
            rule_id,
            UpdateAutoScalingRuleRequest(
                metric_name="memory",
                step_size=3,
            ),
        )
        assert isinstance(update_result, UpdateAutoScalingRuleResponse)
        assert update_result.auto_scaling_rule.metric_name == "memory"
        assert update_result.auto_scaling_rule.step_size == 3

    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Updating a non-existent rule raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.auto_scaling_rule.update(
                uuid.uuid4(),
                UpdateAutoScalingRuleRequest(metric_name="cpu"),
            )


class TestAutoScalingRuleDelete:
    @pytest.mark.asyncio
    async def test_admin_deletes_rule(
        self,
        admin_registry: BackendAIClientRegistry,
        model_deployment_fixture: uuid.UUID,
    ) -> None:
        """Admin deletes an existing rule and confirms deletion."""
        create_result = await admin_registry.auto_scaling_rule.create(
            CreateAutoScalingRuleRequest(
                model_deployment_id=model_deployment_fixture,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                max_threshold=Decimal("80.0"),
                step_size=1,
                time_window=300,
            )
        )
        rule_id = create_result.auto_scaling_rule.id

        delete_result = await admin_registry.auto_scaling_rule.delete(
            DeleteAutoScalingRuleRequest(rule_id=rule_id)
        )
        assert isinstance(delete_result, DeleteAutoScalingRuleResponse)
        assert delete_result.deleted is True

        # Verify the rule no longer exists
        with pytest.raises(NotFoundError):
            await admin_registry.auto_scaling_rule.get(rule_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deleting a non-existent rule returns deleted=False."""
        result = await admin_registry.auto_scaling_rule.delete(
            DeleteAutoScalingRuleRequest(rule_id=uuid.uuid4())
        )
        assert isinstance(result, DeleteAutoScalingRuleResponse)
        assert result.deleted is False
