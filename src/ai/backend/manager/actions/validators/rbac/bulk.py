from typing import override

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
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

_DENY_REASON = "permission_denied"


class BulkActionRBACValidator(BulkActionValidator):
    """RBAC validator for bulk actions; one bulk check across mixed element types."""

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
        self, action: BaseBulkAction, meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        element_refs = list(action.element_refs)
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return BulkValidationResult(
                allowed_entities=element_refs,
                denied_entities=[],
            )

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return BulkValidationResult(
                allowed_entities=element_refs,
                denied_entities=[],
            )

        keys = [
            PermissionResolutionKey(
                user_id=user.user_id,
                element_type=ref.element_type,
                entity_id=ref.element_id,
                subject_entity_type=ref.element_type,
            )
            for ref in element_refs
        ]

        permission_map = await self._repository.check_bulk_permission_with_scope_chain(
            BulkPermissionCheckInput(
                keys=keys,
                operation=action.operation_type().to_permission_operation(),
            )
        )

        allowed_entities: list[RBACElementRef] = []
        denied_entities: list[DeniedEntity] = []
        for key in keys:
            ref = RBACElementRef(element_type=key.element_type, element_id=key.entity_id)
            if permission_map.get(key, False):
                allowed_entities.append(ref)
            else:
                denied_entities.append(DeniedEntity(entity_ref=ref, deny_reason=_DENY_REASON))
        return BulkValidationResult(
            allowed_entities=allowed_entities,
            denied_entities=denied_entities,
        )
