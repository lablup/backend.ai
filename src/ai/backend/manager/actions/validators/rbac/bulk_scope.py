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
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

_DENY_REASON = "permission_denied"


class BulkScopeActionRBACValidator(BulkActionValidator):
    """Bulk analog of ``ScopeActionRBACValidator``: authorize a bulk action at each of its
    scope targets by the caller's permission on the action's *own* entity type.

    ``BulkActionRBACValidator`` checks each target as the entity itself (subject =
    ``ref.element_type``), which fits bulk actions whose targets are entities. Here the
    targets are *scopes*, so the checked subject is ``action.entity_type()`` — e.g. "create
    APP_CONFIG_FRAGMENT in scope X", not "act on the USER / DOMAIN scope itself". A global
    target (no scope grants its resource op) is denied, so only a superadmin passes.
    """

    _repository: PermissionControllerRepository
    _config_provider: ManagerConfigProvider

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
        return "rbac_scope"

    @override
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        element_refs = [t.to_rbac_element_ref() for t in action.targets()]
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return BulkValidationResult(allowed_entities=element_refs, denied_entities=[])

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return BulkValidationResult(allowed_entities=element_refs, denied_entities=[])

        subject_entity_type = action.entity_type().to_element()
        keys = [
            PermissionResolutionKey(
                user_id=user.user_id,
                element_type=ref.element_type,
                entity_id=ref.element_id,
                subject_entity_type=subject_entity_type,
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
        for ref, key in zip(element_refs, keys, strict=True):
            if permission_map.get(key, False):
                allowed_entities.append(ref)
            else:
                denied_entities.append(DeniedEntity(entity_ref=ref, deny_reason=_DENY_REASON))
        return BulkValidationResult(
            allowed_entities=allowed_entities,
            denied_entities=denied_entities,
        )
