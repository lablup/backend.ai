from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.purgers import AppConfigFragmentPurger
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


@dataclass
class BulkPurgeAppConfigFragmentAction(
    PartialBulkPurgeEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Purge many fragments, each answered for separately."""

    purgers: Sequence[AppConfigFragmentPurger]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_purge_app_config_fragments"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [purger.entity_id() for purger in self.purgers]

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, AppConfigFragmentPurger]:
        return {purger.entity_id(): purger for purger in self.purgers}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            purgers=[purger for purger in self.purgers if purger.entity_id() in allowed],
        )
