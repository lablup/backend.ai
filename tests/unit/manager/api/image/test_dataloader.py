"""Tests for image GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.image.loader import load_images_by_ids
from ai.backend.manager.data.image.types import ImageDataWithDetails


class TestLoadImagesByIds:
    """Tests for load_images_by_ids function."""

    @staticmethod
    def create_mock_image(image_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=ImageDataWithDetails, id=image_id)

    @staticmethod
    def create_mock_processor(images: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = images
        mock_processor.search_images.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_images_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_images.wait_for_complete.assert_not_called()

    async def test_returns_images_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        image1 = self.create_mock_image(id1)
        image2 = self.create_mock_image(id2)
        image3 = self.create_mock_image(id3)
        mock_processor = self.create_mock_processor(
            [image3, image1, image2]  # DB returns in different order
        )

        # When
        result = await load_images_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [image1, image2, image3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_image = self.create_mock_image(existing_id)
        mock_processor = self.create_mock_processor([existing_image])

        # When
        result = await load_images_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_image, None]
