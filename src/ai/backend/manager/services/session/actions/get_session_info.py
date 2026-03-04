from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionSingleEntityAction
from ai.backend.manager.services.session.types import LegacySessionInfo


@dataclass
class GetSessionInfoAction(SessionSingleEntityAction):
    """Get information about a specific session.

    RBAC validation checks if the user has READ permission for this session.
    session_id will be resolved from session_name before RBAC validation.
    """

    session_name: str
    owner_access_key: AccessKey
    session_id: str = ""  # TODO: Resolve from session_name before RBAC validation

    @override
    def entity_id(self) -> str | None:
        return self.session_id if self.session_id else None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return self.session_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=self.session_id,
        )


@dataclass
class GetSessionInfoActionResult(BaseActionResult):
    session_info: LegacySessionInfo
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
