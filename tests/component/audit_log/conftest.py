"""Fixtures for audit log REST v2 component tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.validator.bulk import BulkActionValidator, BulkValidationResult
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.audit_log.handler import V2AuditLogHandler
from ai.backend.manager.api.rest.v2.audit_log.registry import register_v2_audit_log_routes
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors
from ai.backend.manager.services.audit_log.service import AuditLogService
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


AuditLogFactory = Callable[..., Awaitable[uuid.UUID]]


@pytest.fixture()
def audit_log_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> AuditLogProcessors:
    """Real repository + service stack; bulk RBAC validator is stubbed out.

    Component tests verify REST plumbing (auth, body parsing, routing,
    pagination) — RBAC enforcement is covered in
    ``tests/unit/manager/repositories/audit_log/test_scoped_search.py``.
    """
    repo = AuditLogRepository(db=database_engine)
    service = AuditLogService(repo)

    bulk_validator = MagicMock(spec=BulkActionValidator)
    bulk_validator.validate = AsyncMock(
        return_value=BulkValidationResult(allowed_entities=[], denied_entities=[])
    )
    validators = MagicMock(spec=ActionValidators)
    validators.rbac = MagicMock()
    validators.rbac.bulk = bulk_validator

    return AuditLogProcessors(service=service, action_monitors=[], validators=validators)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    audit_log_processors: AuditLogProcessors,
) -> list[RouteRegistry]:
    """Register the REST v2 audit log routes for the test server."""
    processors = MagicMock(spec=Processors)
    processors.audit_log = audit_log_processors
    adapter = AuditLogAdapter(processors)

    handler = V2AuditLogHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_audit_log_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def audit_log_factory(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncIterator[AuditLogFactory]:
    """Insert audit_log rows on demand; clean them up at teardown."""
    repo = AuditLogRepository(db=database_engine)
    created: list[uuid.UUID] = []

    async def _factory(
        *,
        entity_type: str,
        entity_id: str | None = None,
        triggered_by: str | None = None,
        operation: str = "update",
        status: OperationStatus = OperationStatus.SUCCESS,
    ) -> uuid.UUID:
        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=uuid.uuid4(),
                entity_type=entity_type,
                operation=operation,
                created_at=datetime.now(UTC),
                description=f"{entity_type} {operation}",
                status=status,
                entity_id=entity_id,
                request_id=None,
                triggered_by=triggered_by,
                duration=None,
            )
        )
        data = await repo.create(creator)
        created.append(data.id)
        return data.id

    yield _factory

    if created:
        async with database_engine.begin() as conn:
            await conn.execute(AuditLogRow.__table__.delete().where(AuditLogRow.id.in_(created)))
