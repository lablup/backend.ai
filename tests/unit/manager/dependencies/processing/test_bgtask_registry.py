from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.processing.bgtask_registry import (
    BgtaskRegistryDependency,
    BgtaskRegistryInput,
)


class TestBgtaskRegistryDependency:
    """Test BgtaskRegistryDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.CommitSessionHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanGPUAllocMapsHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.PurgeImagesHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanImagesHandler")
    @patch(
        "ai.backend.manager.dependencies.processing.bgtask_registry.BackgroundTaskHandlerRegistry"
    )
    async def test_provide_bgtask_registry(
        self,
        mock_registry_class: MagicMock,
        mock_rescan_images: MagicMock,
        mock_purge_images: MagicMock,
        mock_rescan_gpu: MagicMock,
        mock_commit_session: MagicMock,
    ) -> None:
        """Dependency should create registry, register handlers, and set on manager."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry

        mock_processors = MagicMock()
        mock_bgtask_manager = MagicMock()
        mock_repositories = MagicMock()
        mock_agent_client_pool = MagicMock()
        mock_agent_registry = MagicMock()
        mock_event_hub = MagicMock()
        mock_event_fetcher = MagicMock()

        dependency = BgtaskRegistryDependency()
        registry_input = BgtaskRegistryInput(
            processors=mock_processors,
            background_task_manager=mock_bgtask_manager,
            repositories=mock_repositories,
            agent_client_pool=mock_agent_client_pool,
            agent_registry=mock_agent_registry,
            event_hub=mock_event_hub,
            event_fetcher=mock_event_fetcher,
        )

        async with dependency.provide(registry_input) as registry:
            assert registry is mock_registry

            # Verify 4 handlers registered
            assert mock_registry.register.call_count == 4

            # Verify RescanImagesHandler created with processors
            mock_rescan_images.assert_called_once_with(mock_processors)

            # Verify PurgeImagesHandler created with processors
            mock_purge_images.assert_called_once_with(mock_processors)

            # Verify RescanGPUAllocMapsHandler created with correct args
            mock_rescan_gpu.assert_called_once_with(
                agent_repository=mock_repositories.agent.repository,
                agent_client_pool=mock_agent_client_pool,
            )

            # Verify CommitSessionHandler created with correct args
            mock_commit_session.assert_called_once_with(
                session_repository=mock_repositories.session.repository,
                image_repository=mock_repositories.image.repository,
                agent_registry=mock_agent_registry,
                event_hub=mock_event_hub,
                event_fetcher=mock_event_fetcher,
            )

            # Verify set_registry called
            mock_bgtask_manager.set_registry.assert_called_once_with(mock_registry)
