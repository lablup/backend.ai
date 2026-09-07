from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.testutils.action_validators import mock_virtual_entity_rbac_validators


@pytest.fixture
def mock_action_validators() -> ActionValidators:
    return ActionValidators(
        virtual_entity_rbac=mock_virtual_entity_rbac_validators(),
        rbac=RBACValidators(
            scope=MagicMock(spec=ScopeActionRBACValidator),
        ),
    )
