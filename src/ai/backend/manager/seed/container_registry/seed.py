from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self, override

from pydantic import Field, model_validator

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.models.container_registry.row import (
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.container_registry.upserters import ContainerRegistryUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ContainerRegistrySeed(SeedItem):
    """One ``container_registries`` row, keyed by its id."""

    id: ContainerRegistryID
    url: str = Field(max_length=512)
    type: ContainerRegistryType
    registry_name: str = Field(min_length=1, max_length=255)
    is_global: bool = True
    project: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = None
    ssl_verify: bool = True
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _valid_registry(self) -> Self:
        """The URL and the Harbor project rules the API applies to a new registry."""
        args = ContainerRegistryValidatorArgs(url=self.url, type=self.type, project=self.project)
        try:
            ContainerRegistryValidator(args).validate()
        except BackendAIError as e:
            raise ValueError(str(e)) from e
        return self

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ContainerRegistryUpserter(
                id=self.id,
                url=self.url,
                registry_type=self.type,
                registry_name=self.registry_name,
                is_global=self.is_global,
                project=self.project,
                username=self.username,
                password=self.password,
                ssl_verify=self.ssl_verify,
                extra=self.extra,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rule the create API applies to the registry name."""
        if not self.registry_name.strip():
            return ["registry_name is blank"]
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ContainerRegistrySeed]]) -> list[SeedRejection]:
        return []
