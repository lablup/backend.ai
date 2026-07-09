"""Tests for AppConfigService (merged AppConfig resolution) with a mocked repository."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
from ai.backend.manager.services.app_config.actions.resolve import ResolveAppConfigAction
from ai.backend.manager.services.app_config.actions.resolve_bulk import (
    ResolveBulkAppConfigAction,
)
from ai.backend.manager.services.app_config.service import AppConfigService

_USER_ID = UserID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())
_NOW = datetime.now(UTC)
_SCOPE = AppConfigScopeArguments(domain_id=_DOMAIN_ID, user_id=_USER_ID)

FragmentFactory = Callable[[str, dict[str, Any], AppConfigScopeType, str], AppConfigFragmentData]


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
        scope_id: str,
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
            make_fragment("theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, ""),
            make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.USER, str(_USER_ID)),
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
                "",
            ),
            make_fragment(
                "ui",
                {"nav": ["dashboard"], "theme": {"dark": True}},
                AppConfigScopeType.USER,
                str(_USER_ID),
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
    def bulk_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        # Visible fragments for both names, (config_name, rank)-ordered.
        fragments = [
            make_fragment("theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, ""),
            make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.USER, str(_USER_ID)),
            make_fragment("menu", {"items": ["a"]}, AppConfigScopeType.PUBLIC, ""),
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    @pytest.fixture
    def duplicate_name_fragments(
        self,
        make_fragment: FragmentFactory,
        mock_fragment_repository: MagicMock,
    ) -> list[AppConfigFragmentData]:
        fragments = [make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.PUBLIC, "")]
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
                "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, "public"
            )
        ]
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=fragments)
        return fragments

    async def test_resolve_deep_merges_applicable_fragments(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        deep_merge_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="theme", scope_arguments=_SCOPE)
        )

        assert result.app_config.config_name == "theme"
        assert result.app_config.fragments == deep_merge_fragments
        assert result.app_config.merged_config == {"theme": "dark", "lang": "en"}
        assert result.scope_id() == str(_USER_ID)
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], _SCOPE
        )

    async def test_resolve_replaces_lists_wholesale(
        self,
        service: AppConfigService,
        list_replace_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="ui", scope_arguments=_SCOPE)
        )

        # The user's shorter nav list fully replaces public's — no trailing "about"/"contact".
        assert result.app_config.merged_config == {
            "nav": ["dashboard"],
            "theme": {"light": True, "dark": True},
        }

    async def test_resolve_empty_yields_none_merged_config(
        self,
        service: AppConfigService,
        no_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="unknown", scope_arguments=_SCOPE)
        )

        # No contributing fragment -> None (unconfigured), not an empty {}.
        assert result.app_config.fragments == []
        assert result.app_config.merged_config is None

    async def test_resolve_bulk_groups_by_name_and_merges_each(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        bulk_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await service.resolve_app_config_bulk(
            ResolveBulkAppConfigAction(config_names=["theme", "menu", "unknown"], scope=_SCOPE)
        )

        # One AppConfigData per requested name, in request order.
        assert [c.config_name for c in result.app_configs] == ["theme", "menu", "unknown"]
        assert result.app_configs[0].merged_config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].merged_config == {"items": ["a"]}
        assert result.app_configs[2].merged_config is None  # unregistered -> no fragments
        assert result.scope_id() == str(_USER_ID)
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme", "menu", "unknown"], _SCOPE
        )

    async def test_resolve_bulk_repeats_duplicate_config_names_in_output(
        self,
        service: AppConfigService,
        duplicate_name_fragments: list[AppConfigFragmentData],
    ) -> None:
        # A config_name repeated in the request must be repeated in the output — each
        # position resolves independently, never collapsed into a single entry.
        result = await service.resolve_app_config_bulk(
            ResolveBulkAppConfigAction(config_names=["theme", "theme"], scope=_SCOPE)
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "theme"]
        assert result.app_configs[0].merged_config == {"theme": "dark"}
        assert result.app_configs[1].merged_config == {"theme": "dark"}

    async def test_resolve_without_scope_merges_public_fragments_only(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        public_only_fragments: list[AppConfigFragmentData],
    ) -> None:
        # scope=None is the anonymous, pre-login read: only public fragments are queried,
        # and the result is attributable to no user.
        result = await service.resolve_app_config(ResolveAppConfigAction(config_name="theme"))

        assert result.app_config.config_name == "theme"
        assert result.app_config.fragments == public_only_fragments
        assert result.app_config.merged_config == {"theme": "light", "lang": "en"}
        assert result._user_id is None
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], None
        )
