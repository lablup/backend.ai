from __future__ import annotations

from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.containerd import agent as agent_module
from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.client import TaskInfo, TaskState
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import (
    LaunchPlan,
    RuntimeProfile,
    describe_profile_failure,
)
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.errors.agent import ContainerCreationFailedError
from ai.backend.agent.errors.containerd import KernelTaskExited
from ai.backend.agent.types import KernelOwnershipData

from .conftest import FakeProfile
from .fakes import FakeContainerd

CREATE_ERROR = "failed to create shim task: sandbox is blocked"


class _DescribingProfile(FakeProfile):
    calls: list[tuple[int | None, str]]
    _reason: str | None

    def __init__(self, reason: str | None) -> None:
        super().__init__("describing", accepts=True)
        self._reason = reason
        self.calls = []

    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        self.calls.append((exit_status, error_text))
        return self._reason


class _RaisingProfile(FakeProfile):
    def __init__(self) -> None:
        super().__init__("raising", accepts=True)

    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        raise RuntimeError("buggy profile")


class _TwoMethodProfile:
    name = "two-method"

    def accepts(self, slots: Any) -> bool:
        return True

    def plan(self, kernel: Any) -> Any:
        raise AssertionError("must not run")


def _kernel(
    ownership_data: KernelOwnershipData,
    launch_plan: LaunchPlan,
    fake: FakeContainerd,
    profile: RuntimeProfile,
) -> ContainerdKernel:
    return ContainerdKernel(
        ownership_data,
        "net-1",
        MagicMock(),
        1,
        agent_config={},
        resource_spec=MagicMock(),
        service_ports=[],
        environ={},
        data={"container_id": "c1"},
        launch_plan=launch_plan,
        profile=profile,
        client=fake,
    )


def _stopped_task(fake: FakeContainerd) -> None:
    fake.tasks["c1"] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=3)


class TestDescribeProfileFailure:
    def test_runc_describes_nothing(self) -> None:
        assert describe_profile_failure(RuncProfile(1.0), 3, "boom") is None

    def test_profile_text_is_returned(self) -> None:
        profile = _DescribingProfile("refused")

        assert describe_profile_failure(profile, 3, "boom") == "refused"
        assert profile.calls == [(3, "boom")]

    def test_two_method_profile_describes_nothing(self) -> None:
        assert (
            describe_profile_failure(cast(RuntimeProfile, _TwoMethodProfile()), 3, "boom") is None
        )

    def test_raising_profile_describes_nothing(self) -> None:
        assert describe_profile_failure(_RaisingProfile(), 3, "boom") is None


class TestKernelTaskExitedReason:
    async def test_raising_profile_keeps_the_message(
        self, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
    ) -> None:
        kernel = _kernel(ownership_data, launch_plan, fake, _RaisingProfile())
        _stopped_task(fake)

        with pytest.raises(KernelTaskExited) as exc_info:
            await kernel._raise_if_task_exited()

        assert exc_info.value.extra_msg == "the kernel task exited with status 3 (container c1)"
        assert exc_info.value.exit_status == 3

    async def test_profile_text_is_in_the_exception(
        self, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
    ) -> None:
        profile = _DescribingProfile("SomeReason: the runtime refused")
        kernel = _kernel(ownership_data, launch_plan, fake, profile)
        _stopped_task(fake)

        with pytest.raises(KernelTaskExited) as exc_info:
            await kernel._raise_if_task_exited()

        assert "status 3 (container c1): SomeReason: the runtime refused" in str(exc_info.value)
        assert exc_info.value.exit_status == 3
        assert profile.calls[0][0] == 3

    async def test_none_keeps_the_message(
        self, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
    ) -> None:
        kernel = _kernel(ownership_data, launch_plan, fake, _DescribingProfile(None))
        _stopped_task(fake)

        with pytest.raises(KernelTaskExited) as exc_info:
            await kernel._raise_if_task_exited()

        assert exc_info.value.extra_msg == "the kernel task exited with status 3 (container c1)"

    async def test_runc_keeps_the_message(
        self, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
    ) -> None:
        kernel = _kernel(ownership_data, launch_plan, fake, RuncProfile(1.0))
        _stopped_task(fake)

        with pytest.raises(KernelTaskExited) as exc_info:
            await kernel._raise_if_task_exited()

        assert exc_info.value.extra_msg == "the kernel task exited with status 3 (container c1)"

    async def test_missing_task_passes_no_exit_status(
        self, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
    ) -> None:
        profile = _DescribingProfile("gone-reason")
        kernel = _kernel(ownership_data, launch_plan, fake, profile)

        with pytest.raises(KernelTaskExited) as exc_info:
            await kernel._raise_if_task_exited()

        assert "gone-reason" in str(exc_info.value)
        assert profile.calls[0][0] is None


class TestContainerCreationFailedReason:
    @pytest.fixture
    def context(
        self,
        mocker: MockerFixture,
        ownership_data: KernelOwnershipData,
        launch_plan: LaunchPlan,
        fake: FakeContainerd,
    ) -> ContainerdKernelCreationContext:
        context = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
        context.kernel_id = ownership_data.kernel_id
        context._client = cast(Any, fake)
        context._address = MagicMock()
        context._network = MagicMock(teardown=AsyncMock(), publish=AsyncMock())
        context._port_pool = MagicMock()
        context._generated_mounts = []
        context._base_spec = {}
        context._resource_lock = MagicMock()
        mocker.patch.object(context, "_free_allocations", AsyncMock())
        mocker.patch.object(
            agent_module, "resolve_image", AsyncMock(side_effect=ValueError(CREATE_ERROR))
        )
        return context

    async def _start(
        self, context: ContainerdKernelCreationContext, kernel: ContainerdKernel
    ) -> None:
        await context.start_container(kernel, [], None, [], MagicMock())

    async def test_profile_text_is_in_the_exception(
        self,
        context: ContainerdKernelCreationContext,
        ownership_data: KernelOwnershipData,
        launch_plan: LaunchPlan,
        fake: FakeContainerd,
    ) -> None:
        profile = _DescribingProfile("SomeReason: the runtime refused")
        context._profile = profile
        kernel = _kernel(ownership_data, launch_plan, fake, profile)

        with pytest.raises(ContainerCreationFailedError) as exc_info:
            await self._start(context, kernel)

        assert CREATE_ERROR in str(exc_info.value)
        assert str(exc_info.value).endswith("SomeReason: the runtime refused)")
        assert profile.calls == [(None, CREATE_ERROR)]

    @pytest.mark.parametrize(
        "profile", [_DescribingProfile(None), RuncProfile(1.0), _RaisingProfile()]
    )
    async def test_no_text_keeps_the_original_error(
        self,
        context: ContainerdKernelCreationContext,
        ownership_data: KernelOwnershipData,
        launch_plan: LaunchPlan,
        fake: FakeContainerd,
        profile: RuntimeProfile,
    ) -> None:
        context._profile = profile
        kernel = _kernel(ownership_data, launch_plan, fake, profile)

        with pytest.raises(ValueError, match="sandbox is blocked"):
            await self._start(context, kernel)
