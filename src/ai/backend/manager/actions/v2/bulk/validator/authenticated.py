from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import AtomicBulkActionValidator
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

__all__ = ("AuthenticatedAtomicBulkActionValidator",)


class AuthenticatedAtomicBulkActionValidator(AtomicBulkActionValidator):
    """The sole gate of the public bulk read path: the caller must be authenticated.

    Mirrors the single-entity validator of the same name; the entities are ones every
    authenticated user may read, so naming them by id costs no permission.
    """

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
