from __future__ import annotations

import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.plugin.hook import HookResult, HookResults
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    SessionTypes,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.manager.types import UserScope


class TestResourceGroupResolver:
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def scheduling_controller(self, mock_repository: AsyncMock) -> SchedulingController:
        hook_result = HookResult(status=HookResults.PASSED)
        hook_plugin_ctx = AsyncMock()
        hook_plugin_ctx.dispatch = AsyncMock(return_value=hook_result)
        args = SchedulingControllerArgs(
            repository=mock_repository,
            config_provider=MagicMock(),
            storage_manager=AsyncMock(),
            event_producer=AsyncMock(),
            valkey_schedule=AsyncMock(),
            network_plugin_ctx=AsyncMock(),
            hook_plugin_ctx=hook_plugin_ctx,
        )
        return SchedulingController(args)

    @pytest.fixture
    def spec_with_inaccessible_scaling_group(self) -> SessionCreationSpec:
        return SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test-session",
            access_key=AccessKey("TESTKEY"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            priority=10,
            resource_policy={"max_containers_per_session": 5},
            kernel_specs=[
                cast(
                    KernelEnqueueingConfig,
                    {
                        "image_ref": MagicMock(canonical="python:3.9"),
                        "resources": {"cpu": "1", "mem": "1g"},
                    },
                )
            ],
            creation_spec={"mounts": [], "environ": {}},
            scaling_group="nonexistent-sg",
        )

    async def test_inaccessible_scaling_group_returns_none_instead_of_raising(
        self,
        scheduling_controller: SchedulingController,
        mock_repository: AsyncMock,
        spec_with_inaccessible_scaling_group: SessionCreationSpec,
    ) -> None:
        """Regression: inaccessible scaling group should return None with warning, not raise."""
        mock_repository.query_allowed_scaling_groups = AsyncMock(
            return_value=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                ),
                AllowedScalingGroup(
                    name="gpu", is_private=False, scheduler_opts=ScalingGroupOpts()
                ),
            ]
        )
        spec = spec_with_inaccessible_scaling_group

        result = await scheduling_controller._resolve_scaling_group(spec)

        assert result is None
        mock_repository.query_allowed_scaling_groups.assert_awaited_once()
