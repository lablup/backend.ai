import decimal
import logging
from typing import Any

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
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
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointAutoScalingRuleNotFound,
    EndpointNotFound,
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class AutoScalingService:
    _repository: ModelServingRepository
    _admin_repository: AdminModelServingRepository

    def __init__(
        self,
        repository: ModelServingRepository,
        admin_repository: AdminModelServingRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def check_requester_access(self, requester_ctx: RequesterCtx) -> None:
        if requester_ctx.is_authorized is False:
            raise GenericForbidden("Only authorized requests may have access key scopes.")

    async def scale_service_replicas(
        self, action: ScaleServiceReplicasAction
    ) -> ScaleServiceReplicasActionResult:
        # Get endpoint with access validation
        await self.check_requester_access(action.requester_ctx)
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._admin_repository.get_endpoint_by_id_force(action.service_id)
            if not endpoint_data:
                raise ModelServiceNotFound

            success = await self._admin_repository.update_endpoint_replicas_force(
                action.service_id, action.to
            )
        else:
            endpoint_data = await self._repository.get_endpoint_by_id_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )
            if not endpoint_data:
                raise ModelServiceNotFound

            success = await self._repository.update_endpoint_replicas_validated(
                action.service_id,
                action.to,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

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

        # Create auto scaling rule with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            created_rule = await self._admin_repository.create_auto_scaling_rule_force(
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
        else:
            created_rule = await self._repository.create_auto_scaling_rule_validated(
                user_id=action.requester_ctx.user_id,
                user_role=action.requester_ctx.user_role,
                domain_name=action.requester_ctx.domain_name,
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
        fields_to_update: dict[str, Any] = action.modifier.fields_to_update()

        # Update auto scaling rule with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            updated_rule = await self._admin_repository.update_auto_scaling_rule_force(
                action.id, fields_to_update
            )
        else:
            updated_rule = await self._repository.update_auto_scaling_rule_validated(
                action.id,
                fields_to_update,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if updated_rule is None:
            raise EndpointAutoScalingRuleNotFound

        return ModifyEndpointAutoScalingRuleActionResult(
            success=True,
            data=updated_rule,
        )

    async def delete_endpoint_auto_scaling_rule(
        self, action: DeleteEndpointAutoScalingRuleAction
    ) -> DeleteEndpointAutoScalingRuleActionResult:
        # Delete auto scaling rule with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            success = await self._admin_repository.delete_auto_scaling_rule_force(action.id)
        else:
            success = await self._repository.delete_auto_scaling_rule_validated(
                action.id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not success:
            raise EndpointAutoScalingRuleNotFound

        return DeleteEndpointAutoScalingRuleActionResult(
            success=True,
        )
