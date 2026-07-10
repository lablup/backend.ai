from __future__ import annotations

from typing import cast

from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.common.data.user.types import UserData
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.base import BulkCreator, Creator, Purger, Updater
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create import (
    BulkCreateAppConfigFragmentAction,
    BulkCreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
    BulkPurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update import (
    BulkUpdateAppConfigFragmentAction,
    BulkUpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
    CreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
    ScopedSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)

__all__ = ("AppConfigFragmentService",)


class AppConfigFragmentService:
    """Write/read paths for app config fragments (not admin-only).

    Writes are authorized against the ``write_access`` tier of the target layer's
    ``app_config_allow_list`` entry — AppConfig's standalone authorization (there is no
    RBAC validator). The allow-list row's existence only *registers* the layer; who may
    write is decided by ``write_access`` (e.g. a user may manage their own ``user``-scope
    fragment; ``public`` / ``domain`` default to admin-only).
    """

    _repository: AppConfigFragmentRepository
    _allow_list_repository: AppConfigAllowListRepository

    def __init__(
        self,
        repository: AppConfigFragmentRepository,
        allow_list_repository: AppConfigAllowListRepository,
    ) -> None:
        self._repository = repository
        self._allow_list_repository = allow_list_repository

    async def _authorize_write(
        self,
        requester: UserData | None,
        config_name: str,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> None:
        """Raise ``AppConfigFragmentWriteNotAllowed`` unless ``requester`` may write the layer.

        The target layer's allow-list entry carries the ``write_access`` tier; a missing
        entry means the layer is not registered (nothing is writable there).
        """
        entry = await self._allow_list_repository.by_config_and_scope(config_name, scope_type)
        if entry is None:
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config {config_name!r} at scope {scope_type.value!r} is not "
                "allowed (no allow-list entry)."
            )
        if not entry.write_access.is_satisfied_by(requester, scope_type, scope_id):
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config {config_name!r} at scope {scope_type.value!r} is not "
                "allowed for this caller."
            )

    async def create(
        self, action: CreateAppConfigFragmentAction
    ) -> CreateAppConfigFragmentActionResult:
        spec = action.creator_spec
        await self._authorize_write(
            action.requester, spec.config_name, spec.scope_type, spec.scope_id
        )
        data = await self._repository.create(Creator(spec=spec))
        return CreateAppConfigFragmentActionResult(fragment=data)

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        data = await self._repository.get_by_id(action.fragment_id)
        return GetAppConfigFragmentActionResult(fragment=data)

    async def admin_search(
        self, action: AdminSearchAppConfigFragmentAction
    ) -> AdminSearchAppConfigFragmentActionResult:
        result = await self._repository.admin_search(action.querier)
        return AdminSearchAppConfigFragmentActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def _filter_readable(
        self, requester: UserData | None, items: list[AppConfigFragmentData]
    ) -> list[AppConfigFragmentData]:
        """Drop fragments whose layer ``read_access`` the ``requester`` does not satisfy.

        The tier per ``(config_name, scope_type)`` is looked up once and cached. Note this
        gates the returned page only; ``total_count`` still reflects the visible-scope match
        count before the read_access filter (paginated counts are not re-derived here).
        """
        cache: dict[tuple[str, AppConfigScopeType], AppConfigAccessLevel | None] = {}
        readable: list[AppConfigFragmentData] = []
        for item in items:
            key = (item.config_name, item.scope_type)
            if key not in cache:
                entry = await self._allow_list_repository.by_config_and_scope(
                    item.config_name, item.scope_type
                )
                cache[key] = entry.read_access if entry is not None else None
            read_access = cache[key]
            if read_access is not None and read_access.is_satisfied_by(
                requester, item.scope_type, item.scope_id
            ):
                readable.append(item)
        return readable

    async def scoped_search(
        self, action: ScopedSearchAppConfigFragmentAction
    ) -> ScopedSearchAppConfigFragmentActionResult:
        targets = list(action.targets())
        scopes = [t.to_search_scope() for t in targets]
        result = await self._repository.scoped_search(action.querier, scopes)
        readable = await self._filter_readable(action.requester, result.items)
        return ScopedSearchAppConfigFragmentActionResult(
            data=readable,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            queried_refs=[t.to_rbac_element_ref() for t in targets],
        )

    async def update(
        self, action: UpdateAppConfigFragmentAction
    ) -> UpdateAppConfigFragmentActionResult:
        fragment_id = cast(AppConfigFragmentID, action.updater.pk_value)
        existing = await self._repository.get_by_id(fragment_id)
        await self._authorize_write(
            action.requester, existing.config_name, existing.scope_type, existing.scope_id
        )
        data = await self._repository.update(action.updater)
        return UpdateAppConfigFragmentActionResult(fragment=data)

    async def purge(
        self, action: PurgeAppConfigFragmentAction
    ) -> PurgeAppConfigFragmentActionResult:
        fragment_id = cast(AppConfigFragmentID, action.purger.pk_value)
        existing = await self._repository.get_by_id(fragment_id)
        await self._authorize_write(
            action.requester, existing.config_name, existing.scope_type, existing.scope_id
        )
        data = await self._repository.purge(action.purger)
        return PurgeAppConfigFragmentActionResult(fragment=data)

    @staticmethod
    def _remap_failures(
        prefail: list[AppConfigFragmentBulkItemError],
        repo_failed: list[AppConfigFragmentBulkItemError],
        original_indices: list[int],
    ) -> list[AppConfigFragmentBulkItemError]:
        """Merge pre-authz failures with repo failures, remapping the latter to batch indices."""
        merged = list(prefail)
        merged.extend(
            AppConfigFragmentBulkItemError(index=original_indices[e.index], message=e.message)
            for e in repo_failed
        )
        merged.sort(key=lambda e: e.index)
        return merged

    async def bulk_create(
        self, action: BulkCreateAppConfigFragmentAction
    ) -> BulkCreateAppConfigFragmentActionResult:
        authorized: list[AppConfigFragmentCreatorSpec] = []
        original_indices: list[int] = []
        prefail: list[AppConfigFragmentBulkItemError] = []
        for index, spec in enumerate(action.creator_specs):
            try:
                await self._authorize_write(
                    action.requester, spec.config_name, spec.scope_type, spec.scope_id
                )
            except AppConfigFragmentWriteNotAllowed as e:
                prefail.append(AppConfigFragmentBulkItemError(index=index, message=str(e)))
                continue
            authorized.append(spec)
            original_indices.append(index)
        if authorized:
            result = await self._repository.bulk_create(BulkCreator(specs=authorized))
        else:
            result = AppConfigFragmentBulkResult(succeeded=[], failed=[])
        return BulkCreateAppConfigFragmentActionResult(
            succeeded=result.succeeded,
            failed=self._remap_failures(prefail, result.failed, original_indices),
        )

    async def bulk_update(
        self, action: BulkUpdateAppConfigFragmentAction
    ) -> BulkUpdateAppConfigFragmentActionResult:
        authorized: list[Updater[AppConfigFragmentRow]] = []
        original_indices: list[int] = []
        prefail: list[AppConfigFragmentBulkItemError] = []
        for index, updater in enumerate(action.updaters):
            fragment_id = cast(AppConfigFragmentID, updater.pk_value)
            try:
                existing = await self._repository.get_by_id(fragment_id)
                await self._authorize_write(
                    action.requester,
                    existing.config_name,
                    existing.scope_type,
                    existing.scope_id,
                )
            except (AppConfigFragmentNotFound, AppConfigFragmentWriteNotAllowed) as e:
                prefail.append(AppConfigFragmentBulkItemError(index=index, message=str(e)))
                continue
            authorized.append(updater)
            original_indices.append(index)
        if authorized:
            result = await self._repository.bulk_update(authorized)
        else:
            result = AppConfigFragmentBulkResult(succeeded=[], failed=[])
        return BulkUpdateAppConfigFragmentActionResult(
            succeeded=result.succeeded,
            failed=self._remap_failures(prefail, result.failed, original_indices),
        )

    async def bulk_purge(
        self, action: BulkPurgeAppConfigFragmentAction
    ) -> BulkPurgeAppConfigFragmentActionResult:
        authorized: list[Purger[AppConfigFragmentRow]] = []
        original_indices: list[int] = []
        prefail: list[AppConfigFragmentBulkItemError] = []
        for index, purger in enumerate(action.purgers):
            fragment_id = cast(AppConfigFragmentID, purger.pk_value)
            try:
                existing = await self._repository.get_by_id(fragment_id)
                await self._authorize_write(
                    action.requester,
                    existing.config_name,
                    existing.scope_type,
                    existing.scope_id,
                )
            except (AppConfigFragmentNotFound, AppConfigFragmentWriteNotAllowed) as e:
                prefail.append(AppConfigFragmentBulkItemError(index=index, message=str(e)))
                continue
            authorized.append(purger)
            original_indices.append(index)
        if authorized:
            result = await self._repository.bulk_purge(authorized)
        else:
            result = AppConfigFragmentBulkResult(succeeded=[], failed=[])
        return BulkPurgeAppConfigFragmentActionResult(
            succeeded=result.succeeded,
            failed=self._remap_failures(prefail, result.failed, original_indices),
        )
