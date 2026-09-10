"""Declaring a row and writing it in the same breath.

The scenario table declares everything first and writes once at the end. A test that
seeds through fixtures cannot wait that long: a fixture has to answer with a row that
is already there, because the fixture beside it may need to read it.

Both go through the same `Seeder` and the same write path. This only moves when the
writing happens, and keeps it in one session so the test still sees one transaction.
"""

from __future__ import annotations

from typing import Any, cast

from ai.backend.common.data.entity.types import FieldData
from ai.backend.testutils.scenario_steps import Told
from bai_scenario.seeds.ops import SeedOps
from bai_scenario.seeds.seeder import (
    Laid,
    Seeder,
    SeedField,
    SeedLink,
    SeedNest,
    SeedRow,
    SeedRowFrom,
    SeedRowFromThree,
    SeedRowFromTwo,
    lay,
)


class SeedingSession:
    """One `Seeder` and one open write session, used together.

    Every entry point mirrors the seeder's own, writes what it declared, and answers the
    same handle. What was written is read back with `made`.
    """

    _seed: Seeder
    _ops: SeedOps
    _made: dict[Laid[Any], Any]

    def __init__(self, seed: Seeder, ops: SeedOps) -> None:
        self._seed = seed
        self._ops = ops
        self._made = {}

    def told(self) -> tuple[Told, ...]:
        """심은 행들을, 그것을 심은 묶음 아래로 쌓아서."""
        roots: list[str | Laid[Any]] = []
        under: dict[tuple[str, ...], list[Any]] = {(): roots}
        for row in self._seed.declared():
            chain: tuple[str, ...] = ()
            for one in row.nest:
                parent = under[chain]
                chain = chain + (one,)
                if chain not in under:
                    under[chain] = []
                    parent.append(chain)
            under[chain].append(row.states)

        def build(entries: list[Any]) -> tuple[Told, ...]:
            out: list[Told] = []
            for entry in entries:
                if isinstance(entry, tuple):
                    out.append(Told(entry[-1], within=build(under[entry])))
                else:
                    out.append(Told(entry))
            return tuple(out)

        return build(roots)

    def made[D](self, row: Laid[D]) -> D:
        """What the write answered for this row."""
        if row not in self._made:
            raise LookupError("this row was not laid by this session")
        return cast("D", self._made[row])

    async def _settle[D](self, row: Laid[D]) -> Laid[D]:
        await lay(self._ops, self._seed.declared(), self._made)
        return row

    async def creating[D](self, one: SeedRow[D], /) -> Laid[D]:
        return await self._settle(self._seed.creating(one))

    async def creating_from[A, D](self, one: SeedRowFrom[A, D], a: Laid[A], /) -> Laid[D]:
        return await self._settle(self._seed.creating_from(one, a))

    async def creating_from_two[A, B, D](
        self, one: SeedRowFromTwo[A, B, D], a: Laid[A], b: Laid[B], /
    ) -> Laid[D]:
        return await self._settle(self._seed.creating_from_two(one, a, b))

    async def creating_from_three[A, B, C, D](
        self, one: SeedRowFromThree[A, B, C, D], a: Laid[A], b: Laid[B], c: Laid[C], /
    ) -> Laid[D]:
        return await self._settle(self._seed.creating_from_three(one, a, b, c))

    async def once[D](self, one: SeedRow[D], /) -> Laid[D]:
        return await self._settle(self._seed.once(one))

    async def adding[A, D: FieldData](self, one: SeedField[A, D], owner: Laid[A], /) -> Laid[D]:
        return await self._settle(self._seed.adding(one, owner))

    async def linking[S, T](
        self, one: SeedLink[S, T], scope: Laid[S], target: Laid[T], /
    ) -> Laid[None]:
        return await self._settle(self._seed.linking(one, scope, target))

    async def granting[R, U](
        self,
        role: Laid[R],
        to: Laid[U],
        *,
        role_id: Any,
        user_id: Any,
    ) -> Laid[None]:
        return await self._settle(self._seed.granting(role, to, role_id=role_id, user_id=user_id))

    async def within[D](self, nest: SeedNest[D]) -> D:
        """Lay what this nest lays, and write all of it."""
        answered = self._seed.within(nest)
        await lay(self._ops, self._seed.declared(), self._made)
        return answered
