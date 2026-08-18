from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.purgers import AppConfigFragmentPurger
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


@dataclass
class PurgeAppConfigFragmentAction(
    PurgeEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Purge a fragment — not admin-only.

    No allow-list gate is needed: a fragment row exists only while its
    ``(config_name, scope_type)`` allow-list entry does, so an existing fragment is
    always removable at its own scope.
    """

    purger: AppConfigFragmentPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_fragment"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.purger.entity_id()

    @override
    def to_purger(self) -> AppConfigFragmentPurger:
        return self.purger
