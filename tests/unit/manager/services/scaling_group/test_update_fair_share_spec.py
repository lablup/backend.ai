"""
Tests for UpdateFairShareSpecAction in ScalingGroupService.

Tests resource weight validation and capacity-based filtering.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentSelectionStrategy, ResourceSlot, SessionTypes
from ai.backend.manager.data.scaling_group.types import (
    ResourceInfo,
    ScalingGroupData,
    ScalingGroupDriverConfig,
    ScalingGroupMetadata,
    ScalingGroupNetworkConfig,
    ScalingGroupSchedulerConfig,
    ScalingGroupSchedulerOptions,
    ScalingGroupStatus,
    SchedulerType,
)
from ai.backend.manager.errors.fair_share import InvalidResourceWeightError
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService

# =============================================================================
# Common Fixtures
# =============================================================================


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ScalingGroupRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ScalingGroupService:
    return ScalingGroupService(repository=mock_repository)


def _create_scaling_group(
    resource_weights: ResourceSlot | None = None,
    half_life_days: int = 7,
) -> ScalingGroupData:
    scheduler_options = ScalingGroupSchedulerOptions(
        allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
        pending_timeout=timedelta(seconds=0),
        config={},
        agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
        agent_selector_config={},
        enforce_spreading_endpoint_replica=False,
        allow_fractional_resource_fragmentation=False,
        route_cleanup_target_statuses=[],
    )
    return ScalingGroupData(
        name="default",
        status=ScalingGroupStatus(is_active=True, is_public=True),
        metadata=ScalingGroupMetadata(description="Test", created_at=datetime.now(tz=UTC)),
        network=ScalingGroupNetworkConfig(
            wsproxy_addr="", wsproxy_api_token="", use_host_network=False
        ),
        driver=ScalingGroupDriverConfig(name="static", options={}),
        scheduler=ScalingGroupSchedulerConfig(name=SchedulerType.FIFO, options=scheduler_options),
        fair_share_spec=FairShareScalingGroupSpec(
            half_life_days=half_life_days,
            lookback_days=28,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=resource_weights or ResourceSlot(),
        ),
    )


def _create_capacity(resources: dict[str, Decimal]) -> ResourceInfo:
    slot = ResourceSlot(resources)
    return ResourceInfo(capacity=slot, used=ResourceSlot(), free=slot)


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidation:
    """V1-V5: Input validation for resource_weights."""

    # --- V1: Valid resource type ---

    @pytest.fixture
    def existing_scaling_group_with_cpu(self) -> ScalingGroupData:
        return _create_scaling_group(ResourceSlot({"cpu": Decimal("1.0")}))

    @pytest.fixture
    def capacity_cpu_mem_cuda(self) -> ResourceInfo:
        return _create_capacity({
            "cpu": Decimal("16"),
            "mem": Decimal("68719476736"),
            "cuda.device": Decimal("4"),
        })

    @pytest.fixture
    def action_add_mem_weight(self) -> UpdateFairShareSpecAction:
        """V1: Add mem which exists in capacity."""
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("mem", Decimal("0.5"))],
        )

    @pytest.fixture
    def expected_weights_cpu_mem(self) -> ResourceSlot:
        """Expected: cpu preserved, mem added."""
        return ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")})

    async def test_v1_valid_resource_type_succeeds(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_with_cpu: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_add_mem_weight: UpdateFairShareSpecAction,
        expected_weights_cpu_mem: ResourceSlot,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )

        result = await service.update_fair_share_spec(action_add_mem_weight)

        # Verify repository called with correct spec
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == expected_weights_cpu_mem["cpu"]
        assert saved_spec.resource_weights["mem"] == expected_weights_cpu_mem["mem"]

        # Verify result returned
        assert result is not None
        assert result.scaling_group is not None

    # --- V2: Invalid resource type ---

    @pytest.fixture
    def action_add_tpu_weight(self) -> UpdateFairShareSpecAction:
        """V2: Add tpu.device which does NOT exist in capacity."""
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("tpu.device", Decimal("1.0"))],
        )

    async def test_v2_invalid_resource_type_raises_error(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_with_cpu: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_add_tpu_weight: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)

        with pytest.raises(InvalidResourceWeightError) as exc:
            await service.update_fair_share_spec(action_add_tpu_weight)

        assert "tpu.device" in str(exc.value)
        mock_repository.update_scaling_group.assert_not_called()

    # --- V3: Partial invalid types ---

    @pytest.fixture
    def action_mixed_valid_invalid(self) -> UpdateFairShareSpecAction:
        """V3: Mix of valid (cpu) and invalid (tpu, rocm) types."""
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[
                ResourceWeightInput("cpu", Decimal("2.0")),
                ResourceWeightInput("tpu.device", Decimal("1.0")),
                ResourceWeightInput("rocm.device", Decimal("1.0")),
            ],
        )

    async def test_v3_partial_invalid_lists_all_invalid_types(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_with_cpu: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_mixed_valid_invalid: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)

        with pytest.raises(InvalidResourceWeightError) as exc:
            await service.update_fair_share_spec(action_mixed_valid_invalid)

        error_msg = str(exc.value)
        assert "tpu.device" in error_msg
        assert "rocm.device" in error_msg
        mock_repository.update_scaling_group.assert_not_called()

    # --- V4: Delete existing type (weight=None) ---

    @pytest.fixture
    def action_delete_cuda(self) -> UpdateFairShareSpecAction:
        """V4: Delete cuda.device (weight=None) - no validation needed for deletion."""
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("cuda.device", None)],
        )

    async def test_v4_delete_resource_type_succeeds(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_with_cpu: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_delete_cuda: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )

        result = await service.update_fair_share_spec(action_delete_cuda)

        assert result is not None
        mock_repository.update_scaling_group.assert_called_once()

    # --- V5: Delete non-existent type ---

    @pytest.fixture
    def action_delete_nonexistent_tpu(self) -> UpdateFairShareSpecAction:
        """V5: Delete tpu.device that doesn't exist anywhere (no-op, no validation)."""
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("tpu.device", None)],
        )

    async def test_v5_delete_nonexistent_type_succeeds(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_with_cpu: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_delete_nonexistent_tpu: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_with_cpu
        )

        result = await service.update_fair_share_spec(action_delete_nonexistent_tpu)

        assert result is not None
        mock_repository.update_scaling_group.assert_called_once()


