from __future__ import annotations

from decimal import Decimal
from typing import cast
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import LaunchPlan
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.containerd import KernelVerbNotSupported, ProfileSpecRejected
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import KernelCreationConfig, SlotName

from .conftest import FakeProfile

SLOTS = {SlotName("cpu"): Decimal(1), SlotName("mem"): Decimal(1024)}


def _make_context(
    ownership_data: KernelOwnershipData,
    kernel_config: KernelCreationConfig,
    profile: FakeProfile,
) -> ContainerdKernelCreationContext:
    return ContainerdKernelCreationContext(
        ownership_data,
        MagicMock(),
        MagicMock(),
        kernel_config,
        "ubuntu22.04",
        MagicMock(),
        {},
        profile=profile,
        slots=SLOTS,
    )


class TestPrepareContainer:
    async def test_plan_is_called_once_with_the_launch(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
    ) -> None:
        profile = FakeProfile("runc", accepts=True, plan_result=launch_plan)
        ctx = _make_context(ownership_data, kernel_config, profile)

        kernel = await ctx.prepare_container(MagicMock(), {}, [], MagicMock())

        assert isinstance(kernel, ContainerdKernel)
        assert kernel.launch_plan is launch_plan
        assert len(profile.plan_calls) == 1
        launch = profile.plan_calls[0]
        assert launch.kernel_id == ownership_data.kernel_id
        assert launch.session_id == ownership_data.session_id
        assert launch.config is kernel_config
        assert launch.slots is SLOTS

    async def test_profile_rejection_propagates(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        profile = FakeProfile("coco-tdx", accepts=True, plan_error=ProfileSpecRejected("bad"))
        ctx = _make_context(ownership_data, kernel_config, profile)

        with pytest.raises(ProfileSpecRejected):
            await ctx.prepare_container(MagicMock(), {}, [], MagicMock())


class TestCreationContextMembers:
    def test_unsupported_properties_raise(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(ownership_data, kernel_config, FakeProfile("runc", accepts=True))

        with pytest.raises(KernelVerbNotSupported, match="repl_ports"):
            _ = ctx.repl_ports
        with pytest.raises(KernelVerbNotSupported, match="protected_services"):
            _ = ctx.protected_services

    async def test_extra_envs_are_empty(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(ownership_data, kernel_config, FakeProfile("runc", accepts=True))

        assert await ctx.get_extra_envs() == {}

    async def test_resource_spec_requires_cpu(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        config = cast(KernelCreationConfig, {**kernel_config, "resource_slots": {"mem": "1"}})
        ctx = _make_context(ownership_data, config, FakeProfile("runc", accepts=True))

        with pytest.raises(UnsupportedResource):
            await ctx.prepare_resource_spec()
