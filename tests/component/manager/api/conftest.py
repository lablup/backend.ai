from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.types import ModuleDeps
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.processors import Processors


@pytest.fixture()
def server_module_deps_factory() -> Callable[[RootContext], ModuleDeps]:
    """Build ``ModuleDeps`` with real container-registry processors.

    When the test's cleanup contexts include ``services_ctx``, the quota
    service is wired through the real processor pipeline so that harbor
    quota CRUD tests exercise the full handler → processor → service path.
    """

    def _factory(root_ctx: RootContext) -> ModuleDeps:
        processors: Any = getattr(root_ctx, "processors", None) or MagicMock()

        # Wire up container_registry processors from services_ctx
        if hasattr(root_ctx, "services_ctx"):
            quota_service = root_ctx.services_ctx.per_project_container_registries_quota
            cr_service = ContainerRegistryService(
                MagicMock(),  # db — unused by quota methods
                MagicMock(),  # container_registry_repository — unused by quota methods
                quota_service=quota_service,
            )
            cr_processors = ContainerRegistryProcessors(cr_service, [])
            if isinstance(processors, MagicMock):
                processors.container_registry = cr_processors

        return ModuleDeps(
            cors_options=root_ctx.cors_options,
            processors=cast(Processors, processors),
            config_provider=root_ctx.config_provider,
            gql_context_deps=MagicMock(),
        )

    return _factory
