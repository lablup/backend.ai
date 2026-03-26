"""Central RBAC action registry list.

This module provides the canonical list of all RBAC action classes
that should be registered in the PermissionControllerService.
Keeping this list in a lightweight module allows tests to verify
registry completeness without importing the full service factory.
"""

from ai.backend.manager.actions.action.rbac import BaseRBACAction
from ai.backend.manager.actions.action.rbac_session import (
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantHardDeleteRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
)

RBAC_ACTION_REGISTRY: list[type[BaseRBACAction]] = [
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionGrantHardDeleteRBACAction,
]
