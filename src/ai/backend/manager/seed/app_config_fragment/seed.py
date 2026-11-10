from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self, override

from pydantic import Field, model_validator

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.manager.models.app_config_fragment.upserters import (
    AppConfigFragmentUpserter,
    PublicAppConfigFragmentUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class AppConfigFragmentSeed(SeedItem):
    """One ``app_config_fragments`` row: the value of a config name at one scope.
    ``scope_id`` names the domain or user, and is left out for ``public``."""

    config_name: str = Field(min_length=1, max_length=128)
    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None = None
    config: dict[str, Any]

    @model_validator(mode="after")
    def _scope_id_matches_scope_type(self) -> Self:
        """The rule ``scope_id_matches_scope_type`` checks, so the file fails ``seed check``."""
        if (self.scope_type is AppConfigScopeType.PUBLIC) != (self.scope_id is None):
            raise ValueError("scope_id is left out for public and stated for domain and user")
        return self

    @override
    def key(self) -> str:
        if self.scope_id is None:
            return f"{self.config_name}:{self.scope_type.value}"
        return f"{self.config_name}:{self.scope_type.value}:{self.scope_id}"

    @override
    def write(self) -> SeedWrite:
        owner = self.scope_type.to_owner(self.scope_id)
        upserter = (
            PublicAppConfigFragmentUpserter(config_name=self.config_name, config=self.config)
            if owner is None
            else AppConfigFragmentUpserter(
                config_name=self.config_name, owner=owner, config=self.config
            )
        )
        return SeedWrite(upserter=upserter, field_upserters=[], field_purgers=[])

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[AppConfigFragmentSeed]]) -> list[SeedRejection]:
        return []
