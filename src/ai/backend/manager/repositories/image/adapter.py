from __future__ import annotations

from typing import Any, override

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, EntityType, ScopeType
from ai.backend.common.docker import LabelName
from ai.backend.manager.repositories.base.rbac.adapter import CreatorAdapter
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.image.creators import ImageRowCreatorSpec


class ImageCreatorAdapter(CreatorAdapter[ImageRowCreatorSpec]):
    """Adapter for resolving RBAC scope from Image labels.

    Determines scope based on the CUSTOMIZED_OWNER label:
    - If label exists: USER scope with extracted user ID
    - Otherwise: GLOBAL scope
    """

    @override
    def build(self, spec: ImageRowCreatorSpec) -> RBACEntityCreator:
        labels: dict[str, Any] = spec.labels or {}
        owner_label = labels.get(LabelName.CUSTOMIZED_OWNER)

        if owner_label is not None:
            _, _, scope_id = owner_label.partition(":")
            scope_type = ScopeType.USER
        else:
            scope_id = GLOBAL_SCOPE_ID
            scope_type = ScopeType.GLOBAL
        return RBACEntityCreator(
            spec=spec,
            scope_type=scope_type,
            scope_id=scope_id,
            entity_type=EntityType.IMAGE,
        )
