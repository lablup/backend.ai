"""Tests for session, kernel GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import KernelId
from ai.backend.manager.api.gql.data_loader.kernel.loader import load_kernels_by_ids
from ai.backend.manager.data.kernel.types import KernelInfo


class TestLoadKernelsByIds:
    """Tests for load_kernels_by_ids function."""

    @staticmethod
    def create_mock_kernel(kernel_id: KernelId) -> MagicMock:
        return MagicMock(spec=KernelInfo, id=kernel_id)

    @staticmethod
    def create_mock_processor(kernels: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = kernels
        mock_processor.search_kernels.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_kernels_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_kernels.wait_for_complete.assert_not_called()

    async def test_returns_kernels_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = KernelId(uuid.uuid4()), KernelId(uuid.uuid4()), KernelId(uuid.uuid4())
        kernel1 = self.create_mock_kernel(id1)
        kernel2 = self.create_mock_kernel(id2)
        kernel3 = self.create_mock_kernel(id3)
        mock_processor = self.create_mock_processor(
            [kernel3, kernel1, kernel2]  # DB returns in different order
        )

        # When
        result = await load_kernels_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [kernel1, kernel2, kernel3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = KernelId(uuid.uuid4())
        missing_id = KernelId(uuid.uuid4())
        existing_kernel = self.create_mock_kernel(existing_id)
        mock_processor = self.create_mock_processor([existing_kernel])

        # When
        result = await load_kernels_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_kernel, None]
