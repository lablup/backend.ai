from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from .bootstrap import BootstrapComposer, BootstrapInput, BootstrapResources
from .infrastructure.composer import (
    InfrastructureComposer,
    InfrastructureComposerInput,
    InfrastructureResources,
)
from .storage.composer import StorageComposer, StorageComposerInput, StorageResources


@dataclass
class DependencyInput:
    """Input required for complete dependency setup."""

    config_path: Path


@dataclass
class DependencyResources:
    """All dependency resources for storage proxy."""

    bootstrap: BootstrapResources
    infrastructure: InfrastructureResources
    storage: StorageResources


class StorageDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Main composer for all storage proxy dependencies."""

    @property
    def stage_name(self) -> str:
        return "storage-proxy"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all storage proxy dependencies."""
        # Stage 1: Bootstrap (config loading)
        bootstrap = await stack.enter_composer(
            BootstrapComposer(),
            BootstrapInput(config_path=setup_input.config_path),
        )

        # Stage 2: Infrastructure (etcd, redis)
        infrastructure = await stack.enter_composer(
            InfrastructureComposer(),
            InfrastructureComposerInput(local_config=bootstrap.config),
        )

        # Stage 3: Storage (storage-pool)
        storage = await stack.enter_composer(
            StorageComposer(),
            StorageComposerInput(local_config=bootstrap.config),
        )

        yield DependencyResources(
            bootstrap=bootstrap,
            infrastructure=infrastructure,
            storage=storage,
        )
