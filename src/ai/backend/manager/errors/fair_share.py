"""
Fair share domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class InvalidResourceWeightError(EntityError, web.HTTPBadRequest):
    """Raised when resource_weights contains resource types not available in capacity."""

    error_type = "https://api.backend.ai/probs/invalid-resource-weight"
    error_title = "Invalid resource weight configuration."

    invalid_types: list[str]

    def __init__(self, invalid_types: list[str]) -> None:
        self.invalid_types = invalid_types
        super().__init__(f"Resource types not available in capacity: {', '.join(invalid_types)}")

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(),
            ActionOperationType.UPDATE,
            ErrorDetail.INVALID_PARAMETERS,
        )
