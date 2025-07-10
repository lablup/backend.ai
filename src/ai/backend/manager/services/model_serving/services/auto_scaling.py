import asyncio
import decimal
import logging
from typing import Any, Awaitable, Callable

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import execute_with_retry
from ai.backend.manager.repositories.model_serving.auto_scaling import AutoScalingRepository
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
    GenericForbidden,
    InvalidAPIParameters,
)
from ai.backend.manager.services.model_serving.types import (
    EndpointAutoScalingRuleData,
    MutationResult,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class AutoScalingService:
    _repository: AutoScalingRepository

    def __init__(
        self,
        repository: AutoScalingRepository,
    ) -> None:
        self._repository = repository

    async def scale_service_replicas(
        self, action: ScaleServiceReplicasAction
    ) -> ScaleServiceReplicasActionResult:
        endpoint = await self._repository.get_endpoint_by_id(action.service_id, load_routes=True)
        await self._repository.verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        await self._repository.update_endpoint_replicas(action.service_id, action.to)
        return ScaleServiceReplicasActionResult(
            current_route_count=len(endpoint.routings), target_count=action.to
        )

    async def create_endpoint_auto_scaling_rule(
        self, action: CreateEndpointAutoScalingRuleAction
    ) -> CreateEndpointAutoScalingRuleActionResult:
        row = await self._repository.get_endpoint_for_auto_scaling_rule(action.endpoint_id)

        match action.requester_ctx.user_role:
            case UserRole.SUPERADMIN:
                pass
            case UserRole.ADMIN:
                if row.domain != action.requester_ctx.domain_name:
                    raise GenericForbidden
            case UserRole.USER:
                if row.created_user != action.requester_ctx.user_id:
                    raise GenericForbidden

        try:
            _threshold = decimal.Decimal(action.creator.threshold)
        except decimal.InvalidOperation:
            raise InvalidAPIParameters(f"Cannot convert {action.creator.threshold} to Decimal")

        async def _do_mutate() -> MutationResult:
            created_rule = await self._repository.create_auto_scaling_rule(
                row,
                action.creator.metric_source,
                action.creator.metric_name,
                _threshold,
                action.creator.comparator,
                action.creator.step_size,
                cooldown_seconds=action.creator.cooldown_seconds,
                min_replicas=action.creator.min_replicas,
                max_replicas=action.creator.max_replicas,
            )
            return MutationResult(
                success=True,
                message="Auto scaling rule created",
                data=created_rule,
            )

        res = await self._db_mutation_wrapper(_do_mutate)

        return CreateEndpointAutoScalingRuleActionResult(
            success=res.success,
            data=EndpointAutoScalingRuleData.from_row(res.data),
        )

    async def modify_endpoint_auto_scaling_rule(
        self, action: ModifyEndpointAutoScalingRuleAction
    ) -> ModifyEndpointAutoScalingRuleActionResult:
        row = await self._repository.get_auto_scaling_rule_by_id(action.id, load_endpoint=True)

        match action.requester_ctx.user_role:
            case UserRole.SUPERADMIN:
                pass
            case UserRole.ADMIN:
                if row.endpoint_row.domain != action.requester_ctx.domain_name:
                    raise GenericForbidden
            case UserRole.USER:
                if row.endpoint_row.created_user != action.requester_ctx.user_id:
                    raise GenericForbidden

        async def _do_mutate() -> MutationResult:
            updated_rule = await self._repository.update_auto_scaling_rule(row, action.modifier.fields_to_update())
            return MutationResult(
                success=True,
                message="Auto scaling rule updated",
                data=updated_rule,
            )

        res = await self._db_mutation_wrapper(_do_mutate)

        return ModifyEndpointAutoScalingRuleActionResult(
            success=res.success,
            data=EndpointAutoScalingRuleData.from_row(res.data),
        )

    async def delete_endpoint_auto_scaling_rule(
        self, action: DeleteEndpointAutoScalingRuleAction
    ) -> DeleteEndpointAutoScalingRuleActionResult:
        row = await self._repository.get_auto_scaling_rule_by_id(action.id, load_endpoint=True)

        match action.requester_ctx.user_role:
            case UserRole.SUPERADMIN:
                pass
            case UserRole.ADMIN:
                if row.endpoint_row.domain != action.requester_ctx.domain_name:
                    raise GenericForbidden
            case UserRole.USER:
                if row.endpoint_row.created_user != action.requester_ctx.user_id:
                    raise GenericForbidden

        async def _do_mutate() -> MutationResult:
            await self._repository.delete_auto_scaling_rule(row)
            return MutationResult(
                success=True,
                message="Auto scaling rule removed",
                data=None,
            )

        res = await self._db_mutation_wrapper(_do_mutate)

        return DeleteEndpointAutoScalingRuleActionResult(
            success=res.success,
        )

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except sa.exc.StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            log.exception("db_mutation_wrapper(): other error")
            raise