from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta
from ai.backend.manager.actions.validator.base import ActionValidator
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound


class AuthorizationValidator(ActionValidator):
    async def validate(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