# =============================================================================
# Filtering Tests
# =============================================================================


class TestFiltering:
    """F1-F3: Capacity-based filtering of existing resource_weights."""

    # --- F1: Filter out type not in capacity ---

    @pytest.fixture
    def existing_scaling_group_cpu_cuda(self) -> ScalingGroupData:
        """Existing weights: cpu, cuda.device."""
        return _create_scaling_group(
            ResourceSlot({
                "cpu": Decimal("1.0"),
                "cuda.device": Decimal("10.0"),
            })
        )

    @pytest.fixture
    def capacity_cpu_mem_only(self) -> ResourceInfo:
        """Capacity only has cpu, mem (cuda agent removed)."""
        return _create_capacity({"cpu": Decimal("16"), "mem": Decimal("68719476736")})

    @pytest.fixture
    def action_update_half_life(self) -> UpdateFairShareSpecAction:
        """Update half_life_days only (triggers filtering)."""
        return UpdateFairShareSpecAction(resource_group="default", half_life_days=14)

    async def test_f1_filters_types_not_in_capacity(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_cuda: ScalingGroupData,
        capacity_cpu_mem_only: ResourceInfo,
        action_update_half_life: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_only)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )

        result = await service.update_fair_share_spec(action_update_half_life)

        # Verify repository called with filtered weights
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert "cpu" in saved_spec.resource_weights
        assert "cuda.device" not in saved_spec.resource_weights  # filtered out

        assert result is not None

    # --- F2: Keep all types when in capacity ---

    @pytest.fixture
    def existing_scaling_group_cpu_mem(self) -> ScalingGroupData:
        """Existing weights: cpu, mem."""
        return _create_scaling_group(
            ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("0.5"),
            })
        )

    @pytest.fixture
    def capacity_cpu_mem_cuda(self) -> ResourceInfo:
        """Capacity has cpu, mem, cuda.device."""
        return _create_capacity({
            "cpu": Decimal("16"),
            "mem": Decimal("68719476736"),
            "cuda.device": Decimal("4"),
        })

    async def test_f2_keeps_all_types_in_capacity(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_mem: ScalingGroupData,
        capacity_cpu_mem_cuda: ResourceInfo,
        action_update_half_life: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu_mem_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )

        result = await service.update_fair_share_spec(action_update_half_life)

        # Verify all weights preserved
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("1.0")
        assert saved_spec.resource_weights["mem"] == Decimal("0.5")

        assert result is not None

    # --- F3: Empty capacity clears all weights ---

    @pytest.fixture
    def empty_capacity(self) -> ResourceInfo:
        """No agents - empty capacity."""
        return _create_capacity({})

    async def test_f3_clears_weights_when_capacity_empty(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_mem: ScalingGroupData,
        empty_capacity: ResourceInfo,
        action_update_half_life: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )
        mock_repository.get_resource_info = AsyncMock(return_value=empty_capacity)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )

        result = await service.update_fair_share_spec(action_update_half_life)

        # Verify all weights cleared
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert len(saved_spec.resource_weights) == 0

        assert result is not None


