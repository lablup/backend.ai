from __future__ import annotations

from typing import ClassVar

from sqlalchemy.orm import Mapped, declared_attr, synonym

from ai.backend.common.data.entity.types import ScopeType
from ai.backend.common.identifier.scope import ScopeID


class ScopeMixin:
    """Marks a Row as an RBAC scope source.

    Adds ``scope_id`` / ``scope_name`` synonyms for the columns named by
    ``__scope_id_column__`` / ``__scope_name_column__``, so scope rows are
    queried uniformly regardless of their own column names.
    """

    __scope_type__: ClassVar[ScopeType]
    __scope_id_column__: ClassVar[str] = "id"
    __scope_name_column__: ClassVar[str] = "name"

    @declared_attr
    def scope_id(cls) -> Mapped[ScopeID]:
        """Column whose value is used as ``ScopeRef.scope_id``."""
        return synonym(cls.__scope_id_column__)

    @declared_attr
    def scope_name(cls) -> Mapped[str]:
        """Column rendering the scope's display name."""
        return synonym(cls.__scope_name_column__)
