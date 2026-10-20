"""Legacy user config DTO conversion and user and dotfile processor calls."""

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import StringMatchSpec
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
from ai.backend.manager.models.dotfile.creators import DotfileEntryCreator
from ai.backend.manager.models.dotfile.searchable_fields import DotfileSearchableFields
from ai.backend.manager.models.dotfile.searchers import DotfileSearcher
from ai.backend.manager.models.dotfile.updaters import DotfileUpdater
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.services.dotfile.actions.purge import PurgeDotfileAction
from ai.backend.manager.services.dotfile.actions.search import SearchDotfilesAction
from ai.backend.manager.services.dotfile.actions.update import UpdateDotfileAction
from ai.backend.manager.services.dotfile.processors import DotfileProcessors
from ai.backend.manager.services.user.actions.create_dotfile import (
    CreateDotfileAction,
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
        fields = DotfileSearchableFields.own
        conditions = [fields.is_default.filter.equals(True)]
        if path is not None:
            conditions.append(
                fields.path.filter.equals(
                    StringMatchSpec(value=path, case_insensitive=False, negated=False)
                )
            )
        result = await self._dotfile.search.run(
            SearchDotfilesAction(
                user_id=user_id,
                searcher=DotfileSearcher(
                    pagination=NoPagination(),
                    conditions=conditions,
                    orders=[fields.created_at.order.apply(True), fields.field_id.order.apply(True)],
                ),
            )
        )
        return result.items

    async def create_dotfile(self, input: CreateDotfileInput) -> CreateDotfileResponse:
        await self._user.create_dotfile.run(
            CreateDotfileAction(
                creator=DotfileEntryCreator(
                    owner=input.user_id,
                    entry=DotfileEntry(path=input.path, perm=input.perm, data=input.data),
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
        dotfiles = await self._search_default_dotfiles(input.user_id, input.path)
        if not dotfiles:
            raise DotfileNotFound
        await self._dotfile.update.run(
            UpdateDotfileAction(
                updater=DotfileUpdater(dotfile_id=dotfiles[0].id, perm=input.perm, data=input.data)
            )
        )
        return UpdateDotfileResponse()

    async def delete_default_dotfile(
        self, input: DeleteDefaultDotfileInput
    ) -> DeleteDotfileResponse:
        dotfiles = await self._search_default_dotfiles(input.user_id, input.path)
        if not dotfiles:
            raise DotfileNotFound
        await self._dotfile.purge.run(PurgeDotfileAction(dotfile_id=dotfiles[0].id))
        return DeleteDotfileResponse(success=True)
