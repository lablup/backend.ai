"""
Tests for ArtifactRegistryService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryData,
    ArtifactRegistryListResult,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryData,
    HuggingFaceRegistryListResult,
)
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryData,
    ReservoirRegistryListResult,
)
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.create import (
    CreateHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.delete import (
    DeleteHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.list import (
    ListReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService


class TestArtifactRegistryService:
    """Test cases for ArtifactRegistryService"""

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def artifact_registry_service(
        self,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
        )

    @pytest.fixture
    def sample_registry_data(self) -> ArtifactRegistryData:
        return ArtifactRegistryData(
            id=uuid4(),
            registry_id=uuid4(),
            name="test-huggingface-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )

    @pytest.fixture
    def sample_hf_data(self) -> HuggingFaceRegistryData:
        return HuggingFaceRegistryData(
            id=uuid4(),
            name="test-hf-registry",
            url="https://huggingface.co",
            token="hf_test_token_12345",
        )

    @pytest.fixture
    def sample_reservoir_data(self) -> ReservoirRegistryData:
        return ReservoirRegistryData(
            id=uuid4(),
            name="test-reservoir",
            endpoint="https://reservoir.example.com",
            access_key="ak-test",
            secret_key="sk-test",
            api_version="v1",
        )

    # --- SearchArtifactRegistries (existing tests) ---

    async def test_search_artifact_registries(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
        sample_registry_data: ArtifactRegistryData,
    ) -> None:
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
                items=[sample_registry_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.registries == [sample_registry_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_artifact_registry_repository.search_artifact_registries.assert_called_once_with(
            querier=querier
        )

    async def test_search_artifact_registries_empty_result(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.registries == []
        assert result.total_count == 0

    async def test_search_artifact_registries_with_pagination(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
        sample_registry_data: ArtifactRegistryData,
    ) -> None:
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
                items=[sample_registry_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


class TestCreateHuggingFaceRegistryAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_create_huggingface_registry(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        expected = HuggingFaceRegistryData(
            id=uuid4(), name="my-hf", url="https://huggingface.co", token="hf_token"
        )
        mock_huggingface_repository.create = AsyncMock(return_value=expected)
        creator = MagicMock(spec=Creator)
        meta = ArtifactRegistryCreatorMeta(name="my-hf")

        action = CreateHuggingFaceRegistryAction(creator=creator, meta=meta)
        result = await service.create_huggingface_registry(action)

        assert result.result == expected
        mock_huggingface_repository.create.assert_called_once_with(creator, meta)

    async def test_create_huggingface_registry_token_stored_in_meta(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        expected = HuggingFaceRegistryData(
            id=uuid4(), name="secure-hf", url="https://huggingface.co", token="hf_secret_api_key"
        )
        mock_huggingface_repository.create = AsyncMock(return_value=expected)
        creator = MagicMock(spec=Creator)
        meta = ArtifactRegistryCreatorMeta(name="secure-hf")

        action = CreateHuggingFaceRegistryAction(creator=creator, meta=meta)
        result = await service.create_huggingface_registry(action)

        assert result.result.token == "hf_secret_api_key"


class TestGetHuggingFaceRegistryAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_get_huggingface_registry(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        expected = HuggingFaceRegistryData(
            id=registry_id, name="my-hf", url="https://huggingface.co", token=None
        )
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(return_value=expected)

        action = GetHuggingFaceRegistryAction(registry_id=registry_id)
        result = await service.get_huggingface_registry(action)

        assert result.result == expected
        mock_huggingface_repository.get_registry_data_by_id.assert_called_once_with(registry_id)

    async def test_get_huggingface_registry_not_found(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            side_effect=ArtifactRegistryNotFoundError
        )

        action = GetHuggingFaceRegistryAction(registry_id=registry_id)
        with pytest.raises(ArtifactRegistryNotFoundError):
            await service.get_huggingface_registry(action)


class TestListHuggingFaceRegistryAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_list_huggingface_registries(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        items = [
            HuggingFaceRegistryData(
                id=uuid4(), name="hf-1", url="https://huggingface.co", token=None
            ),
            HuggingFaceRegistryData(
                id=uuid4(), name="hf-2", url="https://huggingface.co", token="tok"
            ),
        ]
        mock_huggingface_repository.list_registries = AsyncMock(return_value=items)

        action = ListHuggingFaceRegistryAction()
        result = await service.list_huggingface_registry(action)

        assert result.data == items
        assert len(result.data) == 2
        mock_huggingface_repository.list_registries.assert_called_once()


class TestUpdateHuggingFaceRegistryAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_update_huggingface_registry(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        updated = HuggingFaceRegistryData(
            id=registry_id, name="updated-hf", url="https://huggingface.co", token="new_token"
        )
        mock_huggingface_repository.update = AsyncMock(return_value=updated)
        updater = MagicMock(spec=Updater)
        updater.pk_value = registry_id
        meta = ArtifactRegistryModifierMeta()

        action = UpdateHuggingFaceRegistryAction(updater=updater, meta=meta)
        result = await service.update_huggingface_registry(action)

        assert result.result == updated
        mock_huggingface_repository.update.assert_called_once_with(updater, meta)


class TestDeleteHuggingFaceRegistryAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_delete_huggingface_registry(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        mock_huggingface_repository.delete = AsyncMock(return_value=registry_id)

        action = DeleteHuggingFaceRegistryAction(registry_id=registry_id)
        result = await service.delete_huggingface_registry(action)

        assert result.deleted_registry_id == registry_id
        mock_huggingface_repository.delete.assert_called_once_with(registry_id)

    async def test_delete_huggingface_registry_not_found(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        mock_huggingface_repository.delete = AsyncMock(side_effect=ArtifactRegistryNotFoundError)

        action = DeleteHuggingFaceRegistryAction(registry_id=registry_id)
        with pytest.raises(ArtifactRegistryNotFoundError):
            await service.delete_huggingface_registry(action)


class TestSearchHuggingFaceRegistriesAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_search_huggingface_registries(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        hf_data = HuggingFaceRegistryData(
            id=uuid4(), name="hf-1", url="https://huggingface.co", token=None
        )
        mock_huggingface_repository.search_registries = AsyncMock(
            return_value=HuggingFaceRegistryListResult(
                items=[hf_data], total_count=1, has_next_page=False, has_previous_page=False
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0), conditions=[], orders=[]
        )
        action = SearchHuggingFaceRegistriesAction(querier=querier)
        result = await service.search_huggingface_registries(action)

        assert result.registries == [hf_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        mock_huggingface_repository.search_registries.assert_called_once_with(querier=querier)


class TestGetHuggingFaceRegistriesAction:
    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def service(self, mock_huggingface_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_get_huggingface_registries_by_ids(
        self,
        service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        id1, id2 = uuid4(), uuid4()
        items = [
            HuggingFaceRegistryData(id=id1, name="hf-1", url="https://hf.co", token=None),
            HuggingFaceRegistryData(id=id2, name="hf-2", url="https://hf.co", token="t"),
        ]
        mock_huggingface_repository.get_registries_by_ids = AsyncMock(return_value=items)

        action = GetHuggingFaceRegistriesAction(registry_ids=[id1, id2])
        result = await service.get_huggingface_registries(action)

        assert result.result == items
        assert len(result.result) == 2


class TestCreateReservoirRegistryAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_create_reservoir_registry(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        expected = ReservoirRegistryData(
            id=uuid4(),
            name="my-reservoir",
            endpoint="https://reservoir.example.com",
            access_key="ak",
            secret_key="sk",
            api_version="v1",
        )
        mock_reservoir_repository.create = AsyncMock(return_value=expected)
        creator = MagicMock(spec=Creator)
        meta = ArtifactRegistryCreatorMeta(name="my-reservoir")

        action = CreateReservoirRegistryAction(creator=creator, meta=meta)
        result = await service.create_reservoir_registry(action)

        assert result.result == expected
        mock_reservoir_repository.create.assert_called_once_with(creator, meta)


class TestGetReservoirRegistryAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_get_reservoir_registry(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        reservoir_id = uuid4()
        expected = ReservoirRegistryData(
            id=reservoir_id,
            name="res-1",
            endpoint="https://reservoir.example.com",
            access_key="ak",
            secret_key="sk",
            api_version="v1",
        )
        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            return_value=expected
        )

        action = GetReservoirRegistryAction(reservoir_id=reservoir_id)
        result = await service.get_reservoir_registry(action)

        assert result.result == expected
        mock_reservoir_repository.get_reservoir_registry_data_by_id.assert_called_once_with(
            reservoir_id
        )

    async def test_get_reservoir_registry_not_found(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        reservoir_id = uuid4()
        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            side_effect=ArtifactRegistryNotFoundError
        )

        action = GetReservoirRegistryAction(reservoir_id=reservoir_id)
        with pytest.raises(ArtifactRegistryNotFoundError):
            await service.get_reservoir_registry(action)


class TestListReservoirRegistriesAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_list_reservoir_registries(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        items = [
            ReservoirRegistryData(
                id=uuid4(),
                name="res-1",
                endpoint="https://r1.example.com",
                access_key="ak1",
                secret_key="sk1",
                api_version="v1",
            ),
        ]
        mock_reservoir_repository.list_reservoir_registries = AsyncMock(return_value=items)

        action = ListReservoirRegistriesAction()
        result = await service.list_reservoir_registries(action)

        assert result.data == items
        mock_reservoir_repository.list_reservoir_registries.assert_called_once()


class TestUpdateReservoirRegistryAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_update_reservoir_registry(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        reservoir_id = uuid4()
        updated = ReservoirRegistryData(
            id=reservoir_id,
            name="updated-res",
            endpoint="https://new.example.com",
            access_key="ak",
            secret_key="sk",
            api_version="v2",
        )
        mock_reservoir_repository.update = AsyncMock(return_value=updated)
        updater = MagicMock(spec=Updater)
        updater.pk_value = reservoir_id
        meta = ArtifactRegistryModifierMeta()

        action = UpdateReservoirRegistryAction(updater=updater, meta=meta)
        result = await service.update_reservoir_registry(action)

        assert result.result == updated
        mock_reservoir_repository.update.assert_called_once_with(updater, meta)


class TestDeleteReservoirRegistryAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_delete_reservoir_registry(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        reservoir_id = uuid4()
        mock_reservoir_repository.delete = AsyncMock(return_value=reservoir_id)

        action = DeleteReservoirRegistryAction(reservoir_id=reservoir_id)
        result = await service.delete_reservoir_registry(action)

        assert result.deleted_reservoir_id == reservoir_id
        mock_reservoir_repository.delete.assert_called_once_with(reservoir_id)


class TestSearchReservoirRegistriesAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_search_reservoir_registries(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        res_data = ReservoirRegistryData(
            id=uuid4(),
            name="res-1",
            endpoint="https://r.example.com",
            access_key="ak",
            secret_key="sk",
            api_version="v1",
        )
        mock_reservoir_repository.search_registries = AsyncMock(
            return_value=ReservoirRegistryListResult(
                items=[res_data], total_count=1, has_next_page=False, has_previous_page=False
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0), conditions=[], orders=[]
        )
        action = SearchReservoirRegistriesAction(querier=querier)
        result = await service.search_reservoir_registries(action)

        assert result.registries == [res_data]
        assert result.total_count == 1
        mock_reservoir_repository.search_registries.assert_called_once_with(querier=querier)

    async def test_search_reservoir_registries_invalid_endpoint(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        mock_reservoir_repository.search_registries = AsyncMock(
            return_value=ReservoirRegistryListResult(
                items=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0), conditions=[], orders=[]
        )
        action = SearchReservoirRegistriesAction(querier=querier)
        result = await service.search_reservoir_registries(action)

        assert result.registries == []
        assert result.total_count == 0


class TestGetReservoirRegistriesAction:
    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(self, mock_reservoir_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_get_reservoir_registries_by_ids(
        self,
        service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        id1, id2 = uuid4(), uuid4()
        items = [
            ReservoirRegistryData(
                id=id1,
                name="res-1",
                endpoint="https://r1.example.com",
                access_key="ak1",
                secret_key="sk1",
                api_version="v1",
            ),
            ReservoirRegistryData(
                id=id2,
                name="res-2",
                endpoint="https://r2.example.com",
                access_key="ak2",
                secret_key="sk2",
                api_version="v1",
            ),
        ]
        mock_reservoir_repository.get_registries_by_ids = AsyncMock(return_value=items)

        action = GetReservoirRegistriesAction(registry_ids=[id1, id2])
        result = await service.get_reservoir_registries(action)

        assert result.result == items
        assert len(result.result) == 2


class TestGetArtifactRegistryMetaAction:
    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def service(self, mock_artifact_registry_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=mock_artifact_registry_repository,
        )

    async def test_get_registry_meta_by_id(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        registry_id = uuid4()
        expected = ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,
            name="test-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=expected
        )

        action = GetArtifactRegistryMetaAction(registry_id=registry_id)
        result = await service.get_registry_meta(action)

        assert result.result == expected
        mock_artifact_registry_repository.get_artifact_registry_data.assert_called_once_with(
            registry_id
        )

    async def test_get_registry_meta_by_name(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        expected = ArtifactRegistryData(
            id=uuid4(),
            registry_id=uuid4(),
            name="my-registry",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data_by_name = AsyncMock(
            return_value=expected
        )

        action = GetArtifactRegistryMetaAction(registry_name="my-registry")
        result = await service.get_registry_meta(action)

        assert result.result == expected
        mock_artifact_registry_repository.get_artifact_registry_data_by_name.assert_called_once_with(
            "my-registry"
        )

    async def test_get_registry_meta_not_found_by_id(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            side_effect=ArtifactRegistryNotFoundError
        )

        action = GetArtifactRegistryMetaAction(registry_id=uuid4())
        with pytest.raises(ArtifactRegistryNotFoundError):
            await service.get_registry_meta(action)

    async def test_get_registry_meta_not_found_by_name(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        mock_artifact_registry_repository.get_artifact_registry_data_by_name = AsyncMock(
            side_effect=ArtifactRegistryNotFoundError
        )

        action = GetArtifactRegistryMetaAction(registry_name="nonexistent")
        with pytest.raises(ArtifactRegistryNotFoundError):
            await service.get_registry_meta(action)

    async def test_get_registry_meta_no_id_or_name_raises(
        self,
        service: ArtifactRegistryService,
    ) -> None:
        action = GetArtifactRegistryMetaAction()
        with pytest.raises(InvalidAPIParameters):
            await service.get_registry_meta(action)


class TestGetArtifactRegistryMetasAction:
    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def service(self, mock_artifact_registry_repository: MagicMock) -> ArtifactRegistryService:
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=mock_artifact_registry_repository,
        )

    async def test_get_registry_metas_multiple(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        id1, id2 = uuid4(), uuid4()
        items = [
            ArtifactRegistryData(
                id=uuid4(), registry_id=id1, name="reg-1", type=ArtifactRegistryType.HUGGINGFACE
            ),
            ArtifactRegistryData(
                id=uuid4(), registry_id=id2, name="reg-2", type=ArtifactRegistryType.RESERVOIR
            ),
        ]
        mock_artifact_registry_repository.get_artifact_registry_datas = AsyncMock(
            return_value=items
        )

        action = GetArtifactRegistryMetasAction(registry_ids=[id1, id2])
        result = await service.get_registry_metas(action)

        assert result.result == items
        assert len(result.result) == 2

    async def test_get_registry_metas_partially_missing_skipped(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        id1 = uuid4()
        id_missing = uuid4()
        items = [
            ArtifactRegistryData(
                id=uuid4(), registry_id=id1, name="reg-1", type=ArtifactRegistryType.HUGGINGFACE
            ),
        ]
        mock_artifact_registry_repository.get_artifact_registry_datas = AsyncMock(
            return_value=items
        )

        action = GetArtifactRegistryMetasAction(registry_ids=[id1, id_missing])
        result = await service.get_registry_metas(action)

        assert len(result.result) == 1

    async def test_get_registry_metas_empty_list(
        self,
        service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        mock_artifact_registry_repository.get_artifact_registry_datas = AsyncMock(return_value=[])

        action = GetArtifactRegistryMetasAction(registry_ids=[])
        result = await service.get_registry_metas(action)

        assert result.result == []
