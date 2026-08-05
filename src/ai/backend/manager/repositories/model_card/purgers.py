from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class ModelCardPurgerSpec(PurgerSpec[ModelCardRow]):
    """PurgerSpec for deleting a model card."""

    card_id: uuid.UUID

    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.card_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
