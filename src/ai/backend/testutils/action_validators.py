"""Mock factories for the manager action-validator bundles used by processor tests."""

from unittest.mock import MagicMock

from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualScopeAtomicBulkActionRBACValidator,
    VirtualScopePartialBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.relation.validator.rbac import (
    VirtualScopeRelationActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualScopeScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
    VirtualScopeSingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac import VirtualScopeRBACValidators


def mock_virtual_scope_rbac_validators() -> VirtualScopeRBACValidators:
    """Build a bundle of spec'd validator mocks for the pure-ABC action bases.

    ``MagicMock(spec=...)`` turns the async ``validate`` into an ``AsyncMock``
    automatically, so the mocks are awaitable out of the box.
    """
    return VirtualScopeRBACValidators(
        scope=MagicMock(spec=VirtualScopeScopeActionRBACValidator),
        single_entity=MagicMock(spec=VirtualScopeSingleEntityActionRBACValidator),
        partial_bulk=MagicMock(spec=VirtualScopePartialBulkActionRBACValidator),
        atomic_bulk=MagicMock(spec=VirtualScopeAtomicBulkActionRBACValidator),
        relation=MagicMock(spec=VirtualScopeRelationActionRBACValidator),
    )
