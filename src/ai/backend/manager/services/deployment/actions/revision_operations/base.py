"""Base action class for revision operations."""

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


class RevisionOperationBaseAction(BaseAction):
    """Base action for revision promotion and rollback operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_REVISION
