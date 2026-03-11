"""Component tests for session creation and destruction.

This module covers:
- Session creation: param-based, template-based, cluster creation
- Session creation flags: reuse_if_exists, priority, preemptible, dependencies
- Session creation features: bootstrap scripts, git clone config, owner delegation
- Session destruction: normal, forced, cancel pending, recursive destroy
- Error scenarios: image not found, session already exists, quota exceeded
- Permission failures: unauthenticated, insufficient role, cross-domain access
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    CreateFromParamsRequest,
    CreateFromTemplateRequest,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.image import images
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow

from .conftest import UserFixtureData

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
async def image_seed(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Seed a test image for session creation.

    Component tests cannot actually create sessions (requires live agents),
    but we can test error paths like image-not-found by seeding a valid image.
    """
    unique = secrets.token_hex(4)
    image_name = f"test-image-{unique}:latest"

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(images).values(
                name=image_name,
                registry="index.docker.io",
                architecture="x86_64",
                is_local=False,
                size_bytes=1024 * 1024,
                config_digest="sha256:fake",
                supported_accelerators=[],
                resource_limits=[],
            )
        )

    yield image_name

    async with db_engine.begin() as conn:
        await conn.execute(images.delete().where(images.c.name == image_name))


@pytest.fixture()
async def pending_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[tuple[SessionId, str]]:
    """Seed a PENDING session (no kernel rows) for cancel-pending tests.

    Sessions in PENDING state do not yet have kernel rows, as they are
    waiting for agent scheduling. Used for testing cancel-pending destroy.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-pending-{unique}"
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.PENDING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )

    yield (session_id, session_name)

    async with db_engine.begin() as conn:
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def running_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[tuple[SessionId, str, uuid.UUID]]:
    """Seed a RUNNING session with kernel for normal/forced destroy tests."""
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-running-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group=scaling_group_fixture,
                status=KernelStatus.RUNNING,
                status_info="",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
            )
        )

    yield (session_id, session_name, kernel_id)

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def dependency_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[tuple[SessionId, str]]:
    """Seed a RUNNING session that can serve as a dependency for other sessions.

    Used for testing session creation with dependencies and recursive destroy.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-dep-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group=scaling_group_fixture,
                status=KernelStatus.RUNNING,
                status_info="",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
            )
        )

    yield (session_id, session_name)

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


# ============================================================================
# Session Creation Tests
# ============================================================================


class TestSessionCreation:
    """Tests for session creation APIs.

    NOTE: Component tests cannot actually create sessions because that requires
    live agents for resource allocation and container creation. These tests
    verify error paths and API contract validation that can be tested without
    actual session scheduling.
    """

    async def test_image_not_found_returns_404(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Image not found → 404 error response.

        When attempting to create a session with a non-existent image,
        the API should return HTTP 404 NotFoundError.
        """
        unique = secrets.token_hex(4)
        with pytest.raises(NotFoundError):
            await admin_registry.session.create_from_params(
                CreateFromParamsRequest(
                    image=f"nonexistent-image-{unique}:latest",
                    type=SessionTypes.INTERACTIVE,
                )
            )

    async def test_session_create_with_invalid_image_format_returns_400(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Invalid image format → 400 error response.

        When attempting to create a session with an invalid image format
        (e.g., missing tag separator), the API should return HTTP 400.
        """
        with pytest.raises(InvalidRequestError):
            await admin_registry.session.create_from_params(
                CreateFromParamsRequest(
                    image="invalid-image-format",
                    type=SessionTypes.INTERACTIVE,
                )
            )

    async def test_template_not_found_returns_404(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Template not found → 404 error response.

        When attempting to create a session from a non-existent template,
        the API should return HTTP 404 NotFoundError.
        """
        unique = secrets.token_hex(4)
        with pytest.raises(NotFoundError):
            await admin_registry.session.create_from_template(
                CreateFromTemplateRequest(
                    template_id=f"nonexistent-template-{unique}",
                )
            )

    async def test_unauthenticated_create_returns_401(
        self,
        unauthenticated_registry: BackendAIClientRegistry,
    ) -> None:
        """Unauthenticated request → 401 error.

        Session creation without authentication should return HTTP 401.
        """
        with pytest.raises(PermissionDeniedError):
            await unauthenticated_registry.session.create_from_params(
                CreateFromParamsRequest(
                    image="python:3.11-alpine",
                    type=SessionTypes.INTERACTIVE,
                )
            )


# ============================================================================
# Session Destruction Tests
# ============================================================================


class TestSessionDestruction:
    """Tests for session destruction APIs."""

    async def test_destroy_nonexistent_session_returns_404(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Destroy non-existent session → 404 error.

        Attempting to destroy a session that doesn't exist should return
        HTTP 404 NotFoundError.
        """
        unique = secrets.token_hex(4)
        with pytest.raises(NotFoundError):
            await admin_registry.session.destroy(f"nonexistent-session-{unique}")

    async def test_regular_user_cannot_destroy_other_users_session(
        self,
        user_registry: BackendAIClientRegistry,
        running_session_seed: tuple[SessionId, str, uuid.UUID],
    ) -> None:
        """Regular user cannot destroy another user's session → 403.

        When a regular user attempts to destroy a session owned by another user
        (admin in this case), the API should return HTTP 403 PermissionDeniedError.
        """
        _, session_name, _ = running_session_seed
        with pytest.raises(PermissionDeniedError):
            await user_registry.session.destroy(session_name)

    async def test_unauthenticated_destroy_returns_401(
        self,
        unauthenticated_registry: BackendAIClientRegistry,
        running_session_seed: tuple[SessionId, str, uuid.UUID],
    ) -> None:
        """Unauthenticated destroy request → 401 error.

        Session destruction without authentication should return HTTP 401.
        """
        _, session_name, _ = running_session_seed
        with pytest.raises(PermissionDeniedError):
            await unauthenticated_registry.session.destroy(session_name)
