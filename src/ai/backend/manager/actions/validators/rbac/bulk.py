from typing import Any, override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.actions.validator.bulk import (
    BulkActionValidator,
    BulkValidationResult,
    DeniedEntity,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.role import (
    BulkPermissionCheckInput,
    PermissionResolutionKey,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

_DENY_REASON = "permission_denied"


class BulkActionRBACValidator(BulkActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider

    @classmethod
    @override
    def name(cls) -> str:
        return "rbac"

    @override
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        entity_ids = list(action.entity_ids)
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return BulkValidationResult(
                allowed_entity_ids=entity_ids,
                denied_entities=[],
            )

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return BulkValidationResult(
                allowed_entity_ids=entity_ids,
                denied_entities=[],
            )
        element_type = action.entity_type().to_element()
        keys = [
            PermissionResolutionKey(
                user_id=user.user_id,
                element_type=element_type,
                entity_id=eid,
                subject_entity_type=element_type,
            )
            for eid in entity_ids
        ]
        permission_map = await self._repository.check_bulk_permission_with_scope_chain(
            BulkPermissionCheckInput(
                keys=keys,
                operation=action.operation_type().to_permission_operation(),
            )
        )
        allowed_entity_ids: list[str] = []
        denied_entities: list[DeniedEntity] = []
        for key in keys:
            if permission_map.get(key, False):
                allowed_entity_ids.append(key.entity_id)
            else:
                denied_entities.append(
                    DeniedEntity(entity_id=key.entity_id, deny_reason=_DENY_REASON)
                )
        return BulkValidationResult(
            allowed_entity_ids=allowed_entity_ids,
            denied_entities=denied_entities,
        )
