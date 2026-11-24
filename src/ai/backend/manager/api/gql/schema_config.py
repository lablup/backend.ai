"""Strawberry configuration shared by the manager GQL schemas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, final

from strawberry.schema.config import StrawberryConfig

from ai.backend.common.tristate.unset import UNSET
from ai.backend.manager.errors.api import GraphQLFieldNotSelected


@final
class MissingRejectingResolver:
    """Resolver of fields without their own resolver: rejects a value the request did not select."""

    def __call__(self, source: Any, name: str) -> object:
        value = getattr(source, name)
        if value is UNSET:
            raise GraphQLFieldNotSelected(extra_msg=name)
        return value


@dataclass
class GQLSchemaConfig(StrawberryConfig):
    default_resolver: Callable[[Any, str], object] = field(default_factory=MissingRejectingResolver)
