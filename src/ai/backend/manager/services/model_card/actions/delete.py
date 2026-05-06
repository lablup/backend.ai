from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class DeleteModelCardAction(ModelCardAction):
    purger: Purger[ModelCardRow]
    vfolder_trash_spec: UpdaterSpec[VFolderRow] | None = None
    """Spec used to soft-delete the linked VFolder in the same transaction.

    When set, the repository fills the deleted card's VFolder PK in and applies
    the spec right after the model card row is removed; ``None`` keeps the
    linked VFolder untouched.
    """

    @override
    def entity_id(self) -> str | None:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteModelCardActionResult(BaseActionResult):
    id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)
