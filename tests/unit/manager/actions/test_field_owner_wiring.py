"""The owner a field group is wired under vs the owner its field type declares.

A field group hangs under the entity group that owns its rows, and the field type
declares that owner itself. The two are written in different places, so a field
classified under the wrong entity shows up here as a disagreement.

Kept apart from ``test_registry_catalog`` because reading the production wiring
imports every service package, which would widen the import closure that module's
defined-vs-wired sweep measures.
"""

from __future__ import annotations

import asyncio

from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.services.catalog import load_wiring_catalog


def test_field_wiring_owner_matches_the_declared_owner_type() -> None:
    catalog = asyncio.run(load_wiring_catalog())
    mismatched: list[str] = []
    checked = 0
    for wiring in catalog:
        if wiring.field_type is None:
            continue
        checked += 1
        declared = wiring.field_type.owner_type()
        wired = wiring.entity_type
        if declared is None:
            if not isinstance(wired, GlobalEntityType):
                mismatched.append(
                    f"{wiring.field_type} declares no owner but is wired under {wired}"
                )
        elif type(wired) is not declared:
            mismatched.append(
                f"{wiring.field_type} declares owner {declared.name()} but is wired under {wired}"
            )
    assert checked, "no field operation was wired; the sweep would pass vacuously"
    assert not mismatched, "\n".join(sorted(set(mismatched)))
