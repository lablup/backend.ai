"""The fixed rows every scenario of the searchable-field DB tests reads.

Four shelves in two zones: one whose two conditions sit on different boxes (S1), one
whose single box meets both (S2), one with no child and no related row (S3), and one
whose box has no spec (S4). Expected values are derived from :class:`Seeded` rather
than repeated per test.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .shelf_rows import (
    BoxRow,
    BoxState,
    CartID,
    CartLineRow,
    CartRow,
    CategoryRow,
    ShelfItemRow,
    ShelfKind,
    ShelfRow,
    SpecRow,
    ZoneID,
)

TIMES = [datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=offset) for offset in range(5)]


@dataclass(frozen=True)
class SeededShelf:
    """The values one shelf row was written with, to derive expectations from."""

    id: uuid.UUID
    zone_id: ZoneID
    name: str
    note: str | None
    count: int
    price: Decimal
    kind: ShelfKind
    active: bool
    tags: list[str]
    opened_at: datetime
    closed_at: datetime | None
    category_id: uuid.UUID | None

    def to_row(self) -> ShelfRow:
        return ShelfRow(
            id=self.id,
            name=self.name,
            note=self.note,
            count=self.count,
            price=self.price,
            kind=self.kind,
            active=self.active,
            tags=self.tags,
            opened_at=self.opened_at,
            closed_at=self.closed_at,
            zone_id=self.zone_id,
            category_id=self.category_id,
        )


@dataclass(frozen=True)
class Seeded:
    """Every seeded row, keyed by the name the scenarios call it."""

    zones: dict[str, ZoneID]
    categories: dict[str, uuid.UUID]
    category_ranks: dict[str, int]
    shelves: dict[str, SeededShelf]
    boxes: dict[str, uuid.UUID]
    specs: dict[str, uuid.UUID]
    items: dict[str, uuid.UUID]
    carts: dict[str, CartID]

    def shelf_ids(self, *keys: str) -> set[uuid.UUID]:
        return {self.shelves[key].id for key in keys}

    def shelf_id(self, key: str) -> uuid.UUID:
        return self.shelves[key].id

    def ordered_shelf_ids(self, *keys: str) -> list[uuid.UUID]:
        return [self.shelves[key].id for key in keys]


def _shelves(zones: dict[str, ZoneID], categories: dict[str, uuid.UUID]) -> dict[str, SeededShelf]:
    return {
        "S1": SeededShelf(
            id=uuid.uuid4(),
            zone_id=zones["Z1"],
            name="Alpha",
            note=None,
            count=1,
            price=Decimal("10.50"),
            kind=ShelfKind.BOOK,
            active=True,
            tags=["a", "b"],
            opened_at=TIMES[0],
            closed_at=None,
            category_id=categories["C1"],
        ),
        "S2": SeededShelf(
            id=uuid.uuid4(),
            zone_id=zones["Z1"],
            name="alpha beta",
            note="n",
            count=5,
            price=Decimal("9.75"),
            kind=ShelfKind.BOOK,
            active=False,
            tags=["b"],
            opened_at=TIMES[1],
            closed_at=TIMES[3],
            category_id=categories["C2"],
        ),
        "S3": SeededShelf(
            id=uuid.uuid4(),
            zone_id=zones["Z2"],
            name="Gamma",
            note=None,
            count=5,
            price=Decimal("20.00"),
            kind=ShelfKind.TOOL,
            active=True,
            tags=[],
            opened_at=TIMES[2],
            closed_at=TIMES[4],
            category_id=None,
        ),
        "S4": SeededShelf(
            id=uuid.uuid4(),
            zone_id=zones["Z2"],
            name="delta",
            note=None,
            count=9,
            price=Decimal("5.25"),
            kind=ShelfKind.TOY,
            active=False,
            tags=["a"],
            opened_at=TIMES[3],
            closed_at=None,
            category_id=None,
        ),
    }


async def seed_shelves(shelf_db: ExtendedAsyncSAEngine) -> Seeded:
    """Write every fixed row and answer with what was written."""
    zones = {"Z1": ZoneID(uuid.uuid4()), "Z2": ZoneID(uuid.uuid4())}
    categories = {"C1": uuid.uuid4(), "C2": uuid.uuid4()}
    category_ranks = {"C1": 2, "C2": 1}
    shelves = _shelves(zones, categories)
    specs = {"P1": uuid.uuid4(), "P2": uuid.uuid4(), "P3": uuid.uuid4()}
    boxes = {"B1": uuid.uuid4(), "B2": uuid.uuid4(), "B3": uuid.uuid4(), "B4": uuid.uuid4()}
    items = {"I0": uuid.uuid4(), "I1": uuid.uuid4(), "I2": uuid.uuid4()}
    carts = {"K1": CartID(uuid.uuid4()), "K2": CartID(uuid.uuid4()), "K3": CartID(uuid.uuid4())}

    async with shelf_db.begin_session() as sess:
        sess.add_all([
            CategoryRow(id=categories["C1"], title="Primary", rank=category_ranks["C1"]),
            CategoryRow(id=categories["C2"], title="Secondary", rank=category_ranks["C2"]),
        ])
        await sess.flush()
        sess.add_all([shelf.to_row() for shelf in shelves.values()])
        await sess.flush()
        sess.add_all([
            SpecRow(id=specs["P1"], shelf_id=shelves["S1"].id, grade="x", weight=3),
            SpecRow(id=specs["P2"], shelf_id=shelves["S1"].id, grade="y", weight=7),
            SpecRow(id=specs["P3"], shelf_id=shelves["S2"].id, grade="y", weight=5),
        ])
        await sess.flush()
        sess.add_all([
            BoxRow(
                id=boxes["B1"],
                shelf_id=shelves["S1"].id,
                label="b1",
                size=1,
                state=BoxState.OPEN,
                spec_id=specs["P1"],
            ),
            BoxRow(
                id=boxes["B2"],
                shelf_id=shelves["S1"].id,
                label="b2",
                size=9,
                state=BoxState.CLOSED,
                spec_id=specs["P2"],
            ),
            BoxRow(
                id=boxes["B3"],
                shelf_id=shelves["S2"].id,
                label="b3",
                size=9,
                state=BoxState.OPEN,
                spec_id=specs["P3"],
            ),
            BoxRow(
                id=boxes["B4"],
                shelf_id=shelves["S4"].id,
                label="b4",
                size=1,
                state=BoxState.OPEN,
                spec_id=None,
            ),
        ])
        await sess.flush()
        sess.add_all([
            ShelfItemRow(id=items["I0"], box_id=boxes["B1"], code="c0", qty=1),
            ShelfItemRow(id=items["I1"], box_id=boxes["B3"], code="c1", qty=1),
            ShelfItemRow(id=items["I2"], box_id=boxes["B3"], code="c2", qty=3),
        ])
        sess.add_all([
            CartRow(id=carts["K1"], zone_id=zones["Z1"]),
            CartRow(id=carts["K2"], zone_id=zones["Z2"]),
            CartRow(id=carts["K3"], zone_id=zones["Z1"]),
        ])
        await sess.flush()
        sess.add_all([
            CartLineRow(
                id=uuid.uuid4(), cart_id=carts["K1"], shelf_id=shelves["S1"].id, revoked=False
            ),
            CartLineRow(
                id=uuid.uuid4(), cart_id=carts["K1"], shelf_id=shelves["S2"].id, revoked=True
            ),
            CartLineRow(
                id=uuid.uuid4(), cart_id=carts["K2"], shelf_id=shelves["S2"].id, revoked=False
            ),
            CartLineRow(
                id=uuid.uuid4(), cart_id=carts["K2"], shelf_id=shelves["S4"].id, revoked=False
            ),
        ])

    return Seeded(
        zones=zones,
        categories=categories,
        category_ranks=category_ranks,
        shelves=shelves,
        boxes=boxes,
        specs=specs,
        items=items,
        carts=carts,
    )
