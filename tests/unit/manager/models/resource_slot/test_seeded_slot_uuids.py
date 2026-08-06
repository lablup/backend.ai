"""Every seeded slot type must carry a pinned uuid.

A fresh install takes these from the fixture and an upgraded deployment from
the migration that backfills the same values. A row added here without one
falls back to a generated default, so the same slot would end up with a
different identity depending on how the database was created — the one thing
the alternate key exists to prevent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import UUID

FIXTURE_PATH = Path("fixtures/manager/example-resource-slot-types.json")


def _rows() -> list[dict[str, Any]]:
    payload = json.loads(FIXTURE_PATH.read_text())
    return cast(list[dict[str, Any]], payload["resource_slot_types"])


class TestSeededSlotUUIDs:
    def test_every_row_pins_a_uuid(self) -> None:
        unpinned = [row["slot_name"] for row in _rows() if not row.get("uuid")]
        assert not unpinned, f"seeded slots without a pinned uuid: {unpinned}"

    def test_uuids_are_well_formed(self) -> None:
        for row in _rows():
            UUID(str(row["uuid"]))

    def test_uuids_are_distinct(self) -> None:
        uuids = [row["uuid"] for row in _rows()]
        assert len(set(uuids)) == len(uuids)

    def test_slot_names_are_distinct(self) -> None:
        names = [row["slot_name"] for row in _rows()]
        assert len(set(names)) == len(names)
