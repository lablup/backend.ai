"""RBAC scope targeting for CreateDeploymentAction owner delegation.

The deployment is created owned by ``created_user`` (the caller, or the
delegated ``owner_id``). RBAC authorizes the caller against that user's USER
scope, so the action's target must follow ``creator.metadata.created_user``.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock
from uuid import uuid4

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
)


def _make_action(created_user: uuid.UUID) -> CreateDeploymentAction:
    creator = MagicMock()
    creator.metadata.created_user = created_user
    return CreateDeploymentAction(creator=creator, auto_activate=False)


class TestCreateDeploymentActionScope:
    def test_target_is_created_user_scope(self) -> None:
        owner_id = uuid4()
        action = _make_action(owner_id)

        assert action.scope_type() == ScopeType.USER
        assert action.scope_id() == str(owner_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(owner_id)
