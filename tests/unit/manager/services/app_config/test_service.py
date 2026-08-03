"""Tests for AppConfigService (merged AppConfig get) with a mocked repository."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config.actions.get import GetAppConfigsAction
from ai.backend.manager.services.app_config.service import AppConfigService

_USER_ID = UserID(uuid.uuid4())

# The same owner seen as a fragment's scope_id, which is polymorphic over scope kinds.
_USER_SCOPE_ID = AppConfigScopeID(_USER_ID)
_NOW = datetime.now(UTC)

FragmentFactory = Callable[
    [str, dict[str, Any], AppConfigScopeType, AppConfigScopeID | None],
    AppConfigFragmentData,
]


@pytest.fixture
def make_fragment() -> FragmentFactory:
    """Factory for an ``AppConfigFragmentData`` — the caller names the fragment's identity
    (``config_name``, ``config``, ``scope_type``, ``scope_id``); only the id and timestamps
    (which the merge does not read) are filled in.
    """

    def _make(
        config_name: str,
        config: dict[str, Any],
        scope_type: AppConfigScopeType,
        scope_id: AppConfigScopeID | None,
    ) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name=config_name,
            scope_type=scope_type,
            scope_id=scope_id,
            config=config,
            created_at=_NOW,
            updated_at=_NOW,
        )

    return _make


class TestAppConfigService:
    @pytest.fixture
    def mock_fragment_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def service(self, mock_fragment_repository: MagicMock) -> AppConfigService:
        return AppConfigService(fragment_repository=mock_fragment_repository)

    @pytest.fixture
    def deep_merge_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        # Rank-ordered (low -> high), so the user fragment overrides on merge.
        fragments = [
            make_fragment(
                "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, None
            ),
            make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.USER, _USER_SCOPE_ID),
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def list_replace_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        # A higher-rank list overrides the lower one WHOLE; nested dicts still recurse.
        fragments = [
            make_fragment(
                "ui",
                {"nav": ["home", "about", "contact"], "theme": {"light": True}},
                AppConfigScopeType.PUBLIC,
                None,
            ),
            make_fragment(
                "ui",
                {"nav": ["dashboard"], "theme": {"dark": True}},
                AppConfigScopeType.USER,
                _USER_SCOPE_ID,
            ),
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def no_fragments(
        self,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        fragments: list[AppConfigFragmentData] = []
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def two_name_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        # Visible fragments for both names, (config_name, rank)-ordered.
        fragments = [
            make_fragment(
                "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, None
            ),
            make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.USER, _USER_SCOPE_ID),
            make_fragment("menu", {"items": ["a"]}, AppConfigScopeType.PUBLIC, None),
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def duplicate_name_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        fragments = [make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.PUBLIC, None)]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def public_only_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        fragments = [
            make_fragment(
                "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, None
            )
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    async def test_get_deep_merges_applicable_fragments(
        self,
        service: AppConfigService,
        deep_merge_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["theme"], user_id=_USER_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["theme"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}

    async def test_get_scopes_the_query_to_the_injected_user(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        deep_merge_fragments: list[AppConfigFragmentData],
    ) -> None:
        # The acting user is the whole scope, so a caller cannot name someone else's config.
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["theme"], user_id=_USER_ID)
        )

        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], _USER_ID
        )
        assert result.scope_id() == str(_USER_ID)

    async def test_get_replaces_lists_wholesale(
        self,
        service: AppConfigService,
        list_replace_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["ui"], user_id=_USER_ID)
        )

        # The user's shorter nav list fully replaces public's — no trailing "about"/"contact".
        assert result.app_configs[0].config == {
            "nav": ["dashboard"],
            "theme": {"light": True, "dark": True},
        }

    async def test_get_groups_by_name_and_merges_each(
        self,
        service: AppConfigService,
        two_name_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["theme", "menu"], user_id=_USER_ID)
        )

        # One AppConfigData per requested name, in request order.
        assert [c.config_name for c in result.app_configs] == ["theme", "menu"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].config == {"items": ["a"]}

    async def test_get_repeats_duplicate_config_names_in_output(
        self,
        service: AppConfigService,
        duplicate_name_fragments: list[AppConfigFragmentData],
    ) -> None:
        # A config_name repeated in the request must be repeated in the output — each
        # position is merged independently, never collapsed into a single entry.
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["theme", "theme"], user_id=_USER_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "theme"]
        assert result.app_configs[0].config == {"theme": "dark"}
        assert result.app_configs[1].config == {"theme": "dark"}

    async def test_get_without_matching_fragments_returns_an_empty_merge(
        self,
        service: AppConfigService,
        no_fragments: list[AppConfigFragmentData],
    ) -> None:
        # No contributing fragment is an empty merge, not a 404.
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["unknown"], user_id=_USER_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["unknown"]
        assert result.app_configs[0].config == {}

    async def test_get_keeps_the_merged_names_alongside_an_absent_one(
        self,
        service: AppConfigService,
        two_name_fragments: list[AppConfigFragmentData],
    ) -> None:
        # "unknown" contributes nothing, but that must not withhold the names that did merge.
        result = await service.get_app_configs(
            GetAppConfigsAction(config_names=["theme", "menu", "unknown"], user_id=_USER_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "menu", "unknown"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].config == {"items": ["a"]}
        assert result.app_configs[2].config == {}

    async def test_get_without_an_injected_user_merges_public_fragments_only(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        public_only_fragments: list[AppConfigFragmentData],
    ) -> None:
        # Naming no user is the anonymous, pre-login read: only public fragments are queried.
        result = await service.get_app_configs(GetAppConfigsAction(config_names=["theme"]))

        assert result.app_configs[0].config == {"theme": "light", "lang": "en"}
        assert result._user_id is None
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], None
        )
