"""Guarantee the purge in-use guard sees every vfolder reference in the schema.

``vfolders.id`` is referenced two ways: hard FK columns and soft JSONB
references (``VFolderMount`` / ``MountInfoEntry``) that embed a vfolder id but
are invisible to the DB and to schema metadata. The purge guard consults
:data:`VFOLDER_REFERENCE_CHECKS` for the soft references (and the SET NULL FK
``deployment_revisions.model``); this test fails the build when a new
referencing column is added without registering it, so the hand-maintained
registry cannot silently rot as the schema evolves.
"""

from __future__ import annotations

import importlib
import pkgutil

import ai.backend.manager.models
from ai.backend.common.types import MountInfoEntry, VFolderMount
from ai.backend.manager.models.base import (
    PydanticListColumn,
    StructuredJSONObjectListColumn,
    metadata,
)
from ai.backend.manager.repositories.vfolder.purge_guards import VFOLDER_REFERENCE_CHECKS

# Same discovery rule alembic's env.py uses to register every table on
# ``metadata`` (top-level modules + Row-bearing subpackages).
_SKIP_SUBPACKAGES = {"alembic", "hasher", "minilang", "rbac"}

# FK columns to vfolders.id handled outside the reference registry. Each entry
# needs an explicit justification so adding one is a deliberate decision.
_FK_HANDLED_ELSEWHERE = {
    # RESTRICT FK: the DB blocks row deletion and delete_vfolders_forever
    # surfaces it as VFolderHasLinkedModelCard (with the cascade_model_card opt).
    "model_cards.vfolder",
}


def _load_all_models() -> None:
    for module_info in pkgutil.iter_modules(ai.backend.manager.models.__path__):
        if module_info.ispkg and module_info.name in _SKIP_SUBPACKAGES:
            continue
        importlib.import_module(f"ai.backend.manager.models.{module_info.name}")


def _registered_sources() -> set[str]:
    return {check.source for check in VFOLDER_REFERENCE_CHECKS}


def test_registry_sources_are_unique() -> None:
    sources = [check.source for check in VFOLDER_REFERENCE_CHECKS]
    assert len(sources) == len(set(sources)), f"Duplicate reference sources: {sources}"


def test_all_soft_vfolder_reference_columns_are_registered() -> None:
    """Every JSONB column embedding a vfolder id must have a registry entry."""
    _load_all_models()
    registered = _registered_sources()

    soft_columns: set[str] = set()
    for table in metadata.tables.values():
        for column in table.columns:
            col_type = column.type
            if (
                isinstance(col_type, StructuredJSONObjectListColumn)
                and col_type._schema is VFolderMount
            ) or (isinstance(col_type, PydanticListColumn) and col_type._schema is MountInfoEntry):
                soft_columns.add(f"{table.name}.{column.name}")

    missing = soft_columns - registered
    assert not missing, (
        f"Unregistered vfolder soft-reference column(s): {sorted(missing)}. "
        "Add a VFolderReferenceCheck for each in repositories/vfolder/purge_guards.py "
        "so the purge in-use guard covers it."
    )


def test_all_fk_references_to_vfolders_are_accounted_for() -> None:
    """Every non-CASCADE FK to vfolders.id must be registered or handled."""
    _load_all_models()
    accounted = _registered_sources() | _FK_HANDLED_ELSEWHERE

    unaccounted: list[tuple[str, str | None]] = []
    for table in metadata.tables.values():
        for column in table.columns:
            for fk in column.foreign_keys:
                # ``target_fullname`` is the declared "<table>.<column>" string;
                # reading it does not resolve the FK (so unrelated unresolved
                # FKs elsewhere in the schema cannot break this check).
                if fk.target_fullname != "vfolders.id":
                    continue
                source = f"{table.name}.{column.name}"
                # CASCADE children are deleted together with the vfolder.
                if (fk.ondelete or "").upper() == "CASCADE":
                    continue
                if source not in accounted:
                    unaccounted.append((source, fk.ondelete))

    assert not unaccounted, (
        f"FK column(s) referencing vfolders.id not covered by the purge guard: {unaccounted}. "
        "Register a VFolderReferenceCheck in purge_guards.py, or add to _FK_HANDLED_ELSEWHERE "
        "with justification."
    )
