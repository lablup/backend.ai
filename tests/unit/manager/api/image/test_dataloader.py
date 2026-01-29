"""Tests for image GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.data_loader.image.aliases_loader import (
    load_aliases_by_image_ids,
)
from ai.backend.manager.api.gql.data_loader.image.loader import load_images_by_ids
from ai.backend.manager.data.image.types import ImageData


class TestLoadImagesByIds:
    """Tests for load_images_by_ids function."""

    @staticmethod
    def create_mock_image(image_id: ImageID) -> MagicMock:
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
        id1, id2, id3 = ImageID(uuid.uuid4()), ImageID(uuid.uuid4()), ImageID(uuid.uuid4())
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
        existing_id = ImageID(uuid.uuid4())
        missing_id = ImageID(uuid.uuid4())
        existing_image = self.create_mock_image(existing_id)
        mock_processor = self.create_mock_processor([existing_image])

        # When
        result = await load_images_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_image, None]


class TestLoadAliasesByImageIds:
    """Tests for load_aliases_by_image_ids function."""

    @staticmethod
    def create_mock_processor(aliases_map: dict[ImageID, list[str]]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.aliases_map = aliases_map
        mock_processor.get_aliases_by_image_ids.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_aliases_by_image_ids(mock_processor, [])

        # Then
        assert result == []

    async def test_returns_aliases_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = ImageID(uuid.uuid4()), ImageID(uuid.uuid4()), ImageID(uuid.uuid4())
        aliases_map = {
            id1: ["alias1", "alias1-alt"],
            id2: ["alias2"],
            id3: ["alias3", "alias3-alt", "alias3-v2"],
        }
        mock_processor = self.create_mock_processor(aliases_map)

        # When
        result = await load_aliases_by_image_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [
            ["alias1", "alias1-alt"],
            ["alias2"],
            ["alias3", "alias3-alt", "alias3-v2"],
        ]

    async def test_returns_empty_list_for_missing_ids(self) -> None:
        # Given
        existing_id = ImageID(uuid.uuid4())
        missing_id = ImageID(uuid.uuid4())
        aliases_map = {
            existing_id: ["existing-alias"],
        }
        mock_processor = self.create_mock_processor(aliases_map)

        # When
        result = await load_aliases_by_image_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [["existing-alias"], []]

    async def test_returns_empty_list_for_image_without_aliases(self) -> None:
        # Given
        id_with_aliases = ImageID(uuid.uuid4())
        id_without_aliases = ImageID(uuid.uuid4())
        aliases_map: dict[ImageID, list[str]] = {
            id_with_aliases: ["some-alias"],
            id_without_aliases: [],
        }
        mock_processor = self.create_mock_processor(aliases_map)

        # When
        result = await load_aliases_by_image_ids(
            mock_processor, [id_with_aliases, id_without_aliases]
        )

        # Then
        assert result == [["some-alias"], []]
