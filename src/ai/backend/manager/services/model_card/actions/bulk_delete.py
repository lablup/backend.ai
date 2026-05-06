from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import BulkModelCardDeleteResultData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class BulkDeleteModelCardAction(ModelCardAction):
    purgers: list[Purger[ModelCardRow]]
    vfolder_trash_spec: UpdaterSpec[VFolderRow] | None = None
    """Spec used to soft-delete each card's linked VFolder in the same transaction.

    Each purger runs in its own transaction (partial-failure semantics), so the
    spec is applied per-card via :class:`Updater` rather than a single bulk
    ``UPDATE``. ``None`` keeps the linked VFolders untouched.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class BulkDeleteModelCardActionResult(BaseActionResult):
    data: BulkModelCardDeleteResultData

    @override
    def entity_id(self) -> str | None:
        for card_id in self.data.successes:
            return str(card_id)
        return None
