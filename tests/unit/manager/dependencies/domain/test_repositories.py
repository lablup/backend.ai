from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.domain.repositories import (
    RepositoriesDependency,
    RepositoriesInput,
)


class TestRepositoriesDependency:
    """Test RepositoriesDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.domain.repositories.Repositories")
    async def test_provide_repositories(self, mock_repos_class: MagicMock) -> None:
        """Dependency should create Repositories with correct args."""
        mock_repos = MagicMock()
        mock_repos_class.create.return_value = mock_repos

        db = MagicMock()
        storage_manager = MagicMock()
        config_provider = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()
        valkey_image = MagicMock()

        dependency = RepositoriesDependency()
        repos_input = RepositoriesInput(
            db=db,
            storage_manager=storage_manager,
            config_provider=config_provider,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
            valkey_image=valkey_image,
        )

        async with dependency.provide(repos_input) as repos:
            assert repos is mock_repos
            mock_repos_class.create.assert_called_once()
            call_args = mock_repos_class.create.call_args
            args_obj = call_args.kwargs["args"]
            assert args_obj.db is db
            assert args_obj.storage_manager is storage_manager
            assert args_obj.config_provider is config_provider
            assert args_obj.valkey_stat_client is valkey_stat
            assert args_obj.valkey_live_client is valkey_live
            assert args_obj.valkey_schedule_client is valkey_schedule
            assert args_obj.valkey_image_client is valkey_image

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = RepositoriesDependency()
        assert dependency.stage_name == "repositories"
