from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.repositories.session.admin_repository import AdminSessionRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs


@pytest.fixture
async def processors(
    extra_fixtures,
    database_fixture,
    database_engine,
    registry_ctx,
) -> SessionProcessors:
    agent_registry, _, _, _, _, _, _ = registry_ctx

    # Create REAL SessionRepository and AdminSessionRepository with database fixture
    session_repository = SessionRepository(database_engine)
    admin_session_repository = AdminSessionRepository(database_engine)

    # Use minimal mocked dependencies to avoid timeout
    background_task_manager = AsyncMock()
    idle_checker_host = AsyncMock()
    error_monitor = AsyncMock()

    # Create real SessionService with real repositories
    session_service = SessionService(
        SessionServiceArgs(
            agent_registry=agent_registry,
            event_fetcher=AsyncMock(),
            background_task_manager=background_task_manager,
            event_hub=AsyncMock(),
            error_monitor=error_monitor,
            idle_checker_host=idle_checker_host,
            session_repository=session_repository,
            admin_session_repository=admin_session_repository,
            scheduling_controller=AsyncMock(),
        )
    )

    # Create real SessionProcessors with real service
    return SessionProcessors(session_service, [])


@pytest.fixture
def session_repository(database_engine) -> SessionRepository:
    return SessionRepository(database_engine)


@pytest.fixture
def admin_session_repository(database_engine) -> AdminSessionRepository:
    return AdminSessionRepository(database_engine)
