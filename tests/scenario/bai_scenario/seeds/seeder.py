"""Laying the rows a scenario needs, through the manager's own write specs.

A scenario never writes a row itself. It names a write spec and what that spec reads
from earlier rows; the seeder picks the ops path the spec's own type calls for, makes
the name, and runs every step in one session.

Which ops path writes a row follows from the spec's type, so no scenario names a path:

    RoleManagedGlobalEntityCreator  -> create_role_managed_global_entity
    RoleManagedEntityCreator        -> create_role_managed_entity
    GuardedEntityCreator            -> create_entity   (EntityCreator is one of these)
    GlobalEntityCreator             -> create_global_entity
    EntityUpserter                  -> upsert_entity
    GlobalEntityUpserter            -> upsert_global_entity
    GuardedDataUpdater              -> update_data
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Final, cast

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.specs.creator import (
    FieldCreator,
    FieldToCreate,
    GlobalEntityCreator,
    GuardedEntityCreator,
    NestedFieldCreator,
    RoleManagedEntityCreator,
    RoleManagedGlobalEntityCreator,
)
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.specs.upserter import EntityUpserter, GlobalEntityUpserter
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from bai_scenario.seeds.ops import SeedOps

type WriteSpec[D] = (
    GlobalEntityCreator[Any, D]
    | GuardedEntityCreator[Any, D]
    | RoleManagedGlobalEntityCreator[Any, D]
    | RoleManagedEntityCreator[Any, D]
    | EntityUpserter[Any, D]
    | GlobalEntityUpserter[Any, D]
    | GuardedDataUpdater[Any, D]
)


type Naming = Callable[[str], str]
"""Turns a hint into a name no other row of the same scenario holds."""


class Seed(ABC):
    """What the report says about one row a scenario lays."""

    @abstractmethod
    def kind(self) -> str:
        """레포트가 이 행을 부르는 이름."""
        raise NotImplementedError

    @abstractmethod
    def detail(self) -> str:
        """이 행이 무엇을 세워두는지."""
        raise NotImplementedError

    @abstractmethod
    def name(self, naming: Naming) -> str:
        """The name the row goes in under.

        Most rows ask ``naming`` for one. A row whose name the manager fixes answers
        with that name instead, and the report then says the name the row really holds.
        """
        raise NotImplementedError


class SeedRow[D](Seed, ABC):
    """A row that needs nothing but its own name."""

    @abstractmethod
    def seed(self, name: str) -> WriteSpec[D]:
        raise NotImplementedError


class SeedRowFrom[A, D](Seed, ABC):
    """A row that reads one row laid before it."""

    @abstractmethod
    def seed(self, name: str, source: A) -> WriteSpec[D]:
        raise NotImplementedError


class SeedRowFromTwo[A, B, D](Seed, ABC):
    """A row that reads two rows laid before it."""

    @abstractmethod
    def seed(self, name: str, first: A, second: B) -> WriteSpec[D]:
        raise NotImplementedError


class SeedRowFromThree[A, B, C, D](Seed, ABC):
    """A row that reads three rows laid before it."""

    @abstractmethod
    def seed(self, name: str, first: A, second: B, third: C) -> WriteSpec[D]:
        raise NotImplementedError


class SeedUser[A, B, C](Seed, ABC):
    """A user, provisioned through the path the manager provisions one through.

    The row, its graph, its preset roles, its keypair and its personal project are one
    operation, and a seed takes that operation whole.
    """

    @abstractmethod
    def seed(self, name: str, domain: A, policy: B, keypair_policy: C) -> FullUserCreator:
        raise NotImplementedError


class SeedFieldWithNestedRows[A, D: FieldData](ABC):
    """A field row together with the rows it owns, written in one transaction.

    A monitor that records a scope action writes the record and its scope rows atomically;
    a seed that lays such a record takes that whole write rather than splitting it. Like
    :class:`SeedField`, the row's name and report line come from the owner it is laid under.
    """

    @abstractmethod
    def kind(self) -> str:
        """이 필드를 가진 주인이 무엇을 할 수 있게 되는지."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self, owner: A) -> Any:
        raise NotImplementedError

    @abstractmethod
    def field(self) -> FieldCreator[Any, Any, D]:
        raise NotImplementedError

    @abstractmethod
    def nested(self) -> Sequence[NestedFieldCreator[Any, Any, Any]]:
        raise NotImplementedError


