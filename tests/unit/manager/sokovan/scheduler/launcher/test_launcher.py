"""Unit tests for Sokovan scheduler SessionLauncher.

Based on BEP-1033 test scenarios for launcher testing.

Test Scenarios:
- SC-LA-001 ~ SC-LA-004: Image Pulling
- SC-LA-005 ~ SC-LA-008: Kernel Creation
- SC-LA-009 ~ SC-LA-013: Network Setup
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.sokovan.recorder import RecorderContext
from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher
from ai.backend.manager.sokovan.scheduler.types import (
    ImageConfigData,
    SessionDataForPull,
    SessionDataForStart,
)

# =============================================================================
# TestSessionLauncherImagePulling (SC-LA-001 ~ SC-LA-004)
# =============================================================================


class TestSessionLauncherImagePulling:
    """Tests for image pulling functionality in SessionLauncher.

    Verifies the launcher correctly triggers image pulling on agents.
    """

    async def test_trigger_image_pulling_for_all_agents(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        sessions_for_pull_multiple: list[SessionDataForPull],
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-001: Image pulling triggered for all agents.

        Given: Sessions with kernels on different agents
        When: Trigger image pulling
        Then: check_and_pull called for each agent
        """
        # RecorderContext scope required for shared_phase in trigger_image_pulling
        session_ids = [s.session_id for s in sessions_for_pull_multiple]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.trigger_image_pulling(
                sessions_for_pull_multiple,
                image_config_default,
            )

        # Assert - check_and_pull called for both agents
        mock_client = mock_agent_client_pool._mock_client
        assert mock_client.check_and_pull.await_count == 2

    async def test_deduplicate_images_per_agent(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_pull_duplicate_images: SessionDataForPull,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-002: Duplicate images are deduplicated per agent.

        Given: Session with duplicate image references on same agent
        When: Trigger image pulling
        Then: Each unique image pulled only once per agent
        """
        session_ids = [session_for_pull_duplicate_images.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.trigger_image_pulling(
                [session_for_pull_duplicate_images],
                image_config_default,
            )

        # Assert - check_and_pull called once with deduplicated images
        mock_client = mock_agent_client_pool._mock_client
        mock_client.check_and_pull.assert_awaited_once()
        call_args = mock_client.check_and_pull.call_args
        images_dict = call_args[0][0]
        assert len(images_dict) == 1  # Only one unique image

    async def test_empty_session_list_does_nothing(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-003: Empty session list does nothing.

        Given: Empty session list
        When: Trigger image pulling
        Then: No agent calls made
        """
        # Act - empty list doesn't need RecorderContext
        await launcher.trigger_image_pulling([], image_config_default)

        # Assert - No check_and_pull calls
        mock_client = mock_agent_client_pool._mock_client
        mock_client.check_and_pull.assert_not_awaited()

    async def test_agent_pulling_failure_doesnt_block_others(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        sessions_for_pull_multiple: list[SessionDataForPull],
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-004: Agent pulling failure doesn't block other agents.

        Given: Multiple sessions, one agent fails
        When: Trigger image pulling
        Then: Other agents still receive pull requests (using gather)
        """
        # Arrange - First call fails, second succeeds
        mock_client = mock_agent_client_pool._mock_client
        mock_client.check_and_pull.side_effect = [
            RuntimeError("Agent 1 failed"),
            {},  # Agent 2 success
        ]

        session_ids = [s.session_id for s in sessions_for_pull_multiple]
        with RecorderContext.scope("test", entity_ids=session_ids):
            # Act - Should not raise
            await launcher.trigger_image_pulling(
                sessions_for_pull_multiple,
                image_config_default,
            )

        # Assert - Both agents were called despite failure
        assert mock_client.check_and_pull.await_count == 2


# =============================================================================
# TestSessionLauncherKernelCreation (SC-LA-005 ~ SC-LA-008)
# =============================================================================


class TestSessionLauncherKernelCreation:
    """Tests for kernel creation functionality in SessionLauncher.

    Verifies the launcher correctly creates kernels on agents.
    """

    @pytest.fixture(autouse=True)
    def setup_recorder_context(self) -> None:
        """Setup RecorderContext for kernel creation tests."""
        # Required for shared_phase and shared_step in start_sessions_for_handler

    async def test_start_single_kernel_session(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-005: Single kernel session started successfully.

        Given: Session with one kernel
        When: Start session
        Then: create_kernels called on agent
        """
        session_ids = [session_for_start_single_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel],
                image_config_default,
            )

        # Assert
        mock_client = mock_agent_client_pool._mock_client
        mock_client.create_kernels.assert_awaited_once()

        # Verify single kernel in create_kernels call
        call_args = mock_client.create_kernels.call_args
        kernel_ids = call_args[0][1]  # Second positional arg
        assert len(kernel_ids) == 1

    async def test_multi_kernel_cluster_session(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_multi_kernel: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-006: Multi-kernel cluster session started.

        Given: Session with multiple kernels on same agent
        When: Start session
        Then: All kernels created together
        """
        session_ids = [session_for_start_multi_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_multi_kernel],
                image_config_default,
            )

        # Assert
        mock_client = mock_agent_client_pool._mock_client
        mock_client.create_kernels.assert_awaited_once()

        # Verify kernel count in create_kernels call
        call_args = mock_client.create_kernels.call_args
        kernel_ids = call_args[0][1]  # Second positional arg
        assert len(kernel_ids) == 2

    async def test_session_without_kernels_raises_error(
        self,
        launcher: SessionLauncher,
        mock_repository: AsyncMock,
        session_for_start_no_kernels: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-007: Session without kernels updates error info.

        Given: Session with no kernels
        When: Start session
        Then: Error info updated (no exception raised due to exception handling)
        """
        session_ids = [session_for_start_no_kernels.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            # Act - Should handle exception internally
            await launcher.start_sessions_for_handler(
                [session_for_start_no_kernels],
                image_config_default,
            )

        # Assert - Error info should be updated
        mock_repository.update_session_error_info.assert_awaited()

    async def test_concurrent_session_start(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-008: Multiple sessions started concurrently.

        Given: Multiple sessions to start
        When: Start sessions
        Then: All sessions started concurrently (using gather)
        """
        sessions = [session_for_start_single_kernel, session_for_start_single_kernel]
        session_ids = [s.session_id for s in sessions]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                sessions,
                image_config_default,
            )

        # Assert - create_kernels called for each session
        mock_client = mock_agent_client_pool._mock_client
        assert mock_client.create_kernels.await_count == 2


# =============================================================================
# TestSessionLauncherNetworkSetup (SC-LA-009 ~ SC-LA-013)
# =============================================================================


class TestSessionLauncherNetworkSetup:
    """Tests for network setup functionality in SessionLauncher.

    Verifies the launcher correctly configures network for sessions.
    """

    async def test_volatile_network_single_node(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_repository: AsyncMock,
        session_for_start_multi_kernel: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-009: Volatile network for single-node multi-kernel session.

        Given: Single-node session with multiple kernels
        When: Start session
        Then: Local network created on agent
        """
        session_ids = [session_for_start_multi_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_multi_kernel],
                image_config_default,
            )

        # Assert - Local network creation was requested
        mock_client = mock_agent_client_pool._mock_client
        mock_client.create_local_network.assert_awaited()

    async def test_volatile_network_multi_node_overlay(
        self,
        launcher: SessionLauncher,
        mock_network_plugin_ctx: MagicMock,
        session_for_start_multi_node: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-010: Volatile network for multi-node uses overlay.

        Given: Multi-node cluster session
        When: Start session
        Then: Overlay network created via plugin
        """
        session_ids = [session_for_start_multi_node.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_multi_node],
                image_config_default,
            )

        # Assert - Network plugin was used
        network_plugin = mock_network_plugin_ctx.plugins["overlay"]
        network_plugin.create_network.assert_awaited()

    async def test_host_network_with_ssh_port_mapping(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-011: Host network creates SSH port mapping.

        Given: Session with HOST network type and multiple kernels
        When: Start session
        Then: SSH ports assigned for each kernel
        """
        session_ids = [session_for_start_host_network.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_host_network],
                image_config_default,
            )

        # Assert - Ports were assigned
        mock_client = mock_agent_client_pool._mock_client
        # assign_port called for each kernel in host mode
        assert mock_client.assign_port.await_count == 2

    async def test_network_id_persisted(
        self,
        launcher: SessionLauncher,
        mock_repository: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-012: Network ID is persisted after setup.

        Given: Session starting
        When: Network setup completes
        Then: Network ID updated in repository
        """
        session_ids = [session_for_start_single_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel],
                image_config_default,
            )

        # Assert - Network ID was updated
        mock_repository.update_session_network_id.assert_awaited()

    async def test_no_network_plugin_error(
        self,
        launcher: SessionLauncher,
        mock_network_plugin_ctx: MagicMock,
        mock_repository: AsyncMock,
        session_for_start_multi_node: SessionDataForStart,
        image_config_default: dict[str, ImageConfigData],
    ) -> None:
        """SC-LA-013: Missing network plugin reports error.

        Given: Multi-node session with missing network plugin
        When: Start session
        Then: Error captured and reported
        """
        # Arrange - Remove the overlay plugin
        mock_network_plugin_ctx.plugins = {}

        session_ids = [session_for_start_multi_node.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            # Act - Should handle exception internally
            await launcher.start_sessions_for_handler(
                [session_for_start_multi_node],
                image_config_default,
            )

        # Assert - Error info should be updated
        mock_repository.update_session_error_info.assert_awaited()
