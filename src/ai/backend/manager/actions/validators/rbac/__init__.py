from dataclasses import dataclass

from ai.backend.manager.actions.bulk.validator.rbac import (
    VirtualScopeBulkActionRBACValidator,
)
from ai.backend.manager.actions.scope.validator.rbac import (
    VirtualScopeScopeActionRBACValidator,
)
from ai.backend.manager.actions.single_entity.validator.rbac import (
    VirtualScopeSingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.legacy import (
    LegacyScopeActionRBACValidator,
    LegacySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)


@dataclass
class RBACValidators:
    scope: ScopeActionRBACValidator
    single_entity: SingleEntityActionRBACValidator
    bulk: BulkActionRBACValidator


@dataclass
class LegacyRBACValidators:
    scope: LegacyScopeActionRBACValidator
    single_entity: LegacySingleEntityActionRBACValidator


@dataclass
class VirtualScopeRBACValidators:
    """RBAC validators for the pure-ABC action bases (actions/{single_entity,bulk,scope})."""

    scope: VirtualScopeScopeActionRBACValidator
    single_entity: VirtualScopeSingleEntityActionRBACValidator
    bulk: VirtualScopeBulkActionRBACValidator
