"""Tests for AppConfigFragmentService with mocked repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListSearchResult
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
    AppConfigScopeType,
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
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    Purger,
    Updater,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.service import AppConfigFragmentService
from ai.backend.manager.types import OptionalState

_USER_UUID = uuid.uuid4()
_USER_ID = str(_USER_UUID)


def _fragment(
    *,
    scope_type: AppConfigScopeType = AppConfigScopeType.USER,
    scope_id: str = _USER_ID,
    config_name: str = "theme",
) -> AppConfigFragmentData:
    now = datetime.now(UTC)
    return AppConfigFragmentData(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name=config_name,
        scope_type=scope_type,
        scope_id=scope_id,
        rank=100,
        config={"k": "v"},
        created_at=now,
        updated_at=now,
    )


def _allow_list_result(total_count: int) -> AppConfigAllowListSearchResult:
    return AppConfigAllowListSearchResult(
        items=[],
        total_count=total_count,
        has_next_page=False,
        has_previous_page=False,
    )


class TestAppConfigFragmentService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def mock_allow_list_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigAllowListRepository)

    @pytest.fixture
    def service(
        self, mock_repository: MagicMock, mock_allow_list_repository: MagicMock
    ) -> AppConfigFragmentService:
        return AppConfigFragmentService(
            repository=mock_repository,
            allow_list_repository=mock_allow_list_repository,
        )

    # --- create ---

    async def test_create_passes_write_gate(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        fragment = _fragment()
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(1))
        mock_repository.create = AsyncMock(return_value=fragment)
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_ID,
            config={"k": "v"},
        )

        result = await service.create(CreateAppConfigFragmentAction(creator_spec=spec))

        assert result.fragment == fragment
        mock_repository.create.assert_called_once_with(spec)

    async def test_create_rejected_when_not_allow_listed(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(0))
        mock_repository.create = AsyncMock()
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_ID,
            config={"k": "v"},
        )

        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.create(CreateAppConfigFragmentAction(creator_spec=spec))
        mock_repository.create.assert_not_called()

    # --- get / search ---

    async def test_get(self, service: AppConfigFragmentService, mock_repository: MagicMock) -> None:
        fragment = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=fragment)

        result = await service.get(GetAppConfigFragmentAction(fragment_id=fragment.id))

        assert result.fragment == fragment
        mock_repository.get_by_id.assert_called_once_with(fragment.id)

    async def test_get_not_found(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        missing_id = AppConfigFragmentID(uuid.uuid4())
        mock_repository.get_by_id = AsyncMock(
            side_effect=AppConfigFragmentNotFound(f"id {missing_id} not found")
        )

        with pytest.raises(AppConfigFragmentNotFound):
            await service.get(GetAppConfigFragmentAction(fragment_id=missing_id))

    async def test_admin_search(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.admin_search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.admin_search(AdminSearchAppConfigFragmentAction(querier=querier))

        assert result.data == [fragment]
        assert result.total_count == 1
        mock_repository.admin_search.assert_called_once_with(querier)

    async def test_scoped_search_builds_config_name_scope(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment(config_name="theme")
        mock_repository.scoped_search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.scoped_search(
            ScopedSearchAppConfigFragmentAction(config_name="theme", querier=querier)
        )

        assert result.data == [fragment]
        mock_repository.scoped_search.assert_called_once()
        called_querier, called_scopes = mock_repository.scoped_search.call_args.args
        assert called_querier is querier
        assert [s.config_name for s in called_scopes] == ["theme"]

    # --- admin update ---

    async def test_update_passes_write_gate(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment()
        updated = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(1))
        mock_repository.update = AsyncMock(return_value=updated)
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
            pk_value=existing.id,
        )

        result = await service.update(UpdateAppConfigFragmentAction(updater=updater))

        assert result.fragment == updated
        mock_repository.update.assert_called_once_with(updater)

    async def test_update_rejected_when_not_allow_listed(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(0))
        mock_repository.update = AsyncMock()

        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.update(
                UpdateAppConfigFragmentAction(
                    updater=Updater(
                        spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                        pk_value=existing.id,
                    )
                )
            )
        mock_repository.update.assert_not_called()

    # --- purge ---

    async def test_purge(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.purge = AsyncMock(return_value=fragment)
        purger = Purger(row_class=AppConfigFragmentRow, pk_value=fragment.id)

        result = await service.purge(PurgeAppConfigFragmentAction(purger=purger))

        assert result.fragment == fragment
        mock_repository.purge.assert_called_once_with(purger)
