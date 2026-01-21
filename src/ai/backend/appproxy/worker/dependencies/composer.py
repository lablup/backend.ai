from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from .bootstrap import BootstrapComposer, BootstrapInput
from .infrastructure import InfrastructureComposer, InfrastructureResources


@dataclass
class DependencyInput:
    """Input required for complete dependency setup."""

    config_path: Path | None = None


@dataclass
class DependencyResources:
    """All dependency resources for app proxy worker."""

    infrastructure: InfrastructureResources


class WorkerDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Main composer for all app proxy worker dependencies."""

    @property
    def stage_name(self) -> str:
        return "worker"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all app proxy worker dependencies."""
        # Stage 1: Bootstrap (config)
        bootstrap = await stack.enter_composer(
            BootstrapComposer(),
            BootstrapInput(config_path=setup_input.config_path),
        )

        # Stage 2: Infrastructure (redis)
        infrastructure = await stack.enter_composer(
            InfrastructureComposer(),
            bootstrap.config,
        )

        yield DependencyResources(
            infrastructure=infrastructure,
        )
