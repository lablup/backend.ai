from __future__ import annotations

import uuid
from collections import defaultdict
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
    image_ids: Sequence[uuid.UUID],
) -> list[list[str]]:
    """Batch load image alias strings grouped by image IDs.

    Args:
        processor: ImageProcessors instance.
        image_ids: List of image IDs to load aliases for.

    Returns:
        List of alias string lists in the same order as image_ids.
    """
    if not image_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[ImageAliasConditions.by_image_ids([ImageID(iid) for iid in image_ids])],
    )
    action = SearchAliasesAction(querier=querier)
    result = await processor.search_aliases.wait_for_complete(action)

    aliases_map: dict[uuid.UUID, list[str]] = defaultdict(list)
    for alias_data, image_id in zip(result.data, result.image_ids, strict=False):
        aliases_map[image_id].append(alias_data.alias)

    return [aliases_map.get(iid, []) for iid in image_ids]
