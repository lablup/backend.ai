"""Unit tests for Sokovan scheduler SessionLauncher.

Based on BEP-1033 test scenarios for launcher testing.

Test Scenarios:
- SC-LA-001 ~ SC-LA-004: Image Pulling
- SC-LA-005 ~ SC-LA-008: Kernel Creation
- SC-LA-009 ~ SC-LA-015: Network Setup
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from callosum.rpc import RPCUserError

from ai.backend.common.types import AgentId, AutoPullBehavior
from ai.backend.manager.errors.agent import AgentConnectionUnavailable
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.launcher import launcher as launcher_module
from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher
from ai.backend.manager.sokovan.scheduler.results import FailureDisposition
from ai.backend.manager.views.sokovan.config import NetworkSetup
from ai.backend.manager.views.sokovan.image import ImageConfigData
from ai.backend.manager.views.sokovan.lifecycle import (
    SessionDataForPull,
    SessionDataForStart,
)


async def _never_returns(*args: Any, **kwargs: Any) -> Any:
    await asyncio.Event().wait()


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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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

    @pytest.mark.parametrize("auto_pull", list(AutoPullBehavior))
    async def test_kernel_creation_follows_auto_pull_config(
        self,
        auto_pull: AutoPullBehavior,
        launcher: SessionLauncher,
        mock_config_provider: MagicMock,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """Kernel creation carries the configured auto_pull behavior.

        Given: auto_pull configured in docker.image
        When: Start session
        Then: create_kernels receives that behavior in the kernel and image configs
        """
        mock_config_provider.config.docker.image.auto_pull.value = auto_pull.value

        session_ids = [session_for_start_single_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel],
                image_config_default,
            )

        mock_client = mock_agent_client_pool._mock_client
        mock_client.create_kernels.assert_awaited_once()
        kernel_configs = mock_client.create_kernels.call_args[0][2]
        assert [c["auto_pull"] for c in kernel_configs] == [auto_pull]
        assert [c["image"]["auto_pull"] for c in kernel_configs] == [auto_pull]

    async def test_agent_kernel_creation_failure_logged_at_error(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Kernel creation fails on one agent -> that exception is logged at error."""
        error = RuntimeError("agent refused kernel creation")
        mock_agent_client_pool._mock_client.create_kernels.side_effect = error

        session_ids = [session_for_start_single_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel],
                image_config_default,
            )

        (record,) = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert record.__dict__["log_tag_agent_id"] == "agent-1"
        assert record.__dict__["log_tag_session_id"] == str(
            session_for_start_single_kernel.session_id
        )
        assert record.exc_info is not None
        assert record.exc_info[1] is error
        mock_valkey_schedule.record_session_failed_agents.assert_awaited_once()


