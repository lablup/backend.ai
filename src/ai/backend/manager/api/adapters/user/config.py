"""Legacy user config DTO conversion and user processor calls."""

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileListItem,
    GetDotfileResponse,
    UpdateDotfileResponse,
)
from ai.backend.manager.data.dotfile.types import DotfileEntry
from ai.backend.manager.dto.user_config_input import (
    CreateDotfileInput,
    DeleteDefaultDotfileInput,
    UpdateDefaultDotfileInput,
)
from ai.backend.manager.models.dotfile.conditions import DotfileConditions
from ai.backend.manager.models.dotfile.creators import DotfileEntryCreator
from ai.backend.manager.models.dotfile.purgers import DotfileEntryPurger
from ai.backend.manager.models.dotfile.queriers import DotfileQuerier
from ai.backend.manager.models.dotfile.updaters import DotfileEntryUpdater
from ai.backend.manager.services.user.actions.create_keypair_dotfile import (
    CreateKeypairDotfileAction,
)
from ai.backend.manager.services.user.actions.delete_default_dotfile import (
    DeleteDefaultDotfileAction,
)
from ai.backend.manager.services.user.actions.get_dotfile import GetDotfileAction
from ai.backend.manager.services.user.actions.get_dotfiles import GetUserDotfilesAction
from ai.backend.manager.services.user.actions.update_default_dotfile import (
    UpdateDefaultDotfileAction,
)
from ai.backend.manager.services.user.processors import UserProcessors


class UserConfigAdapter:
    _user: UserProcessors

    def __init__(self, user: UserProcessors) -> None:
        self._user = user

    async def create_dotfile(self, input: CreateDotfileInput) -> CreateDotfileResponse:
        await self._user.create_dotfile.run(
            CreateKeypairDotfileAction(
                user_id=input.user_id,
                creator=DotfileEntryCreator(
                    DotfileEntry(path=input.path, perm=input.perm, data=input.data)
                ),
            )
        )
        return CreateDotfileResponse()

    async def get_default_dotfile(self, user_id: UserID, path: str) -> GetDotfileResponse:
        result = await self._user.get_dotfile.run(
            GetDotfileAction(
                user_id=user_id,
                querier=DotfileQuerier(
                    entity_type=user_id.entity_type(),
                    conditions=[
                        DotfileConditions.by_is_default(True),
                        DotfileConditions.by_path(path),
                    ],
                ),
            )
        )
        entry = result.dotfile
        return GetDotfileResponse(path=entry.path, perm=entry.perm, data=entry.data)

    async def get_default_dotfiles(self, user_id: UserID) -> list[DotfileListItem]:
        result = await self._user.get_default_dotfiles.run(GetUserDotfilesAction(user_id=user_id))
        return [
            DotfileListItem(path=e.path, permission=e.perm, data=e.data)
            for e in result.dotfiles.entries
        ]

    async def update_default_dotfile(
        self, input: UpdateDefaultDotfileInput
    ) -> UpdateDotfileResponse:
        await self._user.update_default_dotfile.run(
            UpdateDefaultDotfileAction(
                user_id=input.user_id,
                path=input.path,
                updater=DotfileEntryUpdater(perm=input.perm, data=input.data),
            )
        )
        return UpdateDotfileResponse()

    async def delete_default_dotfile(
        self, input: DeleteDefaultDotfileInput
    ) -> DeleteDotfileResponse:
        await self._user.delete_default_dotfile.run(
            DeleteDefaultDotfileAction(
                user_id=input.user_id,
                purger=DotfileEntryPurger(path=input.path),
            )
        )
        return DeleteDotfileResponse(success=True)
