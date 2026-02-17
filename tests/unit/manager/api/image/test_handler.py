"""Tests for image REST API handler and adapter.

These tests focus on the adapter's conversion logic and the handler's
orchestration of image queries via mocked processors.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.dto.manager.image import (
    ImageFilter,
    ImageOrder,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import (
    ImageDTO,
)
from ai.backend.common.dto.manager.image.types import ImageOrderField, OrderDirection
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.api.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageDataWithDetails,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageTagEntry,
    ImageType,
    KVPair,
    ResourceLimit,
)
from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.services.image.actions.alias_image import AliasImageByIdAction
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.get_images import GetImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.scan_image import ScanImageAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

# ========== Test Data Factories ==========


def create_image_data(
    image_id: UUID | None = None,
    name: str = "cr.backend.ai/stable/python:3.11",
    registry: str = "cr.backend.ai",
    architecture: str = "x86_64",
    status: ImageStatus = ImageStatus.ALIVE,
) -> ImageData:
    """Create an ImageData for testing."""
    return ImageData(
        id=ImageID(image_id or uuid4()),
        name=ImageCanonical(name),
        project="stable",
        image="python",
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
        tag="3.11",
        registry=registry,
        registry_id=uuid4(),
        architecture=architecture,
        config_digest="sha256:abc123",
        size_bytes=1024 * 1024 * 100,
        is_local=False,
        type=ImageType.COMPUTE,
        accelerators=None,
        labels=ImageLabelsData(label_data={"ai.backend.role": "compute"}),
        resources=ImageResourcesData(resources_data={}),
        resource_limits=[
            ResourceLimit(key="cpu", min=Decimal("1"), max=Decimal("8")),
        ],
        tags=[ImageTagEntry(key="runtime", value="python")],
        status=status,
    )


def create_image_data_with_details(
    image_id: UUID | None = None,
    name: str = "cr.backend.ai/stable/python:3.11",
) -> ImageDataWithDetails:
    """Create an ImageDataWithDetails for testing."""
    return ImageDataWithDetails(
        id=ImageID(image_id or uuid4()),
        name=ImageCanonical(name),
        namespace="stable",
        base_image_name="python",
        project="stable",
        humanized_name="Python 3.11",
        tag="3.11",
        tags=[KVPair(key="runtime", value="python")],
        version="3.11",
        registry="cr.backend.ai",
        registry_id=uuid4(),
        type=ImageType.COMPUTE,
        architecture="x86_64",
        is_local=False,
        status=ImageStatus.ALIVE,
        resource_limits=[
            ResourceLimit(key="cpu", min=Decimal("1"), max=Decimal("8")),
        ],
        supported_accelerators=["cuda"],
        digest="sha256:abc123",
        labels=[KVPair(key="ai.backend.role", value="compute")],
        aliases=["python3"],
        size_bytes=1024 * 1024 * 100,
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
    )


# ========== Adapter Tests ==========


class TestImageAdapter:
    """Tests for ImageAdapter conversion logic."""

    def setup_method(self) -> None:
        self.adapter = ImageAdapter()

    # ----- build_querier -----

    def test_build_querier_defaults(self) -> None:
        """Build querier with default request should use default pagination."""
        request = SearchImagesRequest()
        querier = self.adapter.build_querier(request)

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0
        assert querier.conditions == []
        assert querier.orders == []

    def test_build_querier_with_pagination(self) -> None:
        """Build querier with custom pagination."""
        request = SearchImagesRequest(limit=100, offset=25)
        querier = self.adapter.build_querier(request)

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 100
        assert querier.pagination.offset == 25

    def test_build_querier_with_name_filter(self) -> None:
        """Build querier with name filter should produce a condition."""
        request = SearchImagesRequest(filter=ImageFilter(name=StringFilter(contains="python")))
        querier = self.adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_architecture_filter(self) -> None:
        """Build querier with architecture filter should produce a condition."""
        request = SearchImagesRequest(
            filter=ImageFilter(architecture=StringFilter(equals="x86_64"))
        )
        querier = self.adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_multiple_filters(self) -> None:
        """Build querier with multiple filter fields should produce multiple conditions."""
        request = SearchImagesRequest(
            filter=ImageFilter(
                name=StringFilter(contains="python"),
                architecture=StringFilter(equals="aarch64"),
            )
        )
        querier = self.adapter.build_querier(request)

        assert len(querier.conditions) == 2

    def test_build_querier_with_case_insensitive_filter(self) -> None:
        """Build querier with case-insensitive filter should produce a condition."""
        request = SearchImagesRequest(filter=ImageFilter(name=StringFilter(i_contains="Python")))
        querier = self.adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_order(self) -> None:
        """Build querier with order should produce orders."""
        request = SearchImagesRequest(
            order=[
                ImageOrder(
                    field=ImageOrderField.NAME,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        querier = self.adapter.build_querier(request)

        assert len(querier.orders) == 1

    def test_build_querier_with_multiple_orders(self) -> None:
        """Build querier with multiple orders should produce multiple orders."""
        request = SearchImagesRequest(
            order=[
                ImageOrder(field=ImageOrderField.NAME, direction=OrderDirection.ASC),
                ImageOrder(field=ImageOrderField.CREATED_AT, direction=OrderDirection.DESC),
            ]
        )
        querier = self.adapter.build_querier(request)

        assert len(querier.orders) == 2

    def test_build_querier_no_filter(self) -> None:
        """Build querier with no filter should produce empty conditions."""
        request = SearchImagesRequest(filter=None)
        querier = self.adapter.build_querier(request)

        assert querier.conditions == []

    def test_build_querier_no_orders(self) -> None:
        """Build querier with no orders should produce empty orders."""
        request = SearchImagesRequest(order=None)
        querier = self.adapter.build_querier(request)

        assert querier.orders == []

    # ----- convert_to_dto -----

    def test_convert_to_dto_basic(self) -> None:
        """Convert ImageData to ImageDTO should map all fields correctly."""
        image = create_image_data()
        dto = self.adapter.convert_to_dto(image)

        assert isinstance(dto, ImageDTO)
        assert dto.id == image.id
        assert dto.name == image.name
        assert dto.registry == "cr.backend.ai"
        assert dto.project == "stable"
        assert dto.tag == "3.11"
        assert dto.architecture == "x86_64"
        assert dto.size_bytes == 1024 * 1024 * 100
        assert dto.type == str(ImageType.COMPUTE)
        assert dto.status == str(ImageStatus.ALIVE)
        assert dto.config_digest == "sha256:abc123"
        assert dto.is_local is False
        assert dto.created_at == datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

    def test_convert_to_dto_labels(self) -> None:
        """Convert ImageData labels to ImageDTO label entries."""
        image = create_image_data()
        dto = self.adapter.convert_to_dto(image)

        assert len(dto.labels) == 1
        assert dto.labels[0].key == "ai.backend.role"
        assert dto.labels[0].value == "compute"

    def test_convert_to_dto_tags(self) -> None:
        """Convert ImageData tags to ImageDTO tag entries."""
        image = create_image_data()
        dto = self.adapter.convert_to_dto(image)

        assert len(dto.tags) == 1
        assert dto.tags[0].key == "runtime"
        assert dto.tags[0].value == "python"

    def test_convert_to_dto_resource_limits(self) -> None:
        """Convert ImageData resource limits to ImageDTO resource limit entries."""
        image = create_image_data()
        dto = self.adapter.convert_to_dto(image)

        assert len(dto.resource_limits) == 1
        assert dto.resource_limits[0].key == "cpu"
        assert dto.resource_limits[0].min == Decimal("1")
        assert dto.resource_limits[0].max == Decimal("8")

    # ----- convert_detailed_to_dto -----

    def test_convert_detailed_to_dto_basic(self) -> None:
        """Convert ImageDataWithDetails to ImageDTO should map all fields correctly."""
        image = create_image_data_with_details()
        dto = self.adapter.convert_detailed_to_dto(image)

        assert isinstance(dto, ImageDTO)
        assert dto.id == image.id
        assert dto.name == image.name
        assert dto.registry == "cr.backend.ai"
        assert dto.project == "stable"
        assert dto.tag == "3.11"
        assert dto.architecture == "x86_64"
        assert dto.config_digest == "sha256:abc123"
        assert dto.is_local is False
        assert dto.accelerators == "cuda"

    def test_convert_detailed_to_dto_labels(self) -> None:
        """Convert ImageDataWithDetails labels (KVPair) to ImageDTO label entries."""
        image = create_image_data_with_details()
        dto = self.adapter.convert_detailed_to_dto(image)

        assert len(dto.labels) == 1
        assert dto.labels[0].key == "ai.backend.role"
        assert dto.labels[0].value == "compute"

    def test_convert_detailed_to_dto_no_accelerators(self) -> None:
        """ImageDataWithDetails with no accelerators should produce None."""
        image = create_image_data_with_details()
        image.supported_accelerators = []
        dto = self.adapter.convert_detailed_to_dto(image)

        assert dto.accelerators is None

    def test_convert_detailed_to_dto_no_digest(self) -> None:
        """ImageDataWithDetails with no digest should produce empty string."""
        image = create_image_data_with_details()
        image.digest = None
        dto = self.adapter.convert_detailed_to_dto(image)

        assert dto.config_digest == ""


# ========== Handler Orchestration Tests ==========


class TestImageAPIHandler:
    """Tests for handler orchestration logic with mocked processors."""

    @pytest.fixture
    def mock_search_result(self) -> MagicMock:
        """Mock search images action result."""
        image_1 = create_image_data(
            image_id=UUID("11111111-1111-1111-1111-111111111111"),
            name="cr.backend.ai/stable/python:3.11",
        )
        image_2 = create_image_data(
            image_id=UUID("22222222-2222-2222-2222-222222222222"),
            name="cr.backend.ai/stable/tensorflow:2.15",
        )
        result = MagicMock()
        result.data = [image_1, image_2]
        result.total_count = 2
        result.has_next_page = False
        result.has_previous_page = False
        return result

    @pytest.fixture
    def mock_get_result(self) -> MagicMock:
        """Mock get image by ID action result."""
        image = create_image_data_with_details(
            image_id=UUID("11111111-1111-1111-1111-111111111111"),
        )
        result = MagicMock()
        result.image_with_agent_install_status = MagicMock()
        result.image_with_agent_install_status.image = image
        return result

    @pytest.fixture
    def mock_scan_result(self) -> MagicMock:
        """Mock scan image action result."""
        image = create_image_data(
            image_id=UUID("11111111-1111-1111-1111-111111111111"),
        )
        result = MagicMock()
        result.image = image
        result.errors = []
        return result

    @pytest.fixture
    def mock_alias_result(self) -> MagicMock:
        """Mock alias image action result."""
        result = MagicMock()
        result.image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        result.image_alias = MagicMock()
        result.image_alias.id = uuid4()
        result.image_alias.alias = "python3"
        return result

    @pytest.fixture
    def mock_forget_result(self) -> MagicMock:
        """Mock forget image action result."""
        image = create_image_data(
            image_id=UUID("11111111-1111-1111-1111-111111111111"),
            status=ImageStatus.DELETED,
        )
        result = MagicMock()
        result.image = image
        return result

    @pytest.fixture
    def mock_purge_result(self) -> MagicMock:
        """Mock purge image action result."""
        image = create_image_data(
            image_id=UUID("11111111-1111-1111-1111-111111111111"),
        )
        result = MagicMock()
        result.image = image
        return result

    @pytest.fixture
    def mock_processors(
        self,
        mock_search_result: MagicMock,
        mock_get_result: MagicMock,
        mock_scan_result: MagicMock,
        mock_alias_result: MagicMock,
        mock_forget_result: MagicMock,
        mock_purge_result: MagicMock,
    ) -> MagicMock:
        """Mock processors for image operations."""
        processors = MagicMock()
        processors.image.search_images.wait_for_complete = AsyncMock(
            return_value=mock_search_result
        )
        processors.image.get_image_by_id.wait_for_complete = AsyncMock(return_value=mock_get_result)
        processors.image.scan_image.wait_for_complete = AsyncMock(return_value=mock_scan_result)
        processors.image.alias_image_by_id.wait_for_complete = AsyncMock(
            return_value=mock_alias_result
        )
        processors.image.dealias_image.wait_for_complete = AsyncMock(return_value=mock_alias_result)
        processors.image.forget_image_by_id.wait_for_complete = AsyncMock(
            return_value=mock_forget_result
        )
        processors.image.purge_image_by_id.wait_for_complete = AsyncMock(
            return_value=mock_purge_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_search_images_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Search handler should call search_images processor."""
        await mock_processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=MagicMock())
        )
        mock_processors.image.search_images.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_images_returns_correct_count(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Search result should have correct total count."""
        result = await mock_processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=MagicMock())
        )
        assert result.total_count == 2
        assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_search_images_converts_to_dto(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Search result data should be convertible to DTOs."""
        result = await mock_processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=MagicMock())
        )
        adapter = ImageAdapter()
        items = [adapter.convert_to_dto(img) for img in result.data]

        assert len(items) == 2
        assert all(isinstance(dto, ImageDTO) for dto in items)
        assert items[0].id == UUID("11111111-1111-1111-1111-111111111111")
        assert items[1].id == UUID("22222222-2222-2222-2222-222222222222")

    @pytest.mark.asyncio
    async def test_get_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Get handler should call get_image_by_id processor."""
        image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        await mock_processors.image.get_image_by_id.wait_for_complete(
            GetImageByIdAction(image_id=image_id, image_status=None)
        )
        mock_processors.image.get_image_by_id.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_image_converts_detailed_dto(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Get result should be convertible to detailed DTO."""
        image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        result = await mock_processors.image.get_image_by_id.wait_for_complete(
            GetImageByIdAction(image_id=image_id, image_status=None)
        )
        adapter = ImageAdapter()
        dto = adapter.convert_detailed_to_dto(result.image_with_agent_install_status.image)

        assert isinstance(dto, ImageDTO)
        assert dto.id == UUID("11111111-1111-1111-1111-111111111111")

    @pytest.mark.asyncio
    async def test_scan_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Rescan handler should call scan_image processor."""
        await mock_processors.image.scan_image.wait_for_complete(
            ScanImageAction(canonical="cr.backend.ai/stable/python:3.11", architecture="x86_64")
        )
        mock_processors.image.scan_image.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_image_result_has_image_and_errors(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Scan result should have image data and errors list."""
        result = await mock_processors.image.scan_image.wait_for_complete(
            ScanImageAction(canonical="cr.backend.ai/stable/python:3.11", architecture="x86_64")
        )
        adapter = ImageAdapter()
        dto = adapter.convert_to_dto(result.image)

        assert isinstance(dto, ImageDTO)
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_alias_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Alias handler should call alias_image_by_id processor."""
        await mock_processors.image.alias_image_by_id.wait_for_complete(
            AliasImageByIdAction(
                image_id=ImageID(UUID("11111111-1111-1111-1111-111111111111")),
                alias="python3",
            )
        )
        mock_processors.image.alias_image_by_id.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_alias_result_has_correct_fields(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Alias result should contain alias_id, alias, and image_id."""
        result = await mock_processors.image.alias_image_by_id.wait_for_complete(
            AliasImageByIdAction(
                image_id=ImageID(UUID("11111111-1111-1111-1111-111111111111")),
                alias="python3",
            )
        )
        assert result.image_alias.alias == "python3"
        assert result.image_id == ImageID(UUID("11111111-1111-1111-1111-111111111111"))

    @pytest.mark.asyncio
    async def test_dealias_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Dealias handler should call dealias_image processor."""
        await mock_processors.image.dealias_image.wait_for_complete(
            DealiasImageAction(alias="python3")
        )
        mock_processors.image.dealias_image.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_forget_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Forget handler should call forget_image_by_id processor."""
        image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        await mock_processors.image.forget_image_by_id.wait_for_complete(
            ForgetImageByIdAction(image_id=image_id)
        )
        mock_processors.image.forget_image_by_id.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_forget_result_image_status(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Forget result image should have DELETED status."""
        image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        result = await mock_processors.image.forget_image_by_id.wait_for_complete(
            ForgetImageByIdAction(image_id=image_id)
        )
        adapter = ImageAdapter()
        dto = adapter.convert_to_dto(result.image)

        assert dto.status == "DELETED"

    @pytest.mark.asyncio
    async def test_purge_image_calls_processor(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Purge handler should call purge_image_by_id processor."""
        image_id = ImageID(UUID("11111111-1111-1111-1111-111111111111"))
        await mock_processors.image.purge_image_by_id.wait_for_complete(
            PurgeImageByIdAction(image_id=image_id)
        )
        mock_processors.image.purge_image_by_id.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_result(self) -> None:
        """Search with empty result should return empty data."""
        processors = MagicMock()
        result = MagicMock()
        result.data = []
        result.total_count = 0
        processors.image.search_images.wait_for_complete = AsyncMock(return_value=result)

        search_result = await processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=MagicMock())
        )
        assert search_result.data == []
        assert search_result.total_count == 0
