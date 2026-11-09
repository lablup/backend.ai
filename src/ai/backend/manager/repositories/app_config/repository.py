from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
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
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

__all__ = ("AppConfigRepository",)


class AppConfigRepository:
    """Purges that clear the rows the app config tables cascade to, each with its node."""

    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    async def purge_definition(self, purger: AppConfigDefinitionPurger) -> AppConfigDefinitionData:
        """Purge a config name with the allow-list entries and fragments under it."""
        async with self._ops.write_ops() as w:
            return await self._purge_definition(w, purger)

    async def partial_bulk_purge_definitions(
        self, purgers: Sequence[AppConfigDefinitionPurger]
    ) -> BulkResultWithFailures[AppConfigDefinitionData]:
        """Purge each named config name with what lies under it in its own savepoint."""
        successes: dict[EntityIdentifier, AppConfigDefinitionData] = {}
        errors: dict[EntityIdentifier, Exception] = {}
        if not purgers:
            return BulkResultWithFailures(successes=successes, errors=errors)
        async with self._ops.write_ops() as w:
            for purger in purgers:
                try:
                    async with w.savepoint() as sp:
                        successes[purger.definition_id] = await self._purge_definition(sp, purger)
                except Exception as e:
                    errors[purger.definition_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)

    async def purge_allow_list(self, purger: AppConfigAllowListPurger) -> AppConfigAllowListData:
        """Purge an allow-list entry with the fragments it admits."""
        async with self._ops.write_ops() as w:
            return await self._purge_allow_list(w, purger)

    async def partial_bulk_purge_allow_lists(
        self, purgers: Sequence[AppConfigAllowListPurger]
    ) -> BulkResultWithFailures[AppConfigAllowListData]:
        """Purge each named allow-list entry with its fragments in its own savepoint."""
        successes: dict[EntityIdentifier, AppConfigAllowListData] = {}
        errors: dict[EntityIdentifier, Exception] = {}
        if not purgers:
            return BulkResultWithFailures(successes=successes, errors=errors)
        async with self._ops.write_ops() as w:
            for purger in purgers:
                try:
                    async with w.savepoint() as sp:
                        successes[purger.allow_list_id] = await self._purge_allow_list(sp, purger)
                except Exception as e:
                    errors[purger.allow_list_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)

    async def _purge_definition(
        self, w: V2WriteOps, purger: AppConfigDefinitionPurger
    ) -> AppConfigDefinitionData:
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

    async def _purge_allow_list(
        self, w: V2WriteOps, purger: AppConfigAllowListPurger
    ) -> AppConfigAllowListData:
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
