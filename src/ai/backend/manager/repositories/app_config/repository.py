from __future__ import annotations

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.app_config_allow_list.purgers import (
    AppConfigAllowListPurger,
    AppConfigAllowListsOfDefinitionPurger,
)
from ai.backend.manager.models.app_config_definition.purgers import AppConfigDefinitionPurger
from ai.backend.manager.models.app_config_fragment.purgers import (
    AppConfigFragmentsOfAllowListPurger,
    AppConfigFragmentsOfDefinitionPurger,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("AppConfigRepository",)


class AppConfigRepository:
    """Purges that clear the rows the app config tables cascade to, each with its node."""

    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    async def purge_definition(self, purger: AppConfigDefinitionPurger) -> AppConfigDefinitionData:
        """Purge a config name with the allow-list entries and fragments under it."""
        async with self._ops.write_ops() as w:
            await w.batch_purge_entities_in_global(
                AppConfigFragmentsOfDefinitionPurger(definition_id=purger.definition_id)
            )
            await w.batch_purge_entities_in_global(
                AppConfigAllowListsOfDefinitionPurger(definition_id=purger.definition_id)
            )
            data = await w.purge_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    entity_type=purger.definition_id.entity_type(),
                    operation=ActionOperationType.PURGE,
                    extra_msg=f"app config definition {purger.definition_id} not found",
                )
        return data

    async def purge_allow_list(self, purger: AppConfigAllowListPurger) -> AppConfigAllowListData:
        """Purge an allow-list entry with the fragments it admits."""
        async with self._ops.write_ops() as w:
            await w.batch_purge_entities_in_global(
                AppConfigFragmentsOfAllowListPurger(allow_list_id=purger.allow_list_id)
            )
            data = await w.purge_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    entity_type=purger.allow_list_id.entity_type(),
                    operation=ActionOperationType.PURGE,
                    extra_msg=f"app config allow list {purger.allow_list_id} not found",
                )
        return data
