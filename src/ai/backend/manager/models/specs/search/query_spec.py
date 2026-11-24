"""The base of an entity's query declaration and of its four sections."""

from __future__ import annotations

from typing import ClassVar


class QueryOwnSection:
    """The entity's own columns, each a ``QueryColumn``."""


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
