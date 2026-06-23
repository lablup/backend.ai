"""Tests for AppConfigFragmentService with mocked repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListSearchResult
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
    AppConfigScopeType,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentForbidden,
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
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
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.update_my import (
    UpdateMyAppConfigFragmentAction,
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

    async def test_search(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.search(SearchAppConfigFragmentAction(querier=querier))

        assert result.data == [fragment]
        assert result.total_count == 1
        mock_repository.search.assert_called_once_with(querier)

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
        spec = AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2}))

        result = await service.update(
            UpdateAppConfigFragmentAction(fragment_id=existing.id, updater_spec=spec)
        )

        assert result.fragment == updated
        mock_repository.update.assert_called_once_with(existing.id, spec)

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
                    fragment_id=existing.id,
                    updater_spec=AppConfigFragmentUpdaterSpec(
                        config=OptionalState.update({"b": 2})
                    ),
                )
            )
        mock_repository.update.assert_not_called()

    # --- self-service update ---

    async def test_update_my_replaces_config(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID)
        updated = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(1))
        mock_repository.update = AsyncMock(return_value=updated)

        result = await service.update_my(
            UpdateMyAppConfigFragmentAction(
                fragment_id=existing.id, user_id=UserID(_USER_UUID), config={"b": 2}
            )
        )

        assert result.fragment == updated
        mock_repository.update.assert_called_once()
        called_id, called_spec = mock_repository.update.call_args.args
        assert called_id == existing.id
        assert called_spec.build_values() == {"config": {"b": 2}}

    async def test_update_my_clearing_is_empty_config(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID)
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(1))
        mock_repository.update = AsyncMock(return_value=_fragment())

        await service.update_my(
            UpdateMyAppConfigFragmentAction(
                fragment_id=existing.id, user_id=UserID(_USER_UUID), config={}
            )
        )

        _, called_spec = mock_repository.update.call_args.args
        assert called_spec.build_values() == {"config": {}}

    async def test_update_my_forbidden_when_not_owner(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment(scope_type=AppConfigScopeType.USER, scope_id=str(uuid.uuid4()))
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_allow_list_repository.search = AsyncMock(return_value=_allow_list_result(1))
        mock_repository.update = AsyncMock()

        with pytest.raises(AppConfigFragmentForbidden):
            await service.update_my(
                UpdateMyAppConfigFragmentAction(
                    fragment_id=existing.id, user_id=UserID(_USER_UUID), config={"b": 2}
                )
            )
        mock_repository.update.assert_not_called()

    async def test_update_my_forbidden_when_not_user_scope(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        existing = _fragment(scope_type=AppConfigScopeType.PUBLIC, scope_id="public")
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_repository.update = AsyncMock()

        with pytest.raises(AppConfigFragmentForbidden):
            await service.update_my(
                UpdateMyAppConfigFragmentAction(
                    fragment_id=existing.id, user_id=UserID(_USER_UUID), config={"b": 2}
                )
            )
        mock_repository.update.assert_not_called()

    # --- purge ---

    async def test_purge(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.purge = AsyncMock(return_value=fragment)

        result = await service.purge(PurgeAppConfigFragmentAction(fragment_id=fragment.id))

        assert result.fragment == fragment
        mock_repository.purge.assert_called_once_with(fragment.id)
