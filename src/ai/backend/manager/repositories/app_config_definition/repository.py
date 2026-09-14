from __future__ import annotations

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.app_config_definition.purgers import (
    AppConfigDefinitionPurger,
    DefinitionAllowListPurger,
    DefinitionFragmentPurger,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("AppConfigDefinitionRepository",)


class AppConfigDefinitionRepository:
    """The purge that clears the rows the database cascades to. Everything keyed on one
    spec goes through ``OpsRepository``."""

    _ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._ops = v2_ops_provider

    async def purge(self, definition_id: AppConfigDefinitionID) -> AppConfigDefinitionData:
        """Delete the definition with its allow-list entries and their fragments, each
        with the RBAC graph it left.

        The dependents go first: the database would cascade their rows with the
        definition, but nothing would tear down what they left in the graph.
        """
        async with self._ops.write_ops() as w:
            await w.batch_purge_entities_in_global(
                DefinitionFragmentPurger(definition_id=definition_id)
            )
            await w.batch_purge_entities_in_global(
                DefinitionAllowListPurger(definition_id=definition_id)
            )
            data = await w.purge_entity(AppConfigDefinitionPurger(definition_id=definition_id))
            if data is None:
                raise EntityNotFoundError(
                    entity_type=definition_id.entity_type(),
                    operation=ActionOperationType.PURGE,
                    extra_msg=f"AppConfigDefinitionRow {definition_id} not found",
                )
            return data
