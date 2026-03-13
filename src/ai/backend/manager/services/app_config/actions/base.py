from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult


class AppConfigScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG


class AppConfigScopeActionResult(BaseScopeActionResult):
    pass
