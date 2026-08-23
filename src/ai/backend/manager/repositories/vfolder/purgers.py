from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurgerSpec,
)


@dataclass
class VFolderPurgerSpec(RBACEntityPurgerSpec[VFolderRow]):
    vfolder_id: UUID

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def pk_value(self) -> UUID:
        return self.vfolder_id

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.VFOLDER

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=self.element_type(),
            element_id=str(self.vfolder_id),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
