"""Laying rows down through the manager's own write path.

The generic scenario surface does not know what makes a row. This does: a creator spec
answers the row's data type and, by its own type, which ops path writes it. Four
overloads stand in for that choice, so no scenario names a path.
"""

from __future__ import annotations

from typing import Any, overload

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
    RoleManagedGlobalEntityCreator,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.testutils.typed_scenario import Seed

__all__ = ("Sown", "creates")

type Sown[D] = Seed[OpsRepository[Any], D]


@overload
def creates[R: Base, D](creator: RoleManagedGlobalEntityCreator[R, D]) -> Sown[D]: ...


@overload
def creates[R: Base, D](creator: RoleManagedEntityCreator[R, D]) -> Sown[D]: ...


@overload
def creates[R: Base, D](creator: EntityCreator[R, D]) -> Sown[D]: ...


@overload
def creates[R: Base, D](creator: GlobalEntityCreator[R, D]) -> Sown[D]: ...


def creates(creator: Any) -> Sown[Any]:
    """Lay down the row this creator describes, through the same ops path production
    uses. Which path that is follows from the creator's own type.
    """
    label = type(creator).__name__
    if isinstance(creator, RoleManagedGlobalEntityCreator):

        async def make_role_managed_global(ops: OpsRepository[Any]) -> Any:
            return await ops.create_role_managed_global_entity(creator)

        return Seed(make_role_managed_global, label)
    if isinstance(creator, RoleManagedEntityCreator):

        async def make_role_managed(ops: OpsRepository[Any]) -> Any:
            return await ops.create_role_managed_entity(creator)

        return Seed(make_role_managed, label)
    if isinstance(creator, EntityCreator):

        async def make_entity(ops: OpsRepository[Any]) -> Any:
            return await ops.create_entity(creator)

        return Seed(make_entity, label)

    async def make_global(ops: OpsRepository[Any]) -> Any:
        return await ops.create_global_entity(creator)

    return Seed(make_global, label)
