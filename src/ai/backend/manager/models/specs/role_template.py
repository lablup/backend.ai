"""Role-preset declaration of the v2 lineage.

Only entities that allow role presets carry this interface; every other entity
spec stays entirely unaware of role provisioning.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.models.base import Base


class RoleTemplateSource[TRow: Base](ABC):
    """Declares that role presets apply to this entity's scope, and what the
    preset's ``role_name_template`` may reference.

    Combined with the entity write specs by inheritance
    (:class:`~.creator.RoleManagedEntityCreator`), so the ops path that
    provisions roles is typed against the combination — no runtime capability
    check exists anywhere.
    """

    @abstractmethod
    def template_value(self, row: TRow) -> ScopeTemplateValue:
        """The values exposed to role name templates as ``{{ scope.* }}``,
        read off the settled row — no lookup is involved."""
        raise NotImplementedError