class SeedNest[D](ABC):
    """seed 여러 개를 함께 심어 전제 하나를 준비한다.

    단위가 행 하나가 아니라 "폴더를 만들 수 있는 사용자" 같은 전제다. 무엇을 준비하는지는
    ``kind``가 말하고, 어떤 seed와 어떤 nest를 딛는지는 ``lay`` 안이 보여준다.

    ``Seeder``를 받지만 그 입구가 전부 seed 객체를 요구하므로, nest가 행을 직접 쓰는
    길은 없다.
    """

    @abstractmethod
    def kind(self) -> str:
        """이 묶음이 무엇을 준비하는지."""
        raise NotImplementedError

    @abstractmethod
    def lay(self, seed: Seeder) -> D:
        raise NotImplementedError


class SeedField[A, D: FieldData](ABC):
    """A field row written under an owner the scenario already laid.

    A field grants nothing of its own and dies with its owner, so it is never laid on
    its own: the owner comes with it, and its name with the owner.
    """

    @abstractmethod
    def kind(self) -> str:
        """이 필드를 가진 주인이 무엇을 할 수 있게 되는지."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self, owner: A) -> Any:
        raise NotImplementedError

    @abstractmethod
    def seed(self) -> FieldCreator[Any, Any, D]:
        raise NotImplementedError


class SeedLink[S, T](ABC):
    """A row that links two entities and belongs to neither.

    A resource group reaches a session only through one of these: the group is linked
    to a domain, a project, or a user's keypair, and the session's scope has to find it
    on one of those three paths.
    """

    @abstractmethod
    def kind(self) -> str:
        """무엇을 잇는지. 스코프와 대상 사이에 놓고 읽는다."""
        raise NotImplementedError

    @abstractmethod
    def scope_id(self, scope: S) -> Any:
        raise NotImplementedError

    @abstractmethod
    def target_id(self, target: T) -> Any:
        raise NotImplementedError

    @abstractmethod
    def seed(self) -> RelationCreator[Any, Any, Any]:
        raise NotImplementedError


@dataclass(frozen=True, eq=False)
class Laid[D]:
    """One row a scenario lays down, and a handle on what the write answered.

    Compared by identity, so a call that reads this row holds the handle rather than
    repeating a value the row also carries.
    """

    name: str
    """The name the seeder made for this row, for a call that needs it."""
    kind: str
    """레포트가 이 행을 부르는 이름."""
    nest: tuple[str, ...]
    """이 행을 심은 묶음들. 바깥부터 안쪽 순서다."""
    describe: str
    """How other rows refer to this one."""
    states: str
    """What laying this row establishes, as a sentence, for the report."""
    sources: tuple[Laid[Any], ...]
    write: Callable[[SeedOps, Sequence[Any]], Awaitable[D]]


SKEW: Final = timedelta(seconds=30)
"""두 시계가 어긋나 있어도 봐주는 폭."""


def _since(start: datetime) -> Callable[[datetime], bool]:
    """``start`` 뒤에, 그리고 지금보다 뒤가 아닌 시각."""

    def condition(moment: datetime) -> bool:
        if moment.tzinfo is None:
            return False
        return start - SKEW <= moment <= datetime.now(UTC) + SKEW

    return condition


def _there_is(seed: Seed, name: str) -> str:
    return f"{seed.kind()} {name}"


def _states(sentence: str, detail: str) -> str:
    return f"{sentence}: {detail}" if detail else sentence


async def _write(ops: SeedOps, spec: WriteSpec[Any]) -> Any:
    """Run one spec down the ops path its own type calls for."""
    if isinstance(spec, RoleManagedGlobalEntityCreator):
        return await ops.create_role_managed_global_entity(spec)
    if isinstance(spec, RoleManagedEntityCreator):
        return await ops.create_role_managed_entity(spec)
    if isinstance(spec, GuardedEntityCreator):
        return await ops.create_entity(spec)
    if isinstance(spec, GlobalEntityCreator):
        return await ops.create_global_entity(spec)
    if isinstance(spec, EntityUpserter):
        return await ops.upsert_entity(spec)
    if isinstance(spec, GlobalEntityUpserter):
        return await ops.upsert_global_entity(spec)
    return await ops.update_data(spec)


@dataclass
class Seeder:
    """The rows one scenario lays, and the names it gives them.

    A scenario builder is handed a fresh one, so the numbering restarts at every row of
    the table and a name says which row of this scenario made it.
    """

    _counts: dict[str, int] = field(default_factory=dict)
    _laid: list[Laid[Any]] = field(default_factory=list)
    _singletons: dict[type[Any], Laid[Any]] = field(default_factory=dict)
    _nesting: list[str] = field(default_factory=list)
    _started: datetime = field(default_factory=lambda: datetime.now(UTC))

    def since_started(self) -> Callable[[datetime], bool]:
        """이 시나리오를 만들기 시작한 뒤에 찍힌 시각.

        실행이 쓴 값인지를 묻는 조건이다. 얼마 안에 찍혔는지가 아니라 언제부터 뒤인지를
        기준으로 삼으므로, 임의의 시간 폭을 고르지 않는다.
        """
        return _since(self._started)

    def within[D](self, nest: SeedNest[D]) -> D:
        """Lay what this nest lays, remembering that it laid them."""
        self._nesting.append(nest.kind())
        try:
            return nest.lay(self)
        finally:
            self._nesting.pop()

    def declared(self) -> tuple[Laid[Any], ...]:
        """Every row asked for so far, in the order it was asked."""
        return tuple(self._laid)

    def once[D](self, seed: SeedRow[D], /) -> Laid[D]:
        """The one row of its kind this scenario has.

        A row whose name the manager fixes is a singleton: laying it twice collides on
        the primary key. Whoever needs it asks for it and gets the same one, and the
        seed's own type is what says they are the same.
        """
        key = type(seed)
        if key not in self._singletons:
            self._singletons[key] = self.creating(seed)
        return cast("Laid[D]", self._singletons[key])

    def _remember[D](self, row: Laid[D]) -> Laid[D]:
        self._laid.append(row)
        return row

    def name(self, hint: str) -> str:
        """``hint-1``, ``hint-2``, ... within this scenario."""
        self._counts[hint] = self._counts.get(hint, 0) + 1
        return f"{hint}-{self._counts[hint]}"

    def creating[D](self, seed: SeedRow[D], /) -> Laid[D]:
        """Lay a row that needs nothing but its own name."""
        name = seed.name(self.name)

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            return await _write(ops, seed.seed(name))

        return self._remember(self._given(seed, name, (), write, _there_is(seed, name)))

    def creating_from[A, D](self, seed: SeedRowFrom[A, D], a: Laid[A], /) -> Laid[D]:
        """Lay a row that reads one row laid before it."""
        name = seed.name(self.name)

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            return await _write(ops, seed.seed(name, values[0]))

        return self._remember(self._given(seed, name, (a,), write, _there_is(seed, name)))

    def creating_from_two[A, B, D](
        self, seed: SeedRowFromTwo[A, B, D], a: Laid[A], b: Laid[B], /
    ) -> Laid[D]:
        """Lay a row that reads two rows laid before it."""
        name = seed.name(self.name)

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            return await _write(ops, seed.seed(name, values[0], values[1]))

        return self._remember(self._given(seed, name, (a, b), write, _there_is(seed, name)))

    def creating_from_three[A, B, C, D](
        self, seed: SeedRowFromThree[A, B, C, D], a: Laid[A], b: Laid[B], c: Laid[C], /
    ) -> Laid[D]:
        """Lay a row that reads three rows laid before it."""
        name = seed.name(self.name)

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            return await _write(ops, seed.seed(name, values[0], values[1], values[2]))

        return self._remember(self._given(seed, name, (a, b, c), write, _there_is(seed, name)))

    def provisioning[A, B, C](
        self,
        seed: SeedUser[A, B, C],
        a: Laid[A],
        b: Laid[B],
        c: Laid[C],
        /,
    ) -> Laid[UserData]:
        """Provision what the manager provisions as one operation."""
        name = seed.name(self.name)

        async def write(ops: SeedOps, values: Sequence[Any]) -> UserData:
            result = await ops.create_user(seed.seed(name, *values))
            return result.user

        return self._remember(self._given(seed, name, (a, b, c), write, _there_is(seed, name)))

    def adding[A, D: FieldData](self, seed: SeedField[A, D], owner: Laid[A], /) -> Laid[D]:
        """Lay one field row under the owner the scenario already laid."""

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            return await ops.create_field(seed.owner_id(values[0]), seed.seed())

        return self._remember(
            Laid(
                name=owner.name,
                kind=owner.kind,
                nest=tuple(self._nesting),
                describe=f"{owner.describe}({seed.kind()})",
                states=f"{owner.describe}: {seed.kind()}",
                sources=(owner,),
                write=write,
            )
        )

    def adding_with_nested[A, D: FieldData](
        self, seed: SeedFieldWithNestedRows[A, D], owner: Laid[A], /
    ) -> Laid[D]:
        """Lay one field row and the rows it owns, in the one write a monitor uses."""

        async def write(ops: SeedOps, values: Sequence[Any]) -> Any:
            created = await ops.atomic_create_fields_with_nested(
                [FieldToCreate(owner_id=seed.owner_id(values[0]), creator=seed.field())],
                list(seed.nested()),
            )
            return created[0]

        return self._remember(
            Laid(
                name=owner.name,
                kind=owner.kind,
                nest=tuple(self._nesting),
                describe=f"{owner.describe}({seed.kind()})",
                states=f"{owner.describe}: {seed.kind()}",
                sources=(owner,),
                write=write,
            )
        )

    def linking[S, T](self, seed: SeedLink[S, T], scope: Laid[S], target: Laid[T], /) -> Laid[None]:
        """Link the two rows this scenario laid, the way an operator would."""

        async def write(ops: SeedOps, values: Sequence[Any]) -> None:
            await ops.create_relations(
                seed.seed(), [(seed.scope_id(values[0]), seed.target_id(values[1]))]
            )

        return self._remember(
            Laid(
                name=target.name,
                kind=target.kind,
                nest=tuple(self._nesting),
                describe=target.describe,
                states=f"{scope.describe} {seed.kind()} {target.describe}",
                sources=(scope, target),
                write=write,
            )
        )

    def granting[R, U](
        self,
        role: Laid[R],
        to: Laid[U],
        *,
        role_id: Callable[[R], RoleID],
        user_id: Callable[[U], UserID],
    ) -> Laid[None]:
        """Give the user the role, the way an operator would."""

        async def write(ops: SeedOps, values: Sequence[Any]) -> None:
            await ops.grant_roles(user_id(values[1]), [role_id(values[0])])

        return self._remember(
            Laid(
                name=to.name,
                kind=to.kind,
                nest=tuple(self._nesting),
                describe=to.describe,
                states=f"{to.describe}: {role.describe} 보유",
                sources=(role, to),
                write=write,
            )
        )

    def _given[D](
        self,
        seed: Seed,
        name: str,
        sources: Sequence[Laid[Any]],
        write: Callable[[SeedOps, Sequence[Any]], Awaitable[D]],
        sentence: str,
    ) -> Laid[D]:
        return Laid(
            name=name,
            kind=seed.kind(),
            nest=tuple(self._nesting),
            describe=f"{seed.kind()} {name}",
            states=_states(sentence, seed.detail()),
            sources=tuple(sources),
            write=write,
        )


async def lay(ops: SeedOps, wanted: Sequence[Laid[Any]], made: dict[Laid[Any], Any]) -> None:
    """Write every row the wanted rows rest on, each once, in this session.

    What has been written is carried in ``made`` rather than answered, so a caller that
    lays in several goes writes each row once across all of them.
    """

    async def settle(row: Laid[Any]) -> Any:
        if row in made:
            return made[row]
        values = [await settle(source) for source in row.sources]
        made[row] = await row.write(ops, values)
        return made[row]

    for row in wanted:
        await settle(row)


def laid_in_order(wanted: Sequence[Laid[Any]]) -> list[Laid[Any]]:
    """Every row the wanted rows rest on, in the order they are written."""
    seen: list[Laid[Any]] = []

    def walk(row: Laid[Any]) -> None:
        if row in seen:
            return
        for source in row.sources:
            walk(source)
        seen.append(row)

    for row in wanted:
        walk(row)
    return seen
