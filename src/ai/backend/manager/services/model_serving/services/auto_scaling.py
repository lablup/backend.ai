from __future__ import annotations

import decimal
import logging

from ai.backend.common.contexts.user import current_user
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.service import EndpointAccessForbiddenError
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.model_serving.options import EndpointConditions
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.modify_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_serving.actions.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
    SearchAutoScalingRulesActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointAutoScalingRuleNotFound,
    EndpointNotFound,
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
)
from ai.backend.manager.services.model_serving.services.utils import validate_endpoint_access

log = BraceStyleAdapter(logging.getLogger(__name__))


class AutoScalingService:
    _repository: ModelServingRepository

    def __init__(
        self,
        repository: ModelServingRepository,
    ) -> None:
        self._repository = repository

    async def check_user_access(self) -> None:
        user_data = current_user()
        if user_data is None or user_data.is_authorized is False:
            raise GenericForbidden("Only authorized requests may have access key scopes.")

    async def scale_service_replicas(
        self, action: ScaleServiceReplicasAction
    ) -> ScaleServiceReplicasActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get endpoint data
        endpoint_data = await self._repository.get_endpoint_by_id(action.service_id)
        if not endpoint_data:
            raise ModelServiceNotFound

        # Update replicas (access already validated)
        success = await self._repository.update_endpoint_replicas(action.service_id, action.to)
        if not success:
            raise ModelServiceNotFound

        return ScaleServiceReplicasActionResult(
            current_route_count=len(endpoint_data.routings) if endpoint_data.routings else 0,
            target_count=action.to,
        )

    async def create_endpoint_auto_scaling_rule(
        self, action: CreateEndpointAutoScalingRuleAction
    ) -> CreateEndpointAutoScalingRuleActionResult:
        try:
            _threshold = decimal.Decimal(action.creator.threshold)
        except decimal.InvalidOperation:
            raise InvalidAPIParameters(f"Cannot convert {action.creator.threshold} to Decimal")

        # Validate access to the endpoint first
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.endpoint_id
        )
        if not validation_data:
            raise EndpointNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Create auto scaling rule (access already validated)
        created_rule = await self._repository.create_auto_scaling_rule(
            endpoint_id=action.endpoint_id,
            metric_source=action.creator.metric_source,
            metric_name=action.creator.metric_name,
            threshold=_threshold,
            comparator=action.creator.comparator,
            step_size=action.creator.step_size,
            cooldown_seconds=action.creator.cooldown_seconds,
            min_replicas=action.creator.min_replicas,
            max_replicas=action.creator.max_replicas,
        )

        if created_rule is None:
            raise EndpointNotFound

        return CreateEndpointAutoScalingRuleActionResult(
            success=True,
            data=created_rule,
        )

    async def modify_endpoint_auto_scaling_rule(
        self, action: ModifyEndpointAutoScalingRuleAction
    ) -> ModifyEndpointAutoScalingRuleActionResult:
        # Get the rule to find the endpoint
        rule_data = await self._repository.get_auto_scaling_rule_by_id(action.id)
        if rule_data is None:
            raise EndpointAutoScalingRuleNotFound

        # Validate access to the endpoint
        validation_data = await self._repository.get_endpoint_access_validation_data(
            rule_data.endpoint
        )
        if not validation_data:
            raise EndpointNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Update auto scaling rule (access already validated)
        updated_rule = await self._repository.update_auto_scaling_rule(action.updater)
        if updated_rule is None:
            raise EndpointAutoScalingRuleNotFound

        return ModifyEndpointAutoScalingRuleActionResult(
            success=True,
            data=updated_rule,
        )

    async def delete_endpoint_auto_scaling_rule(
        self, action: DeleteEndpointAutoScalingRuleAction
    ) -> DeleteEndpointAutoScalingRuleActionResult:
        # Get the rule to find the endpoint
        rule_data = await self._repository.get_auto_scaling_rule_by_id(action.id)
        if rule_data is None:
            raise EndpointAutoScalingRuleNotFound

        # Validate access to the endpoint
        validation_data = await self._repository.get_endpoint_access_validation_data(
            rule_data.endpoint
        )
        if not validation_data:
            raise EndpointNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Delete auto scaling rule (access already validated)
        success = await self._repository.delete_auto_scaling_rule(action.id)
        if not success:
            raise EndpointAutoScalingRuleNotFound

        return DeleteEndpointAutoScalingRuleActionResult(
            success=True,
        )

    async def search_auto_scaling_rules(
        self, action: SearchAutoScalingRulesAction
    ) -> SearchAutoScalingRulesActionResult:
        """Searches endpoint auto scaling rules."""
        await self.check_user_access()

        # Apply access control conditions based on role
        user_data = current_user()
        if user_data is None:
            raise GenericForbidden("User context not available.")

        match user_data.role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                pass  # No additional conditions for SUPERADMIN and MONITOR
            case UserRole.ADMIN:
                action.querier.conditions.append(
                    EndpointConditions.by_domain(user_data.domain_name)
                )
            case UserRole.USER:
                action.querier.conditions.append(
                    EndpointConditions.by_session_owner(user_data.user_id)
                )

        result = await self._repository.search_auto_scaling_rules(querier=action.querier)

        return SearchAutoScalingRulesActionResult(
            rules=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
