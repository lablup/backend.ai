from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class PublicResolveDefaultKeypairRateLimitAction(AuthGlobalAction):
    user_id: UserID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_resolve_default_keypair_rate_limit"


@dataclass(frozen=True)
class PublicResolveDefaultKeypairRateLimitResult:
    rate_limit: int | None
