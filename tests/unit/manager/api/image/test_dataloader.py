"""Tests for image GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.data_loader.image.aliases_loader import (
    load_aliases_by_image_ids,
)
from ai.backend.manager.api.gql.data_loader.image.loader import load_images_by_ids
from ai.backend.manager.data.image.types import ImageAliasData, ImageDataWithDetails


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
    def create_mock_processor(data: list[ImageAliasData], image_ids: list[ImageID]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = data
        mock_action_result.image_ids = image_ids
        mock_processor.search_aliases.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    @staticmethod
    def create_alias_data(alias: str) -> ImageAliasData:
        return ImageAliasData(id=uuid.uuid4(), alias=alias)

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
        alias1 = self.create_alias_data("alias1")
        alias1_alt = self.create_alias_data("alias1-alt")
        alias2 = self.create_alias_data("alias2")
        alias3 = self.create_alias_data("alias3")
        alias3_alt = self.create_alias_data("alias3-alt")
        alias3_v2 = self.create_alias_data("alias3-v2")
        # Simulate search_aliases returning data and image_ids in parallel lists
        data = [alias1, alias1_alt, alias2, alias3, alias3_alt, alias3_v2]
        image_ids = [id1, id1, id2, id3, id3, id3]
        mock_processor = self.create_mock_processor(data, image_ids)

        # When
        result = await load_aliases_by_image_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [
            [alias1, alias1_alt],
            [alias2],
            [alias3, alias3_alt, alias3_v2],
        ]

    async def test_returns_empty_list_for_missing_ids(self) -> None:
        # Given
        existing_id = ImageID(uuid.uuid4())
        missing_id = ImageID(uuid.uuid4())
        alias = self.create_alias_data("existing-alias")
        # Only existing_id has an alias in the result
        data = [alias]
        image_ids = [existing_id]
        mock_processor = self.create_mock_processor(data, image_ids)

        # When
        result = await load_aliases_by_image_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [[alias], []]

    async def test_returns_empty_list_for_image_without_aliases(self) -> None:
        # Given
        id_with_aliases = ImageID(uuid.uuid4())
        id_without_aliases = ImageID(uuid.uuid4())
        alias = self.create_alias_data("some-alias")
        # Only id_with_aliases has an alias; id_without_aliases has none
        data = [alias]
        image_ids = [id_with_aliases]
        mock_processor = self.create_mock_processor(data, image_ids)

        # When
        result = await load_aliases_by_image_ids(
            mock_processor, [id_with_aliases, id_without_aliases]
        )

        # Then
        assert result == [[alias], []]
