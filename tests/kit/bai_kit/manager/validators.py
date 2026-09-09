"""The validator bundles the composer assembles inline.

TEMPORARY COPY of ``dependencies/processing/composer.py`` lines 380-423. BA-7778 extracts
the same function into src; when it lands, this module becomes a one-line import of it.
"""

from __future__ import annotations

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
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
    VirtualEntitySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import (
    LegacyRBACValidators,
    RBACValidators,
    VirtualEntityRBACValidators,
)
from ai.backend.manager.actions.validators.rbac.legacy import (
    LegacyScopeActionRBACValidator,
    LegacySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


def build_action_validators(
    permission_controller_repository: PermissionControllerRepository,
    config_provider: ManagerConfigProvider,
) -> tuple[ActionValidators, V2ActionValidators]:
    rbac_validators = RBACValidators(
        scope=ScopeActionRBACValidator(permission_controller_repository, config_provider),
    )
    legacy_rbac_validators = LegacyRBACValidators(
        scope=LegacyScopeActionRBACValidator(permission_controller_repository),
        single_entity=LegacySingleEntityActionRBACValidator(permission_controller_repository),
    )
    virtual_entity_rbac_validators = VirtualEntityRBACValidators(
        scope=VirtualEntityScopeActionRBACValidator(
            permission_controller_repository, config_provider
        ),
        single_entity=VirtualEntitySingleEntityActionRBACValidator(
            permission_controller_repository, config_provider
        ),
        partial_bulk=VirtualEntityPartialBulkActionRBACValidator(
            permission_controller_repository, config_provider
        ),
        atomic_bulk=VirtualEntityAtomicBulkActionRBACValidator(
            permission_controller_repository, config_provider
        ),
        relation=VirtualEntityRelationActionRBACValidator(
            permission_controller_repository, config_provider
        ),
    )
    return (
        ActionValidators(
            rbac=rbac_validators,
            legacy_rbac=legacy_rbac_validators,
            virtual_entity_rbac=virtual_entity_rbac_validators,
        ),
        virtual_entity_rbac_validators.to_action_validators(),
    )
