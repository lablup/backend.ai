"""Legacy RBAC validators for processors invoked from legacy (non-v2) APIs.

These validators perform the same permission check as the strict validators,
but never raise on denial. They record the denial via log + Prometheus counter
so we can observe legacy-path violations without breaking legacy behavior.
"""

import logging
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.metrics.safe import SafeCounter
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
from ai.backend.manager.actions.validator.scope import ScopeActionValidator
from ai.backend.manager.actions.validator.single_entity import SingleEntityActionValidator
from ai.backend.manager.data.permission.role import ScopeChainPermissionCheckInput
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_rbac_legacy_denied_total = SafeCounter(
    name="backendai_manager_rbac_legacy_permission_denied_total",
    labelnames=["validator", "entity_type", "operation"],
    documentation=(
        "Number of RBAC permission denials observed on the legacy processor path. "
        "These are not enforced — the action still proceeds."
    ),
)


class LegacySingleEntityActionRBACValidator(SingleEntityActionValidator):
    """Non-enforcing RBAC validator for single-entity actions on legacy processors.

    Runs the same permission check as `SingleEntityActionRBACValidator` but only
    logs and records a metric when the check fails — never raises. Used so that
    legacy API endpoints retain their existing behavior while we gain visibility
    into which legacy call sites would be rejected under strict enforcement.
    """

    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        operation = action.operation_type().to_permission_operation()
        target = action.target_element()
        allowed = await self._repository.check_permission_with_scope_chain(
            ScopeChainPermissionCheckInput(
                user_id=user.user_id,
                target_element_ref=target,
                operation=operation,
                permission_entity_type=None,
            )
        )
        if not allowed:
            _rbac_legacy_denied_total.labels(
                validator="single_entity",
                entity_type=str(target.element_type),
                operation=str(operation),
            ).inc()
            log.warning(
                "legacy RBAC: user {} lacks permission {} on {} (not enforced)",
                user.user_id,
                operation,
                target,
            )


class LegacyScopeActionRBACValidator(ScopeActionValidator):
    """Non-enforcing RBAC validator for scope actions on legacy processors."""

    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        operation = action.operation_type().to_permission_operation()
        entity_type = action.entity_type()
        target = action.target_element()
        allowed = await self._repository.check_permission_with_scope_chain(
            ScopeChainPermissionCheckInput(
                user_id=user.user_id,
                target_element_ref=target,
                operation=operation,
                permission_entity_type=entity_type,
            )
        )
        if not allowed:
            _rbac_legacy_denied_total.labels(
                validator="scope",
                entity_type=str(entity_type),
                operation=str(operation),
            ).inc()
            log.warning(
                "legacy RBAC: user {} lacks permission {} on {} at {} (not enforced)",
                user.user_id,
                operation,
                entity_type,
                target,
            )
