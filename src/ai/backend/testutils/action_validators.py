"""Factories for the manager action-validator bundles used by processor tests."""

from unittest.mock import MagicMock

from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualEntityAtomicBulkActionRBACValidator,
    VirtualEntityPartialBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.global_scope.validator.rbac import (
    VirtualEntityGlobalActionRBACValidator,
)
from ai.backend.manager.actions.v2.membership.validator.rbac import (
    VirtualEntityMembershipActionRBACValidator,
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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


def build_global_gate(
    db: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> VirtualEntityGlobalActionRBACValidator:
    """The production global gate over the given database.

    For a test registry whose processors are actually run: a super admin passes without
    a read, and everyone else is answered by the graph in that database.
    """
    return VirtualEntityGlobalActionRBACValidator(
        RbacPermissionCheckRepository(PermissionOpsProvider(db), config_provider),
        config_provider,
    )


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
        membership=MagicMock(spec=VirtualEntityMembershipActionRBACValidator),
        global_scope=MagicMock(spec=VirtualEntityGlobalActionRBACValidator),
    )
