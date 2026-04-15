"""Component tests for v2 Session GET endpoint RBAC validation.

Tests that ``GET /v2/sessions/{session_id}`` enforces RBAC through
``SingleEntityActionProcessor``:

- Regular users without explicit permission grants are denied (403).
- Superadmin bypasses RBAC and can read any session.
- Superadmin reading a nonexistent session receives 404 (RBAC bypassed,
  the service raises ``SessionNotFound``).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.session import SessionAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.session.handler import V2SessionHandler
from ai.backend.manager.api.rest.v2.session.registry import register_v2_session_routes
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo

    from .conftest import SessionSeedData, UserFixtureData


@pytest.fixture()
def rbac_permission_repo(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    """Real permission controller repository backed by the real DB."""
    return PermissionControllerRepository(database_engine)


@pytest.fixture()
async def session_processors(
    session_repository: SessionRepository,
    agent_registry: AsyncMock,
    background_task_manager: BackgroundTaskManager,
    error_monitor: ErrorPluginContext,
    appproxy_client_pool: AsyncMock,
    rbac_permission_repo: PermissionControllerRepository,
) -> SessionProcessors:
    """Override of ``session_processors`` with a real ``SingleEntityActionRBACValidator``.

    RBAC checks run ``check_permission_with_scope_chain`` against the real DB,
    so ``get_session`` returns 403 for regular users without explicit grants.
    Superadmin bypasses RBAC.
    """
    args = SessionServiceArgs(
        agent_registry=agent_registry,
        event_fetcher=AsyncMock(),
        background_task_manager=background_task_manager,
        event_hub=AsyncMock(),
        error_monitor=error_monitor,
        idle_checker_host=AsyncMock(),
        session_repository=session_repository,
        scheduling_controller=AsyncMock(),
        appproxy_client_pool=appproxy_client_pool,
        user_repository=AsyncMock(),
    )
    service = SessionService(args)
    real_single_entity_validator = SingleEntityActionRBACValidator(rbac_permission_repo)
    return SessionProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=AsyncMock(),
                single_entity=real_single_entity_validator,
            )
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    session_processors: SessionProcessors,
) -> list[RouteRegistry]:
    """Register v2 session routes for testing GET /v2/sessions/{id}."""
    processors = MagicMock(spec=Processors)
    processors.session = session_processors
    adapter = SessionAdapter(processors)
    handler = V2SessionHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_session_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2 client registry authenticated as superadmin."""
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
    """V2 client registry authenticated as a regular (non-admin) user."""
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


class TestSessionGetV2RBAC:
    """RBAC validation for v2 GET /sessions/{session_id}."""

    async def test_regular_user_querying_own_session_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Regular user without an RBAC grant cannot GET their own session."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.session.get(user_session_seed.session_id)

    async def test_superadmin_querying_own_session_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET their own session."""
        result = await admin_v2_registry.session.get(session_seed.session_id)
        assert str(result.id) == str(session_seed.session_id)

    async def test_superadmin_querying_other_users_session_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET other users' sessions."""
        result = await admin_v2_registry.session.get(user_session_seed.session_id)
        assert str(result.id) == str(user_session_seed.session_id)

    async def test_superadmin_querying_nonexistent_session_gets_404(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Superadmin bypasses RBAC but gets 404 for a missing session."""
        with pytest.raises(NotFoundError):
            await admin_v2_registry.session.get(uuid.uuid4())
