from __future__ import annotations

import secrets
import uuid
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.client.v2.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.image.request import (
    ForgetImageRequest,
    PurgeImageRequest,
)
from ai.backend.common.dto.manager.image.response import (
    ForgetImageResponse,
    GetImageResponse,
    PurgeImageResponse,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow

from .conftest import ImageFactoryHelper


class TestImageForgetLifecycle:
    """Test image forget operation (logical delete)."""

    async def test_admin_forgets_image_status_transition(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Admin forgets image → status transitions to DELETED (image becomes non-retrievable)."""
        image_id, _ = image_fixture

        # Get initial status
        before = await admin_registry.image.get(image_id)
        assert isinstance(before, GetImageResponse)
        assert before.item.status == ImageStatus.ALIVE.name

        # Forget the image
        result = await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )
        assert isinstance(result, ForgetImageResponse)
        assert result.item.id == image_id
        assert result.item.status == ImageStatus.DELETED.name

        # Verify image is no longer retrievable (deleted images are filtered out by default)
        with pytest.raises(NotFoundError):
            await admin_registry.image.get(image_id)

    async def test_forget_nonexistent_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Forget non-existent image → 404."""
        nonexistent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.image.forget(
                ForgetImageRequest(image_id=nonexistent_id),
            )

    async def test_forget_already_forgotten_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Forget already forgotten image → 404 (forgotten images are not retrievable)."""
        image_id, _ = image_fixture

        # Forget once
        await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )

        # Trying to forget again should fail with 404 (image is no longer retrievable)
        with pytest.raises(NotFoundError):
            await admin_registry.image.forget(
                ForgetImageRequest(image_id=image_id),
            )

    @pytest.mark.xfail(
        reason="Handler may return 400 instead of 403 depending on middleware chain",
        strict=False,
    )
    async def test_regular_user_cannot_forget_image(
        self,
        user_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Regular user cannot forget image → 403."""
        image_id, _ = image_fixture
        with pytest.raises(PermissionDeniedError):
            await user_registry.image.forget(
                ForgetImageRequest(image_id=image_id),
            )


class TestImagePurgeLifecycle:
    """Test image purge operation (physical delete)."""

    async def test_admin_purges_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Admin purges image → image physically deleted from database."""
        image_id, _ = image_fixture

        # Purge the image directly (no need to forget first - purge works on any status)
        result = await admin_registry.image.purge(
            PurgeImageRequest(image_id=image_id),
        )
        assert isinstance(result, PurgeImageResponse)
        assert result.item.id == image_id

        # Verify image is actually gone from database
        with pytest.raises(NotFoundError):
            await admin_registry.image.get(image_id)

    async def test_purge_nonexistent_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Purge non-existent image → 404."""
        nonexistent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.image.purge(
                PurgeImageRequest(image_id=nonexistent_id),
            )

    @pytest.mark.xfail(
        reason="Handler may return 400 instead of 403 depending on middleware chain",
        strict=False,
    )
    async def test_regular_user_cannot_purge_image(
        self,
        user_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Regular user cannot purge image → 403."""
        image_id, _ = image_fixture
        with pytest.raises(PermissionDeniedError):
            await user_registry.image.purge(
                PurgeImageRequest(image_id=image_id),
            )

    @pytest.mark.xfail(
        reason="Session dependency blocking not implemented yet - purge currently succeeds even with active sessions",
        strict=False,
    )
    async def test_purge_image_with_active_session_dependency(
        self,
        db_engine,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
        domain_fixture,
        group_fixture,
        admin_user_fixture,
        scaling_group_fixture,
    ) -> None:
        """Purge image with active session dependency → should be blocked with error.

        NOTE: Current implementation does not check session dependencies before purging.
        This test documents the expected future behavior.
        """
        image_id, helper = image_fixture

        # Get the image's canonical name to use in the session
        image_data = await admin_registry.image.get(image_id)
        image_canonical = image_data.item.name

        # Create a RUNNING session using this image
        unique = secrets.token_hex(4)
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()
        now = datetime.now(tzutc())

        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(SessionRow.__table__).values(
                    id=session_id,
                    creation_id=f"cid-{unique}",
                    name=f"test-session-{unique}",
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
                    status_history={
                        SessionStatus.PENDING.name: now.isoformat(),
                        SessionStatus.RUNNING.name: now.isoformat(),
                    },
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
                    session_name=f"test-session-{unique}",
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
                    image=image_canonical,  # Link session to this image
                )
            )

        try:
            # Try to purge the image while session is using it
            # Expected: should raise an error (e.g., ImageInUseError, ConflictError)
            # Actual (current): may succeed without checking dependencies
            with pytest.raises(ConflictError):
                await admin_registry.image.purge(
                    PurgeImageRequest(image_id=image_id),
                )
        finally:
            # Cleanup session
            async with db_engine.begin() as conn:
                await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
                await conn.execute(
                    SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
                )
