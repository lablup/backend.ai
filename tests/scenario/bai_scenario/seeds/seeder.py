"""Laying the rows a scenario needs, through the manager's own write specs.

A scenario never writes a row itself. It names a write spec and what that spec reads
from earlier rows; the seeder picks the ops path the spec's own type calls for, makes
the name, and runs every step in one session.

Which ops path writes a row follows from the spec's type, so no scenario names a path:

    RoleManagedGlobalEntityCreator  -> create_role_managed_global_entity
    RoleManagedEntityCreator        -> create_role_managed_entity
    GuardedEntityCreator            -> create_entity   (EntityCreator is one of these)
    GlobalEntityCreator             -> create_global_entity
    GuardedDataUpdater              -> update_data
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, overload

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.specs.creator import (
    FieldCreator,
    GlobalEntityCreator,
    GuardedEntityCreator,
    RoleManagedEntityCreator,
    RoleManagedGlobalEntityCreator,
)
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.testutils.typed_scenario import (
    ActorBound,
    Answer,
    Deferred,
    Invocation,
    Override,
    Situation,
    situation,
)

type WriteSpec[D] = (
    GlobalEntityCreator[Any, D]
    | GuardedEntityCreator[Any, D]
    | RoleManagedGlobalEntityCreator[Any, D]
    | RoleManagedEntityCreator[Any, D]
    | GuardedDataUpdater[Any, D]
)


@dataclass(frozen=True)
class Spec[D]:
    """A write spec that needs nothing but its own name."""

    hint: str
    build: Callable[[str], WriteSpec[D]]


@dataclass(frozen=True)
class SpecFrom[A, D]:
    """A write spec that reads one row laid before it."""

    hint: str
    build: Callable[[str, A], WriteSpec[D]]


@dataclass(frozen=True)
class SpecFromTwo[A, B, D]:
    """A write spec that reads two rows laid before it."""

    hint: str
    build: Callable[[str, A, B], WriteSpec[D]]


@dataclass(frozen=True)
class SpecFromThree[A, B, C, D]:
    """A write spec that reads three rows laid before it."""

    hint: str
    build: Callable[[str, A, B, C], WriteSpec[D]]


@dataclass(frozen=True)
class FieldOf[A, D: FieldData]:
    """A field row written under an owner the scenario already laid.

    A field grants nothing of its own and dies with its owner, so it is never laid on
    its own: the owner comes with it.
    """

    hint: str
    owner_id: Callable[[A], Any]
    spec: FieldCreator[Any, Any, D]


@dataclass(frozen=True, eq=False)
class Given[D]:
    """One row a scenario lays down, and a handle on what the write answered.

    Compared by identity, so a call that reads this row holds the handle rather than
    repeating a value the row also carries.
    """

    describe: str
    sources: tuple[Given[Any], ...]
    write: Callable[[V2WriteOps, Sequence[Any]], Awaitable[D]]


async def _write(ops: V2WriteOps, spec: WriteSpec[Any]) -> Any:
    """Run one spec down the ops path its own type calls for."""
    if isinstance(spec, RoleManagedGlobalEntityCreator):
        return await ops.create_role_managed_global_entity(spec)
    if isinstance(spec, RoleManagedEntityCreator):
        return await ops.create_role_managed_entity(spec)
    if isinstance(spec, GuardedEntityCreator):
        return await ops.create_entity(spec)
    if isinstance(spec, GlobalEntityCreator):
        return await ops.create_global_entity(spec)
    return await ops.update_data(spec)


@dataclass
class Seeder:
    """The rows one scenario lays, and the names it gives them.

    A scenario builder is handed a fresh one, so the numbering restarts at every row of
    the table and a name says which row of this scenario made it.
    """

    _counts: dict[str, int] = field(default_factory=dict)
    _laid: list[Given[Any]] = field(default_factory=list)

    def situation[C](
        self,
        *,
        config: Sequence[Override[C, Any]] = (),
        answers: Sequence[Answer[Any]] = (),
    ) -> Situation[C]:
        """Every row this scenario asked for, in the order it asked.

        The scenario does not list its rows again: what it made is what it lays.
        """
        return situation(rows=tuple(self._laid), config=config, answers=answers)

    def _remember[D](self, row: Given[D]) -> Given[D]:
        self._laid.append(row)
        return row

    def name(self, hint: str) -> str:
        """``hint-1``, ``hint-2``, ... within this scenario."""
        self._counts[hint] = self._counts.get(hint, 0) + 1
        return f"{hint}-{self._counts[hint]}"

    @overload
    def creating[D](self, spec: Spec[D], /) -> Given[D]: ...

    @overload
    def creating[A, D](self, spec: SpecFrom[A, D], a: Given[A], /) -> Given[D]: ...

    @overload
    def creating[A, B, D](
        self, spec: SpecFromTwo[A, B, D], a: Given[A], b: Given[B], /
    ) -> Given[D]: ...

    @overload
    def creating[A, B, C, D](
        self, spec: SpecFromThree[A, B, C, D], a: Given[A], b: Given[B], c: Given[C], /
    ) -> Given[D]: ...

    def creating(self, spec: Any, /, *sources: Any) -> Given[Any]:
        """Lay the row this spec describes, reading the rows it names."""
        name = self.name(spec.hint)
        build: Callable[..., WriteSpec[Any]] = spec.build

        async def write(ops: V2WriteOps, values: Sequence[Any]) -> Any:
            return await _write(ops, build(name, *values))

        return self._remember(Given(describe=name, sources=tuple(sources), write=write))

    def adding[A, D: FieldData](self, spec: FieldOf[A, D], owner: Given[A], /) -> Given[D]:
        """Lay one field row under the owner the scenario already laid."""

        async def write(ops: V2WriteOps, values: Sequence[Any]) -> Any:
            return await ops.create_field(spec.owner_id(values[0]), spec.spec)

        return self._remember(
            Given(describe=f"{spec.hint} on {owner.describe}", sources=(owner,), write=write)
        )

    def granting[R, U](
        self,
        role: Given[R],
        to: Given[U],
        *,
        role_id: Callable[[R], RoleID],
        user_id: Callable[[U], UserID],
    ) -> Given[None]:
        """Give the user the role, the way an operator would."""

        async def write(ops: V2WriteOps, values: Sequence[Any]) -> None:
            await ops.grant_roles(user_id(values[1]), [role_id(values[0])])

        return self._remember(
            Given(
                describe=f"{to.describe} holds {role.describe}",
                sources=(role, to),
                write=write,
            )
        )


async def lay(ops: V2WriteOps, wanted: Sequence[Given[Any]]) -> dict[Given[Any], Any]:
    """Write every row the wanted rows rest on, each once, in this session."""
    made: dict[Given[Any], Any] = {}

    async def settle(row: Given[Any]) -> Any:
        if row in made:
            return made[row]
        values = [await settle(source) for source in row.sources]
        made[row] = await row.write(ops, values)
        return made[row]

    for row in wanted:
        await settle(row)
    return made


def steps_of(wanted: Sequence[Given[Any]]) -> list[str]:
    """What laying these rows does, in the order it does it."""
    seen: list[Given[Any]] = []

    def walk(row: Given[Any]) -> None:
        if row in seen:
            return
        for source in row.sources:
            walk(source)
        seen.append(row)

    for row in wanted:
        walk(row)
    return [row.describe for row in seen]


def after[D, A, R](
    row: Given[D],
    build: Callable[[D], Invocation[A, R] | ActorBound[A, R, Any]],
) -> Deferred[A, R]:
    """Read the row this scenario laid, then say what to call with it.

    ``build`` receives the created data, typed, so an id the database generated is
    reachable without a placeholder or a literal repeated from the seed.
    """
    return Deferred(row, build)
