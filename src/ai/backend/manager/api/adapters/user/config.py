"""Legacy user config DTO conversion and user and dotfile processor calls."""

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileListItem,
    GetDotfileResponse,
    UpdateDotfileResponse,
)
from ai.backend.manager.data.dotfile.types import DotfileData, DotfileEntry
from ai.backend.manager.dto.user_config_input import (
    CreateDotfileInput,
    DeleteDefaultDotfileInput,
    UpdateDefaultDotfileInput,
)
from ai.backend.manager.errors.storage import DotfileNotFound
from ai.backend.manager.models.dotfile.conditions import DotfileConditions
from ai.backend.manager.models.dotfile.creators import DotfileEntryCreator
from ai.backend.manager.models.dotfile.orders import DotfileOrders
from ai.backend.manager.models.dotfile.purgers import DotfileEntryPurger
from ai.backend.manager.models.dotfile.searchers import DotfileSearcher
from ai.backend.manager.models.dotfile.updaters import DotfileEntryUpdater
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.services.dotfile.actions.search import SearchDotfilesAction
from ai.backend.manager.services.dotfile.processors import DotfileProcessors
from ai.backend.manager.services.user.actions.create_dotfile import (
    CreateDotfileAction,
)
from ai.backend.manager.services.user.actions.delete_default_dotfile import (
    DeleteDefaultDotfileAction,
)
from ai.backend.manager.services.user.actions.update_default_dotfile import (
    UpdateDefaultDotfileAction,
)
from ai.backend.manager.services.user.processors import UserProcessors


class UserConfigAdapter:
    _user: UserProcessors
    _dotfile: DotfileProcessors

    def __init__(self, user: UserProcessors, dotfile: DotfileProcessors) -> None:
        self._user = user
        self._dotfile = dotfile

    async def _search_default_dotfiles(
        self, user_id: UserID, path: str | None = None
    ) -> list[DotfileData]:
        conditions = [DotfileConditions.by_is_default(True)]
        if path is not None:
            conditions.append(DotfileConditions.by_path(path))
        result = await self._dotfile.search.run(
            SearchDotfilesAction(
                user_id=user_id,
                searcher=DotfileSearcher(
                    pagination=NoPagination(),
                    conditions=conditions,
                    orders=[DotfileOrders.created_at(), DotfileOrders.id()],
                ),
            )
        )
        return result.items

    async def create_dotfile(self, input: CreateDotfileInput) -> CreateDotfileResponse:
        await self._user.create_dotfile.run(
            CreateDotfileAction(
                user_id=input.user_id,
                creator=DotfileEntryCreator(
                    DotfileEntry(path=input.path, perm=input.perm, data=input.data)
                ),
            )
        )
        return CreateDotfileResponse()

    async def get_default_dotfile(self, user_id: UserID, path: str) -> GetDotfileResponse:
        dotfiles = await self._search_default_dotfiles(user_id, path)
        if not dotfiles:
            raise DotfileNotFound
        dotfile = dotfiles[0]
        return GetDotfileResponse(path=dotfile.path, perm=dotfile.perm, data=dotfile.data)

    async def get_default_dotfiles(self, user_id: UserID) -> list[DotfileListItem]:
        dotfiles = await self._search_default_dotfiles(user_id)
        return [DotfileListItem(path=d.path, permission=d.perm, data=d.data) for d in dotfiles]

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
