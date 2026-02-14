from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
from ai.backend.manager.dependencies.processing.composer import (
    ProcessingComposer,
    ProcessingInput,
    ProcessingResources,
)


def _make_processing_input() -> ProcessingInput:
    """Create a ProcessingInput with all mock dependencies."""
    mock_config_provider = MagicMock()
    mock_config_provider.config.reporter.smtp = []
    mock_config_provider.config.reporter.action_monitors = []

    return ProcessingInput(
        message_queue=MagicMock(),
        log_events=False,
        event_observer=None,
        valkey_container_log=MagicMock(),
        valkey_stat=MagicMock(),
        valkey_stream=MagicMock(),
        schedule_coordinator=MagicMock(),
        scheduling_controller=MagicMock(),
        deployment_coordinator=MagicMock(),
        route_coordinator=MagicMock(),
        scheduler_repository=MagicMock(),
        event_hub=MagicMock(),
        agent_registry=MagicMock(),
        db=MagicMock(),
        idle_checker_host=MagicMock(),
        event_dispatcher_plugin_ctx=MagicMock(),
        repositories=MagicMock(),
        storage_manager=MagicMock(),
        config_provider=mock_config_provider,
        event_producer=MagicMock(),
        etcd=MagicMock(),
        valkey_live=MagicMock(),
        valkey_artifact_client=MagicMock(),
        event_fetcher=MagicMock(),
        background_task_manager=MagicMock(),
        error_monitor=MagicMock(),
        hook_plugin_ctx=MagicMock(),
        deployment_controller=MagicMock(),
        revision_generator_registry=MagicMock(),
        agent_cache=MagicMock(),
        notification_center=MagicMock(),
        appproxy_client_pool=MagicMock(),
        prometheus_client=MagicMock(),
        agent_client_pool=MagicMock(),
    )


class TestProcessingComposer:
    """Test ProcessingComposer integration."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.processing.bgtask_registry.BackgroundTaskHandlerRegistry"
    )
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.CommitSessionHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanGPUAllocMapsHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.PurgeImagesHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanImagesHandler")
    @patch("ai.backend.manager.dependencies.processing.composer.Dispatchers")
    @patch("ai.backend.manager.dependencies.processing.processors.Processors")
    @patch("ai.backend.manager.dependencies.processing.event_dispatcher.EventDispatcher")
    async def test_compose_produces_resources(
        self,
        mock_dispatcher_class: MagicMock,
        mock_processors_class: MagicMock,
        mock_dispatchers_class: MagicMock,
        mock_rescan_images: MagicMock,
        mock_purge_images: MagicMock,
        mock_rescan_gpu: MagicMock,
        mock_commit_session: MagicMock,
        mock_registry_class: MagicMock,
    ) -> None:
        """Composer should produce ProcessingResources with correct instances."""
        mock_event_dispatcher = MagicMock()
        mock_event_dispatcher.start = AsyncMock()
        mock_event_dispatcher.close = AsyncMock()
        mock_dispatcher_class.return_value = mock_event_dispatcher

        mock_processors = MagicMock()
        mock_processors_class.create.return_value = mock_processors

        mock_dispatchers = MagicMock()
        mock_dispatchers_class.return_value = mock_dispatchers

        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry

        setup_input = _make_processing_input()
        composer = ProcessingComposer()
        stack = DependencyBuilderStack()

        async with stack:
            async with composer.compose(stack, setup_input) as resources:
                assert isinstance(resources, ProcessingResources)
                assert resources.event_dispatcher is mock_event_dispatcher
                assert resources.processors is mock_processors

                # Verify Dispatchers was called and dispatch invoked
                mock_dispatchers_class.assert_called_once()
                mock_dispatchers.dispatch.assert_called_once_with(mock_event_dispatcher)

                # Verify event_dispatcher.start() was called
                mock_event_dispatcher.start.assert_called_once()

                # Verify bgtask registry was set
                mock_bgtask_mgr = cast(MagicMock, setup_input.background_task_manager)
                mock_bgtask_mgr.set_registry.assert_called_once_with(mock_registry)

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.processing.bgtask_registry.BackgroundTaskHandlerRegistry"
    )
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.CommitSessionHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanGPUAllocMapsHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.PurgeImagesHandler")
    @patch("ai.backend.manager.dependencies.processing.bgtask_registry.RescanImagesHandler")
    @patch("ai.backend.manager.dependencies.processing.composer.Dispatchers")
    @patch("ai.backend.manager.dependencies.processing.processors.Processors")
    @patch("ai.backend.manager.dependencies.processing.event_dispatcher.EventDispatcher")
    async def test_compose_initialization_order(
        self,
        mock_dispatcher_class: MagicMock,
        mock_processors_class: MagicMock,
        mock_dispatchers_class: MagicMock,
        mock_rescan_images: MagicMock,
        mock_purge_images: MagicMock,
        mock_rescan_gpu: MagicMock,
        mock_commit_session: MagicMock,
        mock_registry_class: MagicMock,
    ) -> None:
        """Composer should initialize in correct order:
        event_dispatcher -> processors -> dispatchers.dispatch -> start -> bgtask_registry.
        """
        call_order: list[str] = []

        def _track(label: str, return_value: Any) -> Any:
            """Record the call order and return the mock object."""
            call_order.append(label)
            return return_value

        mock_event_dispatcher = MagicMock()
        mock_event_dispatcher.start = AsyncMock(
            side_effect=lambda: call_order.append("dispatcher.start")
        )
        mock_event_dispatcher.close = AsyncMock()
        mock_dispatcher_class.return_value = mock_event_dispatcher
        mock_dispatcher_class.side_effect = lambda *a, **kw: _track(
            "EventDispatcher", mock_event_dispatcher
        )

        mock_processors = MagicMock()
        mock_processors_class.create.side_effect = lambda *a, **kw: _track(
            "Processors.create", mock_processors
        )

        mock_dispatchers = MagicMock()
        mock_dispatchers.dispatch.side_effect = lambda *a: call_order.append("dispatchers.dispatch")
        mock_dispatchers_class.return_value = mock_dispatchers
        mock_dispatchers_class.side_effect = lambda *a, **kw: _track(
            "Dispatchers", mock_dispatchers
        )

        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry_class.side_effect = lambda *a, **kw: _track("BgtaskRegistry", mock_registry)

        setup_input = _make_processing_input()
        composer = ProcessingComposer()
        stack = DependencyBuilderStack()

        async with stack:
            async with composer.compose(stack, setup_input):
                assert call_order == [
                    "EventDispatcher",
                    "Processors.create",
                    "Dispatchers",
                    "dispatchers.dispatch",
                    "dispatcher.start",
                    "BgtaskRegistry",
                ]
