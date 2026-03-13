from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ImageAction


@dataclass
class LoadImageLastUsedAction(ImageAction):
    """Action to load last used timestamps for images."""

    image_ids: Sequence[ImageID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class LoadImageLastUsedActionResult(BaseActionResult):
    """Result of loading last used timestamps.

    last_used_map maps ImageID to the most recent session created_at timestamp.
    Images that have never been used will not appear in the map.
    """

    last_used_map: Mapping[ImageID, datetime]

    @override
    def entity_id(self) -> str | None:
        return None
