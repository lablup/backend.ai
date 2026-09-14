from __future__ import annotations

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.app_config_allow_list.purgers import (
    AllowListFragmentPurger,
    AppConfigAllowListPurger,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("AppConfigAllowListRepository",)


class AppConfigAllowListRepository:
    """The purge that clears the rows the database cascades to. Everything keyed on one
    spec goes through ``OpsRepository``."""

    _ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._ops = v2_ops_provider

    async def purge(self, allow_list_id: AppConfigAllowListID) -> AppConfigAllowListData:
        """Delete the entry with the fragments under it, each with the RBAC graph it left.

        The fragments go first: the database would cascade their rows with the entry,
        but nothing would tear down what they left in the graph.
        """
        async with self._ops.write_ops() as w:
            await w.batch_purge_entities_in_global(
                AllowListFragmentPurger(allow_list_id=allow_list_id)
            )
            data = await w.purge_entity(AppConfigAllowListPurger(allow_list_id=allow_list_id))
            if data is None:
                raise EntityNotFoundError(
                    entity_type=allow_list_id.entity_type(),
                    operation=ActionOperationType.PURGE,
                    extra_msg=f"AppConfigAllowListRow {allow_list_id} not found",
                )
            return data
