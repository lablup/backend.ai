from __future__ import annotations

from collections.abc import Sequence
from typing import Self, override

from pydantic import Field, model_validator

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.system_session_environ.row import ENVIRON_KEY_PATTERN
from ai.backend.manager.models.system_session_environ.upserters import (
    SystemSessionEnvironUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class SystemSessionEnvironSeed(SeedItem):
    """One ``system_session_environ`` row: the variable a value source is injected under at
    one scope. ``scope_id`` names the domain or project, and is left out for ``public``."""

    value_source: SystemSessionEnvironValueSource
    environ_key: str = Field(alias="key", max_length=256, pattern=ENVIRON_KEY_PATTERN)
    scope_type: SystemSessionEnvironScopeType
    scope_id: SystemSessionEnvironScopeID | None = None
    enabled: bool

    @model_validator(mode="after")
    def _validate_scope_id_for_scope_type(self) -> Self:
        """The public scope is named, not stated by id, so the file fails ``seed check``."""
        if (self.scope_type is SystemSessionEnvironScopeType.PUBLIC) != (self.scope_id is None):
            raise ValueError("scope_id is left out for public and stated for domain and project")
        return self

    @override
    def key(self) -> str:
        if self.scope_id is None:
            return f"{self.environ_key}:{self.scope_type.value}"
        return f"{self.environ_key}:{self.scope_type.value}:{self.scope_id}"

    @override
    def write(self) -> SeedWrite:
        owner = (
            global_entity_id(GlobalEntityName.PUBLIC)
            if self.scope_id is None
            else self.scope_type.to_owner(self.scope_id)
        )
        return SeedWrite(
            upserter=SystemSessionEnvironUpserter(
                owner=owner,
                value_source=self.value_source,
                key=self.environ_key,
                enabled=self.enabled,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[SystemSessionEnvironSeed]]) -> list[SeedRejection]:
        return []
