"""Unit tests for Sokovan scheduler kernel handlers.

Based on BEP-1033 test scenarios for handler-level testing.

Test Scenarios:
- SC-SK-001 ~ SC-SK-010: SweepStaleKernelsKernelHandler
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import KernelId
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.sokovan.scheduler.handlers.kernel.sweep_stale_kernels import (
    SweepStaleKernelsKernelHandler,
)

# =============================================================================
# SweepStaleKernelsKernelHandler Tests (SC-SK-001 ~ SC-SK-010)
# =============================================================================


class TestSweepStaleKernelsKernelHandler:
    """Tests for SweepStaleKernelsKernelHandler.

    Verifies the handler correctly identifies stale kernels and categorizes
    them as failures (for TERMINATED transition) or successes (alive).
    """

    @pytest.fixture
    def handler(
        self,
        mock_terminator: AsyncMock,
    ) -> SweepStaleKernelsKernelHandler:
        """Create handler with mocked dependencies."""
        return SweepStaleKernelsKernelHandler(
            terminator=mock_terminator,
        )

    async def test_no_stale_kernels_returns_all_as_success(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernels_multiple: list[KernelInfo],
    ) -> None:
        """SC-SK-001: No stale kernels returns all as success.

        Given: Multiple RUNNING kernels
        When: Terminator reports no stale kernels
        Then: All kernels appear in result.successes
        """
        # Arrange - No dead kernels
        mock_terminator.check_stale_kernels.return_value = []

        # Act
        result = await handler.execute("default", running_kernels_multiple)

        # Assert
        assert len(result.successes) == len(running_kernels_multiple)
        assert len(result.failures) == 0

        # Verify terminator was called with kernel list
        mock_terminator.check_stale_kernels.assert_awaited_once_with(list(running_kernels_multiple))

    async def test_stale_kernel_detected_and_marked_as_failure(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernels_multiple: list[KernelInfo],
    ) -> None:
        """SC-SK-002: Stale kernel detected and returned as failure.

        Given: Multiple RUNNING kernels, one is stale
        When: Terminator identifies the stale kernel
        Then: Stale kernel in failures, others in successes
        """
        # Arrange - First kernel is dead/stale
        dead_kernel_id = KernelId(running_kernels_multiple[0].id)
        mock_terminator.check_stale_kernels.return_value = [dead_kernel_id]

        # Act
        result = await handler.execute("default", running_kernels_multiple)

        # Assert
        assert len(result.failures) == 1
        assert len(result.successes) == len(running_kernels_multiple) - 1
        assert result.failures[0].kernel_id == dead_kernel_id
        assert result.failures[0].reason == "STALE_KERNEL"

    async def test_multiple_stale_kernels_all_marked_as_failures(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernels_multiple: list[KernelInfo],
    ) -> None:
        """SC-SK-003: Multiple stale kernels all marked as failures.

        Given: Multiple RUNNING kernels, all are stale
        When: Terminator identifies all as stale
        Then: All kernels appear in failures
        """
        # Arrange - All kernels are dead/stale
        dead_kernel_ids = [KernelId(k.id) for k in running_kernels_multiple]
        mock_terminator.check_stale_kernels.return_value = dead_kernel_ids

        # Act
        result = await handler.execute("default", running_kernels_multiple)

        # Assert
        assert len(result.failures) == len(running_kernels_multiple)
        assert len(result.successes) == 0

        # Verify all failure reasons
        for failure in result.failures:
            assert failure.reason == "STALE_KERNEL"

    async def test_empty_kernel_list_returns_immediately(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
    ) -> None:
        """SC-SK-004: Empty kernel list returns empty result.

        Given: Empty kernel list
        When: Handler is invoked
        Then: Returns empty result without calling terminator
        """
        # Act
        result = await handler.execute("default", [])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 0

        # Verify terminator was not called
        mock_terminator.check_stale_kernels.assert_not_awaited()

    async def test_single_kernel_alive(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernel: KernelInfo,
    ) -> None:
        """SC-SK-005: Single alive kernel returns as success.

        Given: Single RUNNING kernel
        When: Terminator confirms kernel is alive
        Then: Kernel appears in successes
        """
        # Arrange - Kernel is alive
        mock_terminator.check_stale_kernels.return_value = []

        # Act
        result = await handler.execute("default", [running_kernel])

        # Assert
        assert len(result.successes) == 1
        assert len(result.failures) == 0
        assert result.successes[0].kernel_id == running_kernel.id

    async def test_single_kernel_stale(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernel: KernelInfo,
    ) -> None:
        """SC-SK-006: Single stale kernel returns as failure.

        Given: Single RUNNING kernel
        When: Terminator identifies kernel as stale
        Then: Kernel appears in failures with STALE_KERNEL reason
        """
        # Arrange - Kernel is dead/stale
        dead_kernel_id = KernelId(running_kernel.id)
        mock_terminator.check_stale_kernels.return_value = [dead_kernel_id]

        # Act
        result = await handler.execute("default", [running_kernel])

        # Assert
        assert len(result.failures) == 1
        assert len(result.successes) == 0
        assert result.failures[0].kernel_id == dead_kernel_id
        assert result.failures[0].reason == "STALE_KERNEL"
        assert result.failures[0].from_status == KernelStatus.RUNNING

    async def test_terminator_exception_propagates(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernel: KernelInfo,
    ) -> None:
        """SC-SK-007: Terminator exception propagates to coordinator.

        Given: Terminator raises an exception
        When: Handler is invoked
        Then: Exception propagates (coordinator handles it)
        """
        # Arrange
        mock_terminator.check_stale_kernels.side_effect = RuntimeError("Valkey connection failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Valkey connection failed"):
            await handler.execute("default", [running_kernel])

    async def test_mixed_results_correct_categorization(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernels_five: list[KernelInfo],
    ) -> None:
        """SC-SK-008: Mixed results - correct filtering of alive/dead kernels.

        Given: Five RUNNING kernels
        When: Two are identified as stale, three are alive
        Then: Two in failures, three in successes
        """
        # Arrange - First two are stale
        dead_kernel_ids = [
            KernelId(running_kernels_five[0].id),
            KernelId(running_kernels_five[1].id),
        ]
        mock_terminator.check_stale_kernels.return_value = dead_kernel_ids

        # Act
        result = await handler.execute("default", running_kernels_five)

        # Assert
        assert len(result.failures) == 2
        assert len(result.successes) == 3

        # Verify correct kernels are in failures
        failure_ids = {f.kernel_id for f in result.failures}
        assert KernelId(running_kernels_five[0].id) in failure_ids
        assert KernelId(running_kernels_five[1].id) in failure_ids

        # Verify correct kernels are in successes
        success_ids = {s.kernel_id for s in result.successes}
        assert running_kernels_five[2].id in success_ids
        assert running_kernels_five[3].id in success_ids
        assert running_kernels_five[4].id in success_ids

    async def test_success_has_no_reason(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernel: KernelInfo,
    ) -> None:
        """SC-SK-009: Success entries have no reason (kernel is alive).

        Given: Single RUNNING kernel that is alive
        When: Handler processes the kernel
        Then: Success entry has reason=None
        """
        # Arrange
        mock_terminator.check_stale_kernels.return_value = []

        # Act
        result = await handler.execute("default", [running_kernel])

        # Assert
        assert len(result.successes) == 1
        assert result.successes[0].reason is None

    async def test_from_status_preserved_in_result(
        self,
        handler: SweepStaleKernelsKernelHandler,
        mock_terminator: AsyncMock,
        running_kernels_multiple: list[KernelInfo],
    ) -> None:
        """SC-SK-010: from_status is preserved correctly in results.

        Given: RUNNING kernels
        When: Handler processes kernels
        Then: from_status is RUNNING in all results
        """
        # Arrange - Make first kernel stale
        dead_kernel_id = KernelId(running_kernels_multiple[0].id)
        mock_terminator.check_stale_kernels.return_value = [dead_kernel_id]

        # Act
        result = await handler.execute("default", running_kernels_multiple)

        # Assert - All entries should have from_status = RUNNING
        for failure in result.failures:
            assert failure.from_status == KernelStatus.RUNNING

        for success in result.successes:
            assert success.from_status == KernelStatus.RUNNING
