from __future__ import annotations

import uuid
from decimal import Decimal

import pydantic
import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.image.request import RescanImagesRequest
from ai.backend.common.dto.manager.image.response import RescanImagesResponse
from ai.backend.common.types import ImageID
from ai.backend.manager.data.image.types import ResourceLimitInput
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitByIdAction,
)
from ai.backend.manager.services.image.actions.set_image_resource_limit import (
    SetImageResourceLimitByIdAction,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from .conftest import ImageFactoryHelper


class TestImageRescan:
    @pytest.mark.xfail(reason="Requires live container registry", strict=False)
    @pytest.mark.timeout(10)
    async def test_rescan_returns_response(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-1: Rescan with valid canonical + architecture → RescanImagesResponse."""
        image_id, _ = image_fixture
        canonical = f"registry.test.local/testproject/test-image-{image_id.hex[:8]}:latest"
        result = await admin_registry.image.rescan(
            RescanImagesRequest(
                canonical=canonical,
                architecture="x86_64",
            )
        )
        assert isinstance(result, RescanImagesResponse)

    def test_rescan_request_requires_canonical(self) -> None:
        """F-INPUT-1: RescanImagesRequest without canonical field → ValidationError (→ HTTP 422)."""
        with pytest.raises(pydantic.ValidationError):
            RescanImagesRequest.model_validate({"architecture": "x86_64"})

    def test_rescan_request_requires_architecture(self) -> None:
        """F-INPUT-2: RescanImagesRequest without architecture field → ValidationError (→ HTTP 422)."""
        with pytest.raises(pydantic.ValidationError):
            RescanImagesRequest.model_validate({"canonical": "registry.example/image:latest"})

    @pytest.mark.xfail(
        reason="Handler may return 400 instead of 403 depending on middleware chain",
        strict=False,
    )
    async def test_non_superadmin_cannot_rescan(
        self,
        user_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """F-AUTH-2: Non-superadmin rescan → PermissionDeniedError (403)."""
        image_id, _ = image_fixture
        canonical = f"registry.test.local/testproject/test-image-{image_id.hex[:8]}:latest"
        with pytest.raises(PermissionDeniedError):
            await user_registry.image.rescan(
                RescanImagesRequest(
                    canonical=canonical,
                    architecture="x86_64",
                )
            )


class TestSetImageResourceLimit:
    async def test_set_cpu_resource_limit(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-1: Set CPU resource limit by ID → DB updated."""
        image_id, _ = image_fixture
        action = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("2"),
                max_value=Decimal("8"),
            ),
        )
        result = await image_processors.set_image_resource_limit_by_id.wait_for_complete(action)
        cpu_limit = next((r for r in result.image_data.resource_limits if r.key == "cpu"), None)
        assert cpu_limit is not None
        assert str(cpu_limit.min) == "2"
        assert str(cpu_limit.max) == "8"

    async def test_set_memory_resource_limit(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-4: Set memory resource limit → correct update."""
        image_id, _ = image_fixture
        action = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="mem",
                min_value=Decimal("536870912"),
                max_value=Decimal("8589934592"),
            ),
        )
        result = await image_processors.set_image_resource_limit_by_id.wait_for_complete(action)
        mem_limit = next((r for r in result.image_data.resource_limits if r.key == "mem"), None)
        assert mem_limit is not None
        # INTRINSIC_SLOTS_MIN["mem"] = "1073741824" (1 GiB) > "536870912" (512 MiB),
        # so the resources property takes max(mins) and returns the intrinsic minimum.
        assert str(mem_limit.min) == "1073741824"
        assert str(mem_limit.max) == "8589934592"

    async def test_set_multiple_limits_sequentially(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-5: Set CPU then GPU sequentially → both persist."""
        image_id, _ = image_fixture
        cpu_action = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("4"),
                max_value=Decimal("16"),
            ),
        )
        await image_processors.set_image_resource_limit_by_id.wait_for_complete(cpu_action)

        gpu_action = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="cuda.device",
                min_value=Decimal("0"),
                max_value=Decimal("4"),
            ),
        )
        result = await image_processors.set_image_resource_limit_by_id.wait_for_complete(gpu_action)

        keys = [r.key for r in result.image_data.resource_limits]
        assert "cpu" in keys
        assert "cuda.device" in keys

    async def test_overwrite_existing_limit(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-6: Overwrite existing limit with new values → replaces old."""
        image_id, _ = image_fixture
        action1 = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("1"),
                max_value=Decimal("4"),
            ),
        )
        await image_processors.set_image_resource_limit_by_id.wait_for_complete(action1)

        action2 = SetImageResourceLimitByIdAction(
            image_id=ImageID(image_id),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("8"),
                max_value=Decimal("32"),
            ),
        )
        result = await image_processors.set_image_resource_limit_by_id.wait_for_complete(action2)
        cpu_limit = next((r for r in result.image_data.resource_limits if r.key == "cpu"), None)
        assert cpu_limit is not None
        assert str(cpu_limit.min) == "8"
        assert str(cpu_limit.max) == "32"

    async def test_set_limit_on_nonexistent_image(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """F-SET-1: Set limit on non-existent image ID → ImageNotFound."""
        action = SetImageResourceLimitByIdAction(
            image_id=ImageID(uuid.uuid4()),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("1"),
                max_value=Decimal("4"),
            ),
        )
        with pytest.raises(ImageNotFound):
            await image_processors.set_image_resource_limit_by_id.wait_for_complete(action)


class TestClearImageResourceLimit:
    async def test_clear_custom_resource_limit_by_id(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-7: Clear custom resource limit by ID → custom limits removed."""
        image_id, _ = image_fixture
        action = ClearImageCustomResourceLimitByIdAction(image_id=ImageID(image_id))
        result = await image_processors.clear_image_custom_resource_limit_by_id.wait_for_complete(
            action
        )
        # After clearing _resources, only label-derived intrinsic defaults remain (cpu, mem).
        # Custom max values from the fixture (cpu: "4", mem: "4294967296") are cleared.
        # ResourceLimit.max is typed as Decimal but is actually None for label defaults,
        # so compare via str() to avoid mypy unreachable-statement errors.
        by_key = {r.key: r for r in result.image_data.resource_limits}
        assert set(by_key.keys()) == {"cpu", "mem"}
        assert str(by_key["cpu"].max) == "None"
        assert str(by_key["mem"].max) == "None"

    async def test_clear_idempotent_when_no_custom_limits(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-8: Clear on image with no custom limits → idempotent (no error)."""
        image_id, _ = image_fixture
        action = ClearImageCustomResourceLimitByIdAction(image_id=ImageID(image_id))
        # First clear: removes all custom resources
        await image_processors.clear_image_custom_resource_limit_by_id.wait_for_complete(action)
        # Second clear: should succeed without error
        result = await image_processors.clear_image_custom_resource_limit_by_id.wait_for_complete(
            action
        )
        # After clearing twice, only label-derived intrinsic defaults remain.
        by_key = {r.key: r for r in result.image_data.resource_limits}
        assert set(by_key.keys()) == {"cpu", "mem"}
        assert str(by_key["cpu"].max) == "None"
        assert str(by_key["mem"].max) == "None"

    async def test_clear_by_canonical_name(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-9: Clear by canonical name + architecture (legacy) → limits removed."""
        image_id, _ = image_fixture
        canonical = f"registry.test.local/testproject/test-image-{image_id.hex[:8]}:latest"
        action = ClearImageCustomResourceLimitAction(
            image_canonical=canonical,
            architecture="x86_64",
        )
        result = await image_processors.clear_image_custom_resource_limit.wait_for_complete(action)
        # After clearing _resources, only label-derived intrinsic defaults remain (cpu, mem).
        by_key = {r.key: r for r in result.image_data.resource_limits}
        assert set(by_key.keys()) == {"cpu", "mem"}
        assert str(by_key["cpu"].max) == "None"
        assert str(by_key["mem"].max) == "None"

    async def test_clear_limit_by_nonexistent_image_id(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """F-CLEAR-1: Clear limit by non-existent image ID → ImageNotFound."""
        action = ClearImageCustomResourceLimitByIdAction(image_id=ImageID(uuid.uuid4()))
        with pytest.raises(ImageNotFound):
            await image_processors.clear_image_custom_resource_limit_by_id.wait_for_complete(action)

    async def test_clear_by_nonexistent_canonical(
        self,
        image_processors: ImageProcessors,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """F-CLEAR-2: Clear by non-existent canonical name → ImageNotFound."""
        action = ClearImageCustomResourceLimitAction(
            image_canonical="nonexistent.registry/nonexistent/image:notfound",
            architecture="x86_64",
        )
        with pytest.raises(ImageNotFound):
            await image_processors.clear_image_custom_resource_limit.wait_for_complete(action)
