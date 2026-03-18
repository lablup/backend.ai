from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.export.handler import ExportHandler
from ai.backend.manager.api.rest.export.registry import register_export_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.export.db_source.db_source import ExportDBSource
from ai.backend.manager.repositories.export.registry.base import ExportReportRegistry
from ai.backend.manager.repositories.export.repository import ExportRepository
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService


@pytest.fixture()
def export_processors(database_engine: ExtendedAsyncSAEngine) -> ExportProcessors:
    db_source = ExportDBSource(database_engine)
    registry = ExportReportRegistry.create_default()
    repo = ExportRepository(db_source, registry)
    service = ExportService(repo)
    return ExportProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    export_processors: ExportProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for export-domain tests."""
    return [
        register_export_routes(
            ExportHandler(export=export_processors, export_config=MagicMock()), route_deps
        ),
    ]
