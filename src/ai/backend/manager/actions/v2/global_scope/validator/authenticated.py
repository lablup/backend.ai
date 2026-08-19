from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

__all__ = ("AuthenticatedActionValidator",)


class AuthenticatedActionValidator(GlobalActionValidator):
    """The sole gate of the public read path: the caller must be authenticated.

    Mirrors the lookup layer's validator of the same name — the action targets
    state everyone may read, so authorization reduces to knowing who is asking.
    """

    @override
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
