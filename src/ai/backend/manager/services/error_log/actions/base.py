from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class ErrorLogGlobalAction(BaseGlobalAction):
    """Base for the error-log reads the service still owns."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE
