"""Laying rows down through the manager's own write path.

The generic scenario surface does not know what makes a row. This does: a creator spec
answers the row's data type and, by its own type, which ops path writes it. Four
overloads stand in for that choice, so no scenario names a path.

Which role an actor holds decides what the request answers, so a scenario that depends
on one says so in ``holding`` rather than leaving the reader to find it in the World. A
grant is not a row the request acts on, and does not sit among them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, overload

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
    RoleManagedGlobalEntityCreator,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.scenario import Persona
from ai.backend.testutils.typed_scenario import Held, Seed
from bai_scenario.infra.world import World

__all__ = (
    "DOMAIN_ADMIN_PRESET",
    "PROJECT_ADMIN_PRESET",
    "PROJECT_MEMBER_PRESET",
    "USER_PRESET",
    "SeedRoom",
    "Grown",
    "Scope",
    "creates",
    "holds",
    "times",
    "on_the_domain",
    "on_the_project",
    "on_their_own_scope",
)


@dataclass(frozen=True)
class SeedRoom:
    """What laying a row down has to reach: the write path, and the world it lands in."""

    engine: ExtendedAsyncSAEngine
    world: World
    ops: OpsRepository[Any]


type Grown[D] = Seed[SeedRoom, D]


@overload
def creates[R: Base, D](creator: RoleManagedGlobalEntityCreator[R, D]) -> Grown[D]: ...


@overload
def creates[R: Base, D](creator: RoleManagedEntityCreator[R, D]) -> Grown[D]: ...


@overload
def creates[R: Base, D](creator: EntityCreator[R, D]) -> Grown[D]: ...


@overload
def creates[R: Base, D](creator: GlobalEntityCreator[R, D]) -> Grown[D]: ...


def creates(creator: Any) -> Grown[Any]:
    """Lay down the row this creator describes, through the same ops path production
    uses. Which path that is follows from the creator's own type.
    """
    label = type(creator).__name__
    if isinstance(creator, RoleManagedGlobalEntityCreator):

        async def make_role_managed_global(room: SeedRoom) -> Any:
            return await room.ops.create_role_managed_global_entity(creator)

        return Seed(make_role_managed_global, label)
    if isinstance(creator, RoleManagedEntityCreator):

        async def make_role_managed(room: SeedRoom) -> Any:
            return await room.ops.create_role_managed_entity(creator)

        return Seed(make_role_managed, label)
    if isinstance(creator, EntityCreator):

        async def make_entity(room: SeedRoom) -> Any:
            return await room.ops.create_entity(creator)

        return Seed(make_entity, label)

    async def make_global(room: SeedRoom) -> Any:
        return await room.ops.create_global_entity(creator)

    return Seed(make_global, label)


# ---------------------------------------------------------------------------
# What an actor holds: the premise a permission scenario rests on, said out loud
# ---------------------------------------------------------------------------

DOMAIN_ADMIN_PRESET = "preset_domain_admin"
PROJECT_ADMIN_PRESET = "preset_project_admin"
PROJECT_MEMBER_PRESET = "preset_project_member"
USER_PRESET = "preset_user"


@dataclass(frozen=True)
class Scope:
    """Which scope's copy of a preset role is meant, and how a report says it."""

    label: str
    id_of: Callable[[SeedRoom, Persona], str]


def on_the_domain() -> Scope:
    """The role the preset made in the world's domain."""
    return Scope("the domain", lambda room, _persona: str(room.world.domain_id))


def on_the_project() -> Scope:
    """The role the preset made in the world's shared project."""
    return Scope("the project", lambda room, _persona: str(room.world.project_id))


def on_their_own_scope() -> Scope:
    """The role the preset made in the actor's own user scope."""
    return Scope("their own scope", lambda room, persona: str(room.world.users[persona].id))


def holds(preset: str, scope: Scope) -> Held[SeedRoom]:
    """The actor holds the role a preset made in that scope.

    Assigned the way an operator assigns one. Which role that is was settled when the
    World created the scope, so nothing here looks it up.
    """

    async def apply(room: SeedRoom, persona: Persona) -> None:
        scope_id = scope.id_of(room, persona)
        role_id = room.world.roles.get((preset, scope_id))
        if role_id is None:
            raise LookupError(f"no role from preset {preset!r} in scope {scope_id}")
        await PermissionControllerRepository(room.engine).assign_role(
            UserRoleAssignmentInput(user_id=UserID(room.world.users[persona].id), role_id=role_id)
        )

    return Held(apply, f"{preset} on {scope.label}")


def times[D](count: int, make: Callable[[int], Grown[D]]) -> list[Grown[D]]:
    """``count`` rows, each built from its own index.

    How many rows are already there is often the point of a scenario -- a limit is
    reached or it is not -- and this keeps the number in one place instead of a
    hand-copied list whose length the reader has to count.
    """
    return [make(i) for i in range(count)]
