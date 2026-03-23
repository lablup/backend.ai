from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)


@pytest.fixture
def mock_action_validators() -> ActionValidators:
    return ActionValidators(
        rbac=RBACValidators(
            scope=MagicMock(spec=ScopeActionRBACValidator),
            single_entity=MagicMock(spec=SingleEntityActionRBACValidator),
        ),
    )
