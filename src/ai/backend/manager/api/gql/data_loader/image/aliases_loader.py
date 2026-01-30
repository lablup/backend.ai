from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.types import ImageID
from ai.backend.manager.services.image.actions.get_aliases_by_image_ids import (
    GetAliasesByImageIdsAction,
)
from ai.backend.manager.services.image.processors import ImageProcessors


async def load_aliases_by_image_ids(
    processor: ImageProcessors,
    image_ids: Sequence[ImageID],
) -> list[list[str]]:
    """Batch load image aliases by image IDs.

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs to load aliases for.

    Returns:
        List of alias lists in the same order as image_ids.
    """
    if not image_ids:
        return []

    action = GetAliasesByImageIdsAction(image_ids=list(image_ids))
    result = await processor.get_aliases_by_image_ids.wait_for_complete(action)

    return [result.aliases_map.get(image_id, []) for image_id in image_ids]
