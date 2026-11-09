"""Unit tests for Sokovan scheduler SessionLauncher.

Based on BEP-1033 test scenarios for launcher testing.

Test Scenarios:
- SC-LA-001 ~ SC-LA-004: Image Pulling
- SC-LA-005 ~ SC-LA-008: Kernel Creation
- SC-LA-009 ~ SC-LA-015: Network Setup
- SC-LA-016 ~ SC-LA-022: Sealed Kernel Creation (PRE_CREATE_KERNEL hook)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.plugin.hook import FIRST_COMPLETED, HookResult, HookResults
from ai.backend.common.types import AgentId, AutoPullBehavior, SessionId
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher
from ai.backend.manager.views.sokovan.image import ImageConfigData
from ai.backend.manager.views.sokovan.lifecycle import (
    KernelBindingData,
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

    async def test_system_session_environ_overrides_the_session_environ(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_name_bound_to_key_a: None,
        session_for_start_with_user_environ: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """A system session environ value wins over the session's own entry under its key.

        Given: The session's environ sets A and U; a public row binds the session name to A
        When: Start session
        Then: The kernel's environ has the session name under A and the session's U
        """
        session_ids = [session_for_start_with_user_environ.session_id]
        with RecorderContext.scope("test", entity_ids=session_ids):
            await launcher.start_sessions_for_handler(
                [session_for_start_with_user_environ],
                image_config_default,
            )

        kernel_configs = mock_agent_client_pool._mock_client.create_kernels.call_args[0][2]
        environ = kernel_configs[0]["environ"]
        assert environ["A"] == "test-session"
        assert environ["U"] == "mine"

    async def test_unbuildable_agent_does_not_block_other_agents(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        session_for_start_multi_kernel: SessionDataForStart,
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """A kernel config that cannot be built fails only its own agent.

        Given: Two agents, one kernel referencing an unknown image
        When: Session is started
        Then: create_kernels is awaited once (other agent), the bad agent is recorded
              as failed, and no session error info is written
        """
        # Arrange
        main, sub = session_for_start_multi_kernel.kernels
        session = replace(
            session_for_start_multi_kernel,
            kernels=[
                replace(main, agent_id=AgentId("agent-1")),
                replace(sub, agent_id=AgentId("agent-2"), image_id=uuid4()),
            ],
        )

        # Act
        with RecorderContext.scope("test", entity_ids=[session.session_id]):
            await launcher.start_sessions_for_handler([session], image_config_default)

        # Assert
        mock_agent_client_pool._mock_client.create_kernels.assert_awaited_once()
        mock_valkey_schedule.record_session_failed_agents.assert_awaited_once_with(
            session.session_id, [AgentId("agent-2")]
        )
        mock_repository.update_session_error_info.assert_not_awaited()


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


# =============================================================================
# TestSessionLauncherSealedKernel (SC-LA-016 ~ SC-LA-019)
# =============================================================================

_SEALED_SPEC: dict[str, Any] = {
    "schema_version": 1,
    "initdata": "initdata-b64",
    "sealed": "sealed-b64",
    "signature": "signature-b64",
}


@pytest.mark.usefixtures("patch_sealed_launch_slots")
class TestSessionLauncherSealedKernel:
    """Tests for the PRE_CREATE_KERNEL hook applied to sealed-launch kernels."""

    async def _start(
        self,
        launcher: SessionLauncher,
        session: SessionDataForStart,
        image_configs: dict[UUID, ImageConfigData],
    ) -> dict[SessionId, RejectedByHook]:
        with RecorderContext.scope("test", entity_ids=[session.session_id]):
            return await launcher.start_sessions_for_handler([session], image_configs)

    async def test_non_sealed_kernel_skips_hook(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_hook_plugin_ctx: MagicMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-016: A kernel without sealed slots is sent untouched, no hook dispatched."""
        session = session_with_kernels_factory(session_kernel_factory(sealed=False))

        rejected = await self._start(launcher, session, image_config_default)

        assert rejected == {}
        mock_hook_plugin_ctx.dispatch.assert_not_awaited()
        sent = mock_agent_client_pool._mock_client.create_kernels.call_args[0][2][0]
        assert "confidential" not in sent
        assert sent["environ"]["USER_SECRET"] == session.environ["USER_SECRET"]

    async def test_sealed_kernel_dispatches_hook_and_sends_stripped_config(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_hook_plugin_ctx: MagicMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-017: A sealed kernel goes through the hook; secrets stay out of the config."""
        mock_hook_plugin_ctx.dispatch.return_value = HookResult(
            status=HookResults.PASSED, src_plugin="confidential", result=dict(_SEALED_SPEC)
        )
        session = session_with_kernels_factory(session_kernel_factory())

        await self._start(launcher, session, image_config_default)

        call = mock_hook_plugin_ctx.dispatch.await_args
        assert call.args[0] == "PRE_CREATE_KERNEL"
        assert call.kwargs == {"return_when": FIRST_COMPLETED, "success_if_no_hook": False}
        config, cluster_info, payload, extra = call.args[1]
        assert all(key.startswith("BACKENDAI_") for key in config["environ"])
        assert config["internal_data"]["ssh_keypair"]["private_key"] == ""
        assert cluster_info["ssh_keypair"]["private_key"] == ""
        assert payload == {"schema_version": 1, "environ": session.environ}
        assert extra == {"domain_id": str(session.domain_id)}
        send_args = mock_agent_client_pool._mock_client.create_kernels.call_args[0]
        assert send_args[2][0] is config
        assert config["confidential"] == _SEALED_SPEC

    async def test_no_hook_rejects_sealed_kernel(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_repository: AsyncMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-018: With no hook handling the event, nothing is sent (fail closed)."""
        session = session_with_kernels_factory(session_kernel_factory())

        rejected = await self._start(launcher, session, image_config_default)

        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()
        mock_repository.update_session_error_info.assert_awaited()
        assert isinstance(rejected[session.session_id], RejectedByHook)

    @pytest.mark.parametrize(
        "malformed",
        [
            None,
            {"schema_version": 1, "initdata": "a", "sealed": "b"},
            {**_SEALED_SPEC, "signature": 3},
        ],
    )
    async def test_malformed_result_rejected(
        self,
        malformed: Mapping[str, Any] | None,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_hook_plugin_ctx: MagicMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-019: A malformed hook result rejects the session and sends nothing."""
        mock_hook_plugin_ctx.dispatch.return_value = HookResult(
            status=HookResults.PASSED, src_plugin="confidential", result=malformed
        )
        session = session_with_kernels_factory(session_kernel_factory())

        rejected = await self._start(launcher, session, image_config_default)

        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()
        assert isinstance(rejected[session.session_id], RejectedByHook)

    async def test_rejection_on_one_agent_sends_nothing_to_other_agents(
        self,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-020: A rejected sealed kernel on one agent stops the plain agents too."""
        session = session_with_kernels_factory(
            session_kernel_factory(agent_id=AgentId("agent-1"), sealed=False),
            session_kernel_factory(agent_id=AgentId("agent-2"), sealed=True),
        )

        rejected = await self._start(launcher, session, image_config_default)

        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()
        assert isinstance(rejected[session.session_id], RejectedByHook)

    async def test_hook_timeout_rejects_like_a_rejection(
        self,
        monkeypatch: pytest.MonkeyPatch,
        launcher: SessionLauncher,
        mock_agent_client_pool: MagicMock,
        mock_hook_plugin_ctx: MagicMock,
        mock_repository: AsyncMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-021: A hook that does not answer in time rejects the session."""
        monkeypatch.setattr(
            "ai.backend.manager.sokovan.scheduler.launcher.launcher"
            "._PRE_CREATE_KERNEL_HOOK_TIMEOUT_SEC",
            0.01,
        )

        async def _hang(*args: Any, **kwargs: Any) -> HookResult:
            await asyncio.sleep(10)
            raise AssertionError("unreachable")

        mock_hook_plugin_ctx.dispatch.side_effect = _hang
        session = session_with_kernels_factory(session_kernel_factory())

        rejected = await self._start(launcher, session, image_config_default)

        mock_agent_client_pool._mock_client.create_kernels.assert_not_awaited()
        mock_repository.update_session_error_info.assert_awaited()
        assert isinstance(rejected[session.session_id], RejectedByHook)

    async def test_hook_error_reason_is_not_shown_to_the_user(
        self,
        launcher: SessionLauncher,
        mock_hook_plugin_ctx: MagicMock,
        session_with_kernels_factory: Callable[..., SessionDataForStart],
        session_kernel_factory: Callable[..., KernelBindingData],
        image_config_default: dict[UUID, ImageConfigData],
    ) -> None:
        """SC-LA-022: The reason of a failing hook stays in the log, not in the failure message."""
        mock_hook_plugin_ctx.dispatch.return_value = HookResult(
            status=HookResults.ERROR,
            src_plugin="confidential",
            reason="ValueError('USER_SECRET=hunter2')",
        )
        session = session_with_kernels_factory(session_kernel_factory())

        rejected = await self._start(launcher, session, image_config_default)

        message = rejected[session.session_id].extra_msg
        assert message is not None
        assert "hunter2" not in message
