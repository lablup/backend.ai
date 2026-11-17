"""The base of an entity's query declaration and of its four sections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from ai.backend.manager.models.specs.search.field import QueryColumn


class QueryOwnSection:
    """The entity's own columns, each a ``QueryColumn``."""

    def columns(self) -> Mapping[str, QueryColumn[Any, Any, Any]]:
        """Declared columns by ``name``, in declaration order (base classes first)."""
        declared: dict[str, QueryColumn[Any, Any, Any]] = {}
        for klass in reversed(type(self).__mro__):
            for value in vars(klass).values():
                if isinstance(value, QueryColumn):
                    declared[value.name] = value
        return declared


class QueryNestedSection:
    """Rows of other tables the entity owns, each a ``NestedQueryColumn``."""


class QueryLinkedSection:
    """Connections to other entities: ``membership`` and ``usage`` conditions."""


class QueryAggregateSection:
    """Group and aggregate value items wrapping a ``QueryColumn`` of ``own``."""


class QuerySpec:
    """``{Entity}QuerySpec`` sets ``own`` and, when it has them, the other sections."""

    own: ClassVar[QueryOwnSection]
    nested: ClassVar[type[QueryNestedSection]] = QueryNestedSection
    linked: ClassVar[type[QueryLinkedSection]] = QueryLinkedSection
    aggregate: ClassVar[type[QueryAggregateSection]] = QueryAggregateSection
