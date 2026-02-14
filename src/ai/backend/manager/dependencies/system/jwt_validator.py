from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class JWTValidatorDependency(NonMonitorableDependencyProvider[ManagerUnifiedConfig, JWTValidator]):
    """Provides JWTValidator instance from manager configuration."""

    @property
    def stage_name(self) -> str:
        return "jwt-validator"

    @asynccontextmanager
    async def provide(self, setup_input: ManagerUnifiedConfig) -> AsyncIterator[JWTValidator]:
        jwt_config = setup_input.jwt.to_jwt_config()
        yield JWTValidator(jwt_config)
