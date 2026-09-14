from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogFieldType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import FieldGroupMeta, GroupMeta
from ai.backend.manager.api.rest.export.handler import ExportHandler
from ai.backend.manager.api.rest.export.registry import register_export_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.export.db_source.db_source import ExportDBSource
from ai.backend.manager.repositories.export.registry.base import ExportReportRegistry
from ai.backend.manager.repositories.export.repository import ExportRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService


@pytest.fixture()
def export_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> ExportProcessors:
    db_source = ExportDBSource(database_engine)
    registry = ExportReportRegistry.create_default()
    repo = ExportRepository(db_source, registry)
    service = ExportService(repo)
    return ExportProcessors(
        processor_registry.group(GroupMeta(UserEntityType())),
        processor_registry.group(GroupMeta(SessionEntityType())),
        processor_registry.group(GroupMeta(ProjectEntityType())),
        processor_registry.group(GroupMeta(GlobalEntityType())),
        processor_registry.dangling_field_group(FieldGroupMeta(AuditLogFieldType()), AuditLogData),
        service,
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    export_processors: ExportProcessors,
    processor_registry: ProcessorRegistry[Any],
) -> list[RouteRegistry]:
    """Load only the modules required for export-domain tests."""
    return [
        register_export_routes(
            ExportHandler(
                export=export_processors,
                domain=DomainProcessors(
                    processor_registry.group(GroupMeta(DomainEntityType())), AsyncMock(), []
                ),
                export_config=MagicMock(),
            ),
            route_deps,
        ),
    ]
