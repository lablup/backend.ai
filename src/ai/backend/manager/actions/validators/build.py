from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualEntityAtomicBulkActionRBACValidator,
    VirtualEntityPartialBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.relation.validator.rbac import (
    VirtualEntityRelationActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualEntityScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.validator.used_by import (
    VirtualEntityUsedByRBACValidator,
)
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
    VirtualEntitySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators.rbac import VirtualEntityRBACValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


def build_action_validators(
    permission_check_repository: RbacPermissionCheckRepository,
    config_provider: ManagerConfigProvider,
) -> V2ActionValidators:
    virtual_entity_rbac_validators = VirtualEntityRBACValidators(
        scope=VirtualEntityScopeActionRBACValidator(permission_check_repository, config_provider),
        used_by=VirtualEntityUsedByRBACValidator(permission_check_repository, config_provider),
        single_entity=VirtualEntitySingleEntityActionRBACValidator(
            permission_check_repository, config_provider
        ),
        partial_bulk=VirtualEntityPartialBulkActionRBACValidator(permission_check_repository),
        atomic_bulk=VirtualEntityAtomicBulkActionRBACValidator(permission_check_repository),
        relation=VirtualEntityRelationActionRBACValidator(
            permission_check_repository, config_provider
        ),
    )
    return virtual_entity_rbac_validators.to_action_validators()