# =============================================================================
# Merge Tests
# =============================================================================


class TestMerge:
    """M1-M4: Merging partial updates with existing spec."""

    @pytest.fixture
    def existing_scaling_group_cpu_only(self) -> ScalingGroupData:
        return _create_scaling_group(ResourceSlot({"cpu": Decimal("1.0")}))

    @pytest.fixture
    def existing_scaling_group_cpu_mem(self) -> ScalingGroupData:
        return _create_scaling_group(
            ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("0.5"),
            })
        )

    @pytest.fixture
    def full_capacity(self) -> ResourceInfo:
        return _create_capacity({
            "cpu": Decimal("16"),
            "mem": Decimal("68719476736"),
            "cuda.device": Decimal("4"),
        })

    # --- M1: Add new type ---

    @pytest.fixture
    def action_add_mem(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("mem", Decimal("0.5"))],
        )

    async def test_m1_adds_new_resource_type(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_only: ScalingGroupData,
        full_capacity: ResourceInfo,
        action_add_mem: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )
        mock_repository.get_resource_info = AsyncMock(return_value=full_capacity)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )

        result = await service.update_fair_share_spec(action_add_mem)

        # Verify merged weights
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("1.0")  # preserved
        assert saved_spec.resource_weights["mem"] == Decimal("0.5")  # added

        assert result is not None

    # --- M2: Update existing type ---

    @pytest.fixture
    def action_update_cpu(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("cpu", Decimal("2.0"))],
        )

    async def test_m2_updates_existing_type(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_only: ScalingGroupData,
        full_capacity: ResourceInfo,
        action_update_cpu: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )
        mock_repository.get_resource_info = AsyncMock(return_value=full_capacity)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )

        result = await service.update_fair_share_spec(action_update_cpu)

        # Verify updated weight
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("2.0")  # updated

        assert result is not None

    # --- M3: Delete existing type ---

    @pytest.fixture
    def action_delete_cpu(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[ResourceWeightInput("cpu", None)],
        )

    async def test_m3_deletes_existing_type(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_mem: ScalingGroupData,
        full_capacity: ResourceInfo,
        action_delete_cpu: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )
        mock_repository.get_resource_info = AsyncMock(return_value=full_capacity)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_mem
        )

        result = await service.update_fair_share_spec(action_delete_cpu)

        # Verify cpu deleted, mem preserved
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert "cpu" not in saved_spec.resource_weights  # deleted
        assert saved_spec.resource_weights["mem"] == Decimal("0.5")  # preserved

        assert result is not None

    # --- M4: None input preserves existing ---

    @pytest.fixture
    def action_update_half_life_only(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            half_life_days=14,
            resource_weights=None,
        )

    async def test_m4_preserves_weights_when_input_none(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_only: ScalingGroupData,
        full_capacity: ResourceInfo,
        action_update_half_life_only: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )
        mock_repository.get_resource_info = AsyncMock(return_value=full_capacity)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_only
        )

        result = await service.update_fair_share_spec(action_update_half_life_only)

        # Verify weights preserved, half_life updated
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("1.0")  # preserved
        assert saved_spec.half_life_days == 14  # updated

        assert result is not None


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """I1-I2: Full validation + merge + filtering flow."""

    # --- I1: Full flow ---

    @pytest.fixture
    def existing_scaling_group_cpu_cuda(self) -> ScalingGroupData:
        """Has cuda weight that will be filtered."""
        return _create_scaling_group(
            ResourceSlot({
                "cpu": Decimal("1.0"),
                "cuda.device": Decimal("10.0"),
            })
        )

    @pytest.fixture
    def capacity_without_cuda(self) -> ResourceInfo:
        """Cuda agent removed."""
        return _create_capacity({"cpu": Decimal("16"), "mem": Decimal("68719476736")})

    @pytest.fixture
    def action_update_cpu_add_mem(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[
                ResourceWeightInput("cpu", Decimal("2.0")),
                ResourceWeightInput("mem", Decimal("0.5")),
            ],
        )

    async def test_i1_full_flow_validate_merge_filter(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_cuda: ScalingGroupData,
        capacity_without_cuda: ResourceInfo,
        action_update_cpu_add_mem: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_without_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )

        result = await service.update_fair_share_spec(action_update_cpu_add_mem)

        # Verify full flow: validate -> merge -> filter
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("2.0")  # updated
        assert saved_spec.resource_weights["mem"] == Decimal("0.5")  # added
        assert "cuda.device" not in saved_spec.resource_weights  # filtered out

        assert result is not None

    # --- I2: Agent removal auto-cleanup ---

    @pytest.fixture
    def action_half_life_only(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(resource_group="default", half_life_days=14)

    async def test_i2_agent_removal_cleans_weights(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu_cuda: ScalingGroupData,
        capacity_without_cuda: ResourceInfo,
        action_half_life_only: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_without_cuda)
        mock_repository.update_scaling_group = AsyncMock(
            return_value=existing_scaling_group_cpu_cuda
        )

        result = await service.update_fair_share_spec(action_half_life_only)

        # Verify cuda cleaned up during unrelated update
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.half_life_days == 14
        assert "cuda.device" not in saved_spec.resource_weights  # auto-cleaned
        assert saved_spec.resource_weights["cpu"] == Decimal("1.0")  # preserved

        assert result is not None


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """E1-E2: Edge cases."""

    # --- E1: Non-existent resource group ---

    @pytest.fixture
    def action_nonexistent_group(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(resource_group="nonexistent", half_life_days=14)

    async def test_e1_nonexistent_group_raises_error(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        action_nonexistent_group: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            side_effect=ScalingGroupNotFound("nonexistent")
        )

        with pytest.raises(ScalingGroupNotFound):
            await service.update_fair_share_spec(action_nonexistent_group)

        mock_repository.update_scaling_group.assert_not_called()

    # --- E2: Empty list preserves existing ---

    @pytest.fixture
    def existing_scaling_group_cpu(self) -> ScalingGroupData:
        return _create_scaling_group(ResourceSlot({"cpu": Decimal("1.0")}))

    @pytest.fixture
    def capacity_cpu(self) -> ResourceInfo:
        return _create_capacity({"cpu": Decimal("16")})

    @pytest.fixture
    def action_empty_weights_list(self) -> UpdateFairShareSpecAction:
        return UpdateFairShareSpecAction(
            resource_group="default",
            resource_weights=[],
            half_life_days=14,
        )

    async def test_e2_empty_list_preserves_weights(
        self,
        service: ScalingGroupService,
        mock_repository: MagicMock,
        existing_scaling_group_cpu: ScalingGroupData,
        capacity_cpu: ResourceInfo,
        action_empty_weights_list: UpdateFairShareSpecAction,
    ) -> None:
        mock_repository.get_scaling_group_by_name = AsyncMock(
            return_value=existing_scaling_group_cpu
        )
        mock_repository.get_resource_info = AsyncMock(return_value=capacity_cpu)
        mock_repository.update_scaling_group = AsyncMock(return_value=existing_scaling_group_cpu)

        result = await service.update_fair_share_spec(action_empty_weights_list)

        # Verify weights preserved with empty list input
        call_args = mock_repository.update_scaling_group.call_args
        saved_spec: FairShareScalingGroupSpec = call_args[0][
            0
        ].spec.fair_share.fair_share_spec.value()
        assert saved_spec.resource_weights["cpu"] == Decimal("1.0")  # preserved

        assert result is not None
