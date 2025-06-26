import uuid
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CreatedSessionMeta:
    id: uuid.UUID
    name: str


@dataclass
class SessionDependency:
    dependencies: Mapping[CreatedSessionMeta, list[CreatedSessionMeta]]
