import pytest

from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.testutils.action_validators import mock_virtual_entity_rbac_validators


@pytest.fixture
def mock_action_validators() -> ActionValidators:
    return mock_virtual_entity_rbac_validators().to_action_validators()
