"""PurgerSpec implementations for permission-related entities.

Deprecated: permission rows are removed through the v2 specs under
``models/rbac_models/permission/``. The remaining users move under BA-7204.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.repositories.base.purger import PurgerSpec


@dataclass
class PermissionPurgerSpec(PurgerSpec[PermissionRow]):
    """PurgerSpec for deleting a permission.

    Deprecated: use ``RolePermissionPurger`` in
    ``models/rbac_models/permission/purgers.py`` — BA-7204.
    """

    permission_id: uuid.UUID

    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.permission_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
