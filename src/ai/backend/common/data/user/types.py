from dataclasses import dataclass
from typing import Self
from uuid import UUID

from ai.backend.common.dto.manager.context import UserIdentityCtx


@dataclass(frozen=True)
class UserData:
    user_id: UUID
    is_authorized: bool
    is_admin: bool
    is_superadmin: bool
    role: str
    domain_name: str


@dataclass(frozen=True)
class UserIdentity:
    user_uuid: UUID
    user_role: str
    user_email: str
    domain_name: str

    @classmethod
    def from_ctx(cls, ctx: UserIdentityCtx) -> Self:
        return cls(
            user_uuid=ctx.user_uuid,
            user_role=ctx.user_role,
            user_email=ctx.user_email,
            domain_name=ctx.domain_name,
        )
