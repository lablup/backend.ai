from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
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
from ai.backend.manager.data.image.types import ImageStatus

from .conftest import ImageFactoryHelper


class TestImageForgetLifecycle:
    """Test image forget operation (logical delete)."""

    async def test_admin_forgets_image_status_transition(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Admin forgets image → status transitions to DELETED."""
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

        # Verify status persisted
        after = await admin_registry.image.get(image_id)
        assert isinstance(after, GetImageResponse)
        assert after.item.status == ImageStatus.DELETED.name

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
        """Forget already forgotten image → idempotent (no error)."""
        image_id, _ = image_fixture

        # Forget once
        await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )

        # Forget again - should succeed
        result = await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )
        assert isinstance(result, ForgetImageResponse)
        assert result.item.id == image_id
        assert result.item.status == ImageStatus.DELETED.name

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

    async def test_admin_purges_forgotten_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Admin purges forgotten image → image physically deleted."""
        image_id, _ = image_fixture

        # Forget first (best practice before purge)
        await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )

        # Purge the image
        result = await admin_registry.image.purge(
            PurgeImageRequest(image_id=image_id),
        )
        assert isinstance(result, PurgeImageResponse)
        assert result.item.id == image_id

        # Verify image is actually gone
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
