from ai.backend.common.contexts.user import current_user
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

from ..action.base import BaseAction
from ..types import ActionTriggerMeta
from .validator.base import ActionValidator


class AuthorizationValidator(ActionValidator):
    async def validate(self, action: BaseAction, meta: ActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
