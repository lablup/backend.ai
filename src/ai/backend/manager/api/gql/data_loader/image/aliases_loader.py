from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.types import ImageID
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.image.options import ImageAliasConditions
from ai.backend.manager.services.image.actions.search_aliases import SearchAliasesAction
from ai.backend.manager.services.image.processors import ImageProcessors


async def load_alias_by_ids(
    processor: ImageProcessors,
    alias_ids: Sequence[uuid.UUID],
) -> list[ImageAliasData | None]:
    """Batch load image aliases by their own alias IDs.

    NOTE: This loads aliases by ImageAliasRow.id (the alias's own UUID).
    For loading aliases by the image they belong to, use load_aliases_by_image_ids().

    Args:
        processor: ImageProcessors instance.
        alias_ids: List of alias IDs (ImageAliasRow.id) to load.

    Returns:
        List of ImageAliasData (or None if not found) in the same order as alias_ids.
    """
    if not alias_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[ImageAliasConditions.by_ids(alias_ids)],
    )
    action = SearchAliasesAction(querier=querier)
    result = await processor.search_aliases.wait_for_complete(action)

    alias_map: dict[uuid.UUID, ImageAliasData] = {alias.id: alias for alias in result.data}
    return [alias_map.get(alias_id) for alias_id in alias_ids]


async def load_aliases_by_image_ids(
    processor: ImageProcessors,
    image_ids: Sequence[ImageID],
) -> list[list[ImageAliasData]]:
    """Batch load image aliases by the image IDs they belong to.

    NOTE: This loads aliases by ImageAliasRow.image_id (the parent image's UUID).
    For loading a single alias by its own ID, use load_alias_by_ids().

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs (ImageRow.id) to load aliases for.

    Returns:
        List of ImageAliasData lists in the same order as image_ids.
        Each inner list contains all aliases belonging to that image.
    """
    if not image_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[ImageAliasConditions.by_image_ids(image_ids)],
    )
    action = SearchAliasesAction(querier=querier)
    result = await processor.search_aliases.wait_for_complete(action)

    # Group aliases by image_id
    aliases_map: dict[ImageID, list[ImageAliasData]] = {image_id: [] for image_id in image_ids}
    for alias_data, image_id in zip(result.data, result.image_ids, strict=True):
        if image_id in aliases_map:
            aliases_map[image_id].append(alias_data)

    return [aliases_map.get(image_id, []) for image_id in image_ids]
