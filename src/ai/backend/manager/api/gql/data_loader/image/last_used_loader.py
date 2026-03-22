from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from ai.backend.common.types import ImageID
from ai.backend.manager.services.image.actions.load_image_last_used import (
    LoadImageLastUsedAction,
)
from ai.backend.manager.services.image.processors import ImageProcessors


async def load_image_last_used_by_ids(
    processor: ImageProcessors,
    image_ids: Sequence[ImageID],
) -> list[datetime | None]:
    """Batch load last used timestamps for images by their IDs.

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs to load last used timestamps for.

    Returns:
        List of datetime (or None if never used) in the same order as image_ids.
    """
    if not image_ids:
        return []

    action_result = await processor.load_image_last_used.wait_for_complete(
        LoadImageLastUsedAction(image_ids=image_ids)
    )

    return [action_result.last_used_map.get(image_id) for image_id in image_ids]
