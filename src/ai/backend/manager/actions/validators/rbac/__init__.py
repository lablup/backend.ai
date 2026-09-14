from dataclasses import dataclass

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


@dataclass
class VirtualEntityRBACValidators:
    """RBAC validators for the v2 action bases (actions/v2/{single_entity,bulk,scope,relation})."""

    scope: VirtualEntityScopeActionRBACValidator
    single_entity: VirtualEntitySingleEntityActionRBACValidator
    partial_bulk: VirtualEntityPartialBulkActionRBACValidator
    atomic_bulk: VirtualEntityAtomicBulkActionRBACValidator
    relation: VirtualEntityRelationActionRBACValidator

    def to_action_validators(self) -> V2ActionValidators:
        """Place every validator in this bundle into its shape's slot.

        The processors read the slots, so a validator missing from here never runs.
        """
        return V2ActionValidators(
            single_entity=[self.single_entity],
            partial_bulk=[self.partial_bulk],
            atomic_bulk=[self.atomic_bulk],
            scope=[self.scope],
            relation=[self.relation],
        )
