from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.validator.base import LookupActionValidator
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

__all__ = ("AuthenticatedActionValidator",)


class AuthenticatedActionValidator(LookupActionValidator):
    """The sole gate of the lookup layer: the caller must be authenticated.

    Resolving a key reveals whether it exists, so the action that consumes the id has
    to answer a lookup failure and its own permission denial the same way. That is a
    convention this base cannot enforce.
    """

    @override
    async def validate(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
