from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)
from ai.backend.manager.actions.v2.single_entity.validator.base import SingleEntityActionValidator
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

__all__ = ("AuthenticatedActionValidator",)


class AuthenticatedActionValidator(SingleEntityActionValidator):
    """The sole gate of the public read path: the caller must be authenticated.

    Mirrors the global layer's validator of the same name. The entity is one every
    authenticated user may read, so naming it by id costs no permission.
    """

    @override
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
