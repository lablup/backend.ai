"""Shared adapter for authenticated password changes."""

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.user.request import UpdatePasswordInput
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordAction
from ai.backend.manager.services.auth.processors import AuthProcessors


class AuthAdapter:
    _auth: AuthProcessors

    def __init__(self, auth: AuthProcessors) -> None:
        self._auth = auth

    async def update_password(
        self,
        user_id: UserID,
        domain_name: str,
        email: str,
        input: UpdatePasswordInput,
    ) -> bool:
        result = await self._auth.update_password.run(
            UpdatePasswordAction(
                user_id=user_id,
                domain_name=domain_name,
                email=email,
                old_password=input.old_password,
                new_password=input.new_password,
            )
        )
        return result.success
