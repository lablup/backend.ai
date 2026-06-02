from dataclasses import dataclass

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
