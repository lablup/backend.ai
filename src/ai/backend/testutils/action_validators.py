"""Mock factories for the manager action-validator bundles used by processor tests."""

from unittest.mock import MagicMock

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
from ai.backend.manager.actions.validators.rbac import VirtualEntityRBACValidators


def mock_virtual_entity_rbac_validators() -> VirtualEntityRBACValidators:
    """Build a bundle of spec'd validator mocks for the pure-ABC action bases.

    ``MagicMock(spec=...)`` turns the async ``validate`` into an ``AsyncMock``
    automatically, so the mocks are awaitable out of the box.
    """
    return VirtualEntityRBACValidators(
        scope=MagicMock(spec=VirtualEntityScopeActionRBACValidator),
        single_entity=MagicMock(spec=VirtualEntitySingleEntityActionRBACValidator),
        partial_bulk=MagicMock(spec=VirtualEntityPartialBulkActionRBACValidator),
        atomic_bulk=MagicMock(spec=VirtualEntityAtomicBulkActionRBACValidator),
        relation=MagicMock(spec=VirtualEntityRelationActionRBACValidator),
    )
