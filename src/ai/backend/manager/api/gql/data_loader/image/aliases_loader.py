from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.types import ImageID
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.image.options import ImageAliasConditions
from ai.backend.manager.services.image.actions.get_aliases_by_image_ids import (
    GetAliasesByImageIdsAction,
)
from ai.backend.manager.services.image.actions.search_aliases import SearchAliasesAction
from ai.backend.manager.services.image.processors import ImageProcessors


async def load_alias_by_ids(
    processor: ImageProcessors,
    alias_ids: Sequence[uuid.UUID],
) -> list[ImageAliasData | None]:
    """Batch load image aliases by their own alias IDs.
    NOTE: This loads aliases by ImageAliasRow.id (the alias's own UUID).

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
) -> list[list[str]]:
    """Batch load image aliases grouped by image IDs.

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs to load aliases for.

    Returns:
        List of alias string lists in the same order as image_ids.
    """
    if not image_ids:
        return []

    action_result = await processor.get_aliases_by_image_ids.wait_for_complete(
        GetAliasesByImageIdsAction(image_ids=list(image_ids))
    )
    return [action_result.aliases_map.get(image_id, []) for image_id in image_ids]
