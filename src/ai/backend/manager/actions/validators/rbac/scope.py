import logging
from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, is_impersonating, triggered_user
from ai.backend.common.exception import UnreachableError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import BLANK_ID, OperationStatus
from ai.backend.manager.actions.validator.scope import ScopeActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.role import (
    PermissionResolutionKey,
    ScopeChainPermissionCheckInput,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScopeActionRBACValidator(ScopeActionValidator):
    _repository: PermissionControllerRepository
    _config_provider: ManagerConfigProvider
    _audit_log_repository: AuditLogRepository

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider
        self._audit_log_repository = audit_log_repository

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        target = action.target_element()
        allowed = await self._repository.check_permission_with_scope_chain(
            ScopeChainPermissionCheckInput(
                key=PermissionResolutionKey(
                    user_id=user.user_id,
                    element_type=target.element_type,
                    entity_id=target.element_id,
                    subject_entity_type=action.entity_type().to_element(),
                ),
                operation=action.operation_type().to_permission_operation(),
            )
        )
        if not allowed:
            # Audit the denial only while impersonating, to bound audit volume.
            if is_impersonating():
                await self._audit_denial(action, meta)
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission "
                f"{action.operation_type().to_permission_operation()} "
                f"on {action.entity_type()} at {action.target_element()}"
            )

    async def _audit_denial(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        trigger = triggered_user()
        acting = current_user()
        try:
            await self._audit_log_repository.create(
                Creator(
                    spec=AuditLogCreatorSpec(
                        action_id=meta.action_id,
                        entity_type=action.entity_type(),
                        operation=action.operation_type(),
                        created_at=meta.started_at,
                        description=(
                            f"Permission denied: {action.operation_type()} "
                            f"on {action.entity_type()} at {action.target_element().to_str()}"
                        ),
                        status=OperationStatus.ERROR,
                        entity_id=action.target_element().element_id or BLANK_ID,
                        request_id=current_request_id() or BLANK_ID,
                        triggered_by=str(trigger.user_id) if trigger else None,
                        acted_as=str(acting.user_id) if acting else None,
                        duration=None,
                    )
                )
            )
        except Exception as e:
            log.warning("Failed to record denial audit: {}", e)
