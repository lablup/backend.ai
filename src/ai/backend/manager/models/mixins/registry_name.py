"""Shared mixin for the per-type artifact registry rows (huggingface, reservoir).

The registry name lives on the artifact_registries row, not on the per-type row.
``registry_name`` is a query expression: a reader fills it with
``with_expression(Row.registry_name, ArtifactRegistryRow.name)`` or by assignment.
"""

from __future__ import annotations

from sqlalchemy.orm import Mapped, declared_attr, query_expression


class RegistryNameMixin:
    @declared_attr
    def registry_name(cls) -> Mapped[str | None]:
        return query_expression()
