"""build_action_validators fills every v2 validator slot."""

from __future__ import annotations

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
from ai.backend.manager.actions.validators.build import build_action_validators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class TestBuildActionValidators:
    def test_every_v2_slot_holds_its_validator(self) -> None:
        v2_validators = build_action_validators(
            MagicMock(spec=PermissionControllerRepository),
            MagicMock(spec=ManagerConfigProvider),
        )

        assert len(v2_validators.single_entity) == 1
        assert isinstance(
            v2_validators.single_entity[0], VirtualEntitySingleEntityActionRBACValidator
        )
        assert len(v2_validators.partial_bulk) == 1
        assert isinstance(
            v2_validators.partial_bulk[0], VirtualEntityPartialBulkActionRBACValidator
        )
        assert len(v2_validators.atomic_bulk) == 1
        assert isinstance(v2_validators.atomic_bulk[0], VirtualEntityAtomicBulkActionRBACValidator)
        assert len(v2_validators.scope) == 1
        assert isinstance(v2_validators.scope[0], VirtualEntityScopeActionRBACValidator)
        assert len(v2_validators.relation) == 1
        assert isinstance(v2_validators.relation[0], VirtualEntityRelationActionRBACValidator)
