"""Tests for AppConfigService (merged AppConfig resolution) with a mocked repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigScopeType,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigResolveScope
from ai.backend.manager.services.app_config.actions.resolve import ResolveAppConfigAction
from ai.backend.manager.services.app_config.service import AppConfigService

_USER_UUID = uuid.uuid4()
_USER_ID = UserID(_USER_UUID)
_DOMAIN_ID = DomainID(uuid.uuid4())


def _fragment(
    *, scope_type: AppConfigScopeType, scope_id: str, rank: int, config: dict[str, object]
) -> AppConfigFragmentData:
    now = datetime.now(UTC)
    return AppConfigFragmentData(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name="theme",
        scope_type=scope_type,
        scope_id=scope_id,
        rank=rank,
        config=config,
        created_at=now,
        updated_at=now,
    )


class TestAppConfigService:
    @pytest.fixture
    def mock_fragment_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def service(self, mock_fragment_repository: MagicMock) -> AppConfigService:
        return AppConfigService(fragment_repository=mock_fragment_repository)

    async def test_resolve_deep_merges_applicable_fragments(
        self, service: AppConfigService, mock_fragment_repository: MagicMock
    ) -> None:
        # The repository returns the applicable fragments rank-ordered (low -> high).
        public = _fragment(
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id="public",
            rank=100,
            config={"theme": "light", "lang": "en"},
        )
        user = _fragment(
            scope_type=AppConfigScopeType.USER,
            scope_id=str(_USER_ID),
            rank=300,
            config={"theme": "dark"},
        )
        mock_fragment_repository.list_visible_fragments = AsyncMock(return_value=[public, user])

        result = await service.resolve(
            ResolveAppConfigAction(config_name="theme", domain_id=_DOMAIN_ID, user_id=_USER_ID)
        )

        assert result.app_config.config_name == "theme"
        assert result.app_config.fragments == [public, user]
        assert result.app_config.config == {"theme": "dark", "lang": "en"}
        assert result.user_id == _USER_ID
        mock_fragment_repository.list_visible_fragments.assert_called_once_with(
            "theme", AppConfigResolveScope(domain_id=_DOMAIN_ID, user_id=_USER_ID)
        )

    async def test_resolve_empty_projects_config_to_none(
        self, service: AppConfigService, mock_fragment_repository: MagicMock
    ) -> None:
        mock_fragment_repository.list_visible_fragments = AsyncMock(return_value=[])

        result = await service.resolve(
            ResolveAppConfigAction(config_name="unknown", domain_id=_DOMAIN_ID, user_id=_USER_ID)
        )

        assert result.app_config.fragments == []
        assert result.app_config.config is None
