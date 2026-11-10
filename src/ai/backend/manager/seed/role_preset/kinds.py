from __future__ import annotations

import importlib
import pkgutil

import ai.backend.common.data.entity as entity_package
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.errors.permission import InvalidRoleSeed


def _subclasses[T: type](base: T) -> list[T]:
    found: list[T] = []
    for sub in base.__subclasses__():
        found.append(sub)
        found.extend(_subclasses(sub))
    return found


class PermissionKinds:
    """The entity types a role file states a permission for.

    `permissions.entity_type` holds an `EntityType`, so the kind classes are what the
    declaration is compared against. Only the entity package's own kinds count:
    `__subclasses__` alone varies with what the caller has imported.
    """

    _entity_types: frozenset[str]

    def __init__(self) -> None:
        for module in pkgutil.iter_modules(entity_package.__path__):
            importlib.import_module(f"{entity_package.__name__}.{module.name}")
        names: set[str] = set()
        for kind in _subclasses(EntityType):
            if not kind.__module__.startswith(entity_package.__name__):
                continue
            names.add(self._name_of(kind))
        self._entity_types = frozenset(names)

    def _name_of(self, kind: type[EntityType]) -> str:
        """The kind's name. A kind missing a name or a description is refused."""
        address = f"{kind.__module__}.{kind.__qualname__}"
        try:
            name = kind.name()
        except NotImplementedError as e:
            raise InvalidRoleSeed(f"{address} declares no name; it cannot be permitted.") from e
        try:
            kind.description()
        except NotImplementedError as e:
            raise InvalidRoleSeed(f"{address} declares no description.") from e
        if not name:
            raise InvalidRoleSeed(f"{address} answers an empty name.")
        return name

    def declared(self) -> frozenset[str]:
        return self._entity_types
