from abc import ABC, abstractmethod
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.user import UserNotFound

__all__ = (
    "BulkLookupActionValidator",
    "AuthenticatedBulkLookupActionValidator",
)


class BulkLookupActionValidator(ABC):
    """Validates a bulk lookup before execution."""

    @abstractmethod
    async def validate(self, meta: BulkLookupActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")


class AuthenticatedBulkLookupActionValidator(BulkLookupActionValidator):
    """The whole of this shape's authorization, as the single lookup's is: a bulk lookup
    names no target either, so the action that follows answers for the ids it produced."""

    @override
    async def validate(self, meta: BulkLookupActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        if not user.is_authorized:
            raise GenericForbidden("Only authorized requests are allowed to perform this action")
