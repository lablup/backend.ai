from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.image.types import ImageDataWithDetails
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.image.options import ImageConditions
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction
from ai.backend.manager.services.image.processors import ImageProcessors


async def load_images_by_ids(
    processor: ImageProcessors,
    image_ids: Sequence[uuid.UUID],
) -> list[Optional[ImageDataWithDetails]]:
    """Batch load images by their IDs.

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs to load.

    Returns:
        List of ImageDataWithDetails (or None if not found) in the same order as image_ids.
    """
    if not image_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(image_ids)),
        conditions=[ImageConditions.by_ids(image_ids)],
    )

    action_result = await processor.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    image_map: dict[uuid.UUID, ImageDataWithDetails] = {
        uuid.UUID(str(image.id)): image for image in action_result.data
    }
    return [image_map.get(image_id) for image_id in image_ids]
