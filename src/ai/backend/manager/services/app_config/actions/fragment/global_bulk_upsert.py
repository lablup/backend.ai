from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_FRAGMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import AtomicUpsertGlobalEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.upserters import (
    PublicAppConfigFragmentUpserter,
)


@dataclass
class GlobalBulkUpsertAppConfigFragmentsAction(
    AtomicUpsertGlobalEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Write the ``public`` fragments, all of them or none.

    A public value applies to everyone and belongs to no one, so no scope can answer for
    it — the SUPERADMIN gate does, which is what separates this from the owned write.
    """

    upserters: Sequence[PublicAppConfigFragmentUpserter]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_FRAGMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_bulk_upsert_app_config_fragments"

    @override
    def to_upserters(self) -> Sequence[PublicAppConfigFragmentUpserter]:
        return self.upserters
