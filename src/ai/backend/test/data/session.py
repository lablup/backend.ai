import uuid
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class CreatedSessionMeta:
    id: uuid.UUID
    name: str


@dataclass
class SessionDependency:
    dependencies: Mapping[CreatedSessionMeta, list[CreatedSessionMeta]]
