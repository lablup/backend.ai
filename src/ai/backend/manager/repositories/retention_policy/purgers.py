from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class RetentionPolicyPurgerSpec(PurgerSpec[RetentionPolicyRow]):
    """PurgerSpec for deleting a retention policy."""

    policy_id: uuid.UUID

    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