class TestSessionLauncherStartFailures:
    """Sessions the launcher could not start are returned with a disposition, never dropped."""

    async def test_network_setup_failure_is_replace_and_blames_no_agent(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _refuses(
            session: SessionDataForStart, assigned_ports: list[tuple[AgentId, int]]
        ) -> NetworkSetup:
            raise ServerMisconfiguredError("the network could not be set up")

        monkeypatch.setattr(launcher, "_setup_network_configuration", _refuses)
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        failure = failed[session_id]
        assert "ServerMisconfiguredError" in failure.message
        assert failure.disposition is FailureDisposition.REPLACE
        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()
        mock_repository.update_session_error_info.assert_awaited()
        mock_valkey_schedule.record_session_failed_agents.assert_not_awaited()

    async def test_missing_network_plugin_blames_no_agent(
        self,
        launcher: SessionLauncher,
        mock_network_plugin_ctx: MagicMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_multi_node: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """The manager lacks the configured driver: no agent is at fault, none is avoided."""
        mock_network_plugin_ctx.plugins = {}
        session_id = session_for_start_multi_node.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_multi_node], image_config_default
            )

        assert "ServerMisconfiguredError" in failed[session_id].message
        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_valkey_schedule.record_session_failed_agents.assert_not_awaited()

    async def test_agent_failing_local_network_setup_is_recorded_alone(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_multi_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """The agent asked to make the local network failed: only that agent is avoided."""
        mock_client = mock_agent_client_pool._mock_client
        mock_client.create_local_network.side_effect = RuntimeError("bridge creation failed")
        session_id = session_for_start_multi_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_multi_kernel], image_config_default
            )

        assert "AgentNetworkSetupFailed" in failed[session_id].message
        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_client.create_kernels.assert_not_awaited()
        mock_valkey_schedule.record_session_failed_agents.assert_awaited_once_with(
            session_id, [session_for_start_multi_kernel.kernels[0].agent_id]
        )

    async def test_failure_before_kernel_creation_is_replace(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _boom() -> tuple[str, str]:
            raise RuntimeError("could not make the cluster ssh keypair")

        monkeypatch.setattr(launcher, "_create_cluster_ssh_keypair", _boom)
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()

    async def test_session_without_assigned_agent_is_replace(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        for kernel in session_for_start_single_kernel.kernels:
            kernel.agent_id = None
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()

    async def test_started_session_is_not_reported(
        self,
        launcher: SessionLauncher,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        session_ids = [session_for_start_single_kernel.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert failed == {}

    async def test_refused_kernel_creation_is_abandon(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        mock_agent_client_pool._mock_client.create_kernels.side_effect = RPCUserError(
            "ImagePullFailedError", "ImagePullFailedError('no such image')", ""
        )
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.ABANDON

    @pytest.mark.parametrize(
        "error",
        [
            TimeoutError(),
            AgentConnectionUnavailable(AgentId("agent-1"), "connection unhealthy"),
            RuntimeError("the transport went away mid-create"),
        ],
    )
    async def test_kernel_creation_not_answered_by_the_agent_is_not_a_failure(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        error: Exception,
    ) -> None:
        """The agent may still be creating: the session goes on and the creation timeout owns it."""
        mock_agent_client_pool._mock_client.create_kernels.side_effect = error
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert failed == {}
        mock_valkey_schedule.record_session_failed_agents.assert_awaited_once()

    async def test_refusal_beside_an_unanswered_agent_is_not_a_failure(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_multi_node: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """One agent may still be creating, so the session is not given up under it."""
        mock_agent_client_pool._mock_client.create_kernels.side_effect = [
            RPCUserError("ImagePullFailedError", "ImagePullFailedError('no such image')", ""),
            TimeoutError(),
        ]
        session_id = session_for_start_multi_node.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_multi_node], image_config_default
            )

        assert mock_agent_client_pool._mock_client.create_kernels.await_count == 2
        assert failed == {}

    async def test_failure_before_dispatch_is_replace_when_its_error_is_not_stored(
        self,
        launcher: SessionLauncher,
        mock_repository: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _boom() -> tuple[str, str]:
            raise RuntimeError("could not make the cluster ssh keypair")

        monkeypatch.setattr(launcher, "_create_cluster_ssh_keypair", _boom)
        mock_repository.update_session_error_info.side_effect = ConnectionError("db is down")
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert "could not make the cluster ssh keypair" in failed[session_id].message
        assert failed[session_id].disposition is FailureDisposition.REPLACE

    async def test_network_setup_failure_is_replace_when_its_error_is_not_stored(
        self,
        launcher: SessionLauncher,
        mock_repository: AsyncMock,
        session_for_start_single_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _refuses(
            session: SessionDataForStart, assigned_ports: list[tuple[AgentId, int]]
        ) -> NetworkSetup:
            raise ServerMisconfiguredError("the network could not be set up")

        monkeypatch.setattr(launcher, "_setup_network_configuration", _refuses)
        mock_repository.update_session_error_info.side_effect = ConnectionError("db is down")
        session_id = session_for_start_single_kernel.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_single_kernel], image_config_default
            )

        assert "ServerMisconfiguredError" in failed[session_id].message
        assert failed[session_id].disposition is FailureDisposition.REPLACE

    async def test_start_timeout_after_dispatch_is_not_a_failure(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """START_SESSION_TIMEOUT may fire while agents are creating: never torn down for it."""
        monkeypatch.setattr(launcher_module, "START_SESSION_TIMEOUT_SEC", 0.05)
        mock_client = mock_agent_client_pool._mock_client
        mock_client.assign_port.side_effect = [22001, 22002]
        mock_client.create_kernels.side_effect = _never_returns
        session_id = session_for_start_host_network.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_host_network], image_config_default
            )

        assert failed == {}
        mock_client.release_port.assert_not_awaited()

    async def test_start_timeout_before_dispatch_is_replace_and_releases_ports(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """No agent was asked to create yet: re-placed, and the host ports given back."""
        monkeypatch.setattr(launcher_module, "START_SESSION_TIMEOUT_SEC", 0.05)
        monkeypatch.setattr(launcher, "_create_cluster_ssh_keypair", _never_returns)
        mock_client = mock_agent_client_pool._mock_client
        mock_client.assign_port.side_effect = [22001, 22002]
        session_id = session_for_start_host_network.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_host_network], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_client.create_kernels.assert_not_awaited()
        assert sorted(c.args[0] for c in mock_client.release_port.await_args_list) == [
            22001,
            22002,
        ]


class TestSessionLauncherHostPortRelease:
    """Host ports a failed attempt took are given back before the session is placed again."""

    async def test_ports_released_when_start_fails_before_dispatch(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _boom() -> tuple[str, str]:
            raise RuntimeError("could not make the cluster ssh keypair")

        monkeypatch.setattr(launcher, "_create_cluster_ssh_keypair", _boom)
        mock_client = mock_agent_client_pool._mock_client
        mock_client.assign_port.side_effect = [22001, 22002]
        session_id = session_for_start_host_network.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_host_network], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.REPLACE
        assert sorted(c.args[0] for c in mock_client.release_port.await_args_list) == [
            22001,
            22002,
        ]

    async def test_ports_released_when_a_later_assignment_fails(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        mock_client = mock_agent_client_pool._mock_client
        mock_client.assign_port.side_effect = [22001, RuntimeError("port pool exhausted")]
        session_id = session_for_start_host_network.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_host_network], image_config_default
            )

        assert failed[session_id].disposition is FailureDisposition.REPLACE
        mock_client.release_port.assert_awaited_once_with(22001)

    async def test_ports_kept_when_the_session_started(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_host_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        session_id = session_for_start_host_network.session_id

        with RecorderContext.scope("test", entity_ids=[session_id]):
            failed = await launcher.start_sessions_for_handler(
                [session_for_start_host_network], image_config_default
            )

        assert failed == {}
        mock_agent_client_pool._mock_client.release_port.assert_not_awaited()


# =============================================================================
# TestSessionLauncherNetworkSetup (SC-LA-009 ~ SC-LA-015)
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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
        image_config_default: dict[UUID, ImageConfigData],
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

    async def test_persistent_network_uses_ref_name(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_for_start_persistent_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-014: Persistent network is addressed by its ref_name.

        Given: Session attached to a pre-created persistent network
        When: Start session
        Then: Kernels join the plugin-generated network under the network's driver
        """
        session_ids = [session_for_start_persistent_network.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_persistent_network],
                image_config_default,
            )

        mock_client = mock_agent_client_pool._mock_client
        cluster_info = mock_client.create_kernels.call_args[0][3]
        assert cluster_info["network_config"] == {
            "mode": "bridge",
            "network_name": "bai-multinode-00000000-0000-0000-0000-0000000000b2-nw",
        }

    async def test_persistent_network_id_not_overwritten(
        self,
        launcher: SessionLauncher,
        mock_repository: AsyncMock,
        session_for_start_persistent_network: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-015: Persistent network reference survives the start.

        Given: Session whose network_id points at a networks row
        When: Start session
        Then: The reference is left alone, so teardown can still resolve it
        """
        session_ids = [session_for_start_persistent_network.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_persistent_network],
                image_config_default,
            )

        mock_repository.update_session_network_id.assert_not_awaited()

    async def test_no_network_plugin_error(
        self,
        launcher: SessionLauncher,
        mock_network_plugin_ctx: MagicMock,
        mock_repository: AsyncMock,
        session_for_start_multi_node: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
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
