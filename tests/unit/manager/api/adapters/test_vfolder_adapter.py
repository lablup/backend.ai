"""Unit tests for v2 VFolderAdapter."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.common.dto.manager.v2.vfolder.request import (
    SearchVFoldersInput,
    VFolderFilter,
)
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderUsageData,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.vfolder.actions.get_usage import (
    GetVFolderUsageActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_in_project import (
    SearchVFoldersInProjectActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_user_vfolders import (
    SearchUserVFoldersActionResult,
)


class TestVFolderAdapterMySearch:
    """Tests for VFolderAdapter.my_search()."""

    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture
    def vfolder_data(self) -> VFolderData:
        return VFolderData(
            id=VFolderUUID(uuid4()),
            name="test-vfolder",
            host="local:volume1",
            quota_scope_id=QuotaScopeID.parse(f"user:{uuid4()}"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            creator="test@example.com",
            creator_id=uuid4(),
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=uuid4(),
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
            created_at=datetime.now(tz=UTC),
            last_used=None,
            updated_at=datetime.now(tz=UTC),
            domain_name="default",
        )

    @pytest.fixture
    def mock_processors(self, vfolder_data: VFolderData) -> MagicMock:
        processors = MagicMock()
        result = SearchUserVFoldersActionResult(
            user_id=uuid4(),
            data=[vfolder_data],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        processors.vfolder.search_user_vfolders.wait_for_complete = AsyncMock(
            return_value=result,
        )
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> VFolderAdapter:
        return VFolderAdapter(mock_processors)

    async def test_my_search_calls_processor_with_user_scope(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
        user_data: UserData,
    ) -> None:
        """my_search should call search_user_vfolders processor with correct user scope."""
        input_dto = SearchVFoldersInput(limit=10, offset=0)

        with patch(
            "ai.backend.manager.api.adapters.vfolder.adapter.current_user",
            return_value=user_data,
        ):
            await adapter.my_search(input_dto)

        mock_processors.vfolder.search_user_vfolders.wait_for_complete.assert_called_once()
        action = mock_processors.vfolder.search_user_vfolders.wait_for_complete.call_args[0][0]
        assert action.scope.user_id == user_data.user_id

    async def test_my_search_returns_payload(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
        user_data: UserData,
    ) -> None:
        """my_search should return SearchVFoldersPayload with items from action result."""
        input_dto = SearchVFoldersInput(limit=10, offset=0)

        with patch(
            "ai.backend.manager.api.adapters.vfolder.adapter.current_user",
            return_value=user_data,
        ):
            result = await adapter.my_search(input_dto)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False


class TestVFolderAdapterProjectSearch:
    """Tests for VFolderAdapter.project_search()."""

    @pytest.fixture
    def project_id(self) -> uuid.UUID:
        return uuid4()

    @pytest.fixture
    def vfolder_data(self) -> VFolderData:
        group_id = uuid4()
        return VFolderData(
            id=VFolderUUID(uuid4()),
            name="project-vfolder",
            host="local:volume1",
            quota_scope_id=QuotaScopeID.parse(f"user:{uuid4()}"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            creator="test@example.com",
            creator_id=uuid4(),
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.GROUP,
            user=uuid4(),
            group=group_id,
            cloneable=False,
            status=VFolderOperationStatus.READY,
            created_at=datetime.now(tz=UTC),
            last_used=None,
            updated_at=datetime.now(tz=UTC),
            domain_name="default",
        )

    @pytest.fixture
    def mock_processors(
        self,
        vfolder_data: VFolderData,
        project_id: uuid.UUID,
    ) -> MagicMock:
        processors = MagicMock()
        result = SearchVFoldersInProjectActionResult(
            project_id=project_id,
            data=[vfolder_data],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        processors.vfolder.search_vfolders_in_project.wait_for_complete = AsyncMock(
            return_value=result,
        )
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> VFolderAdapter:
        return VFolderAdapter(mock_processors)

    async def test_project_search_calls_processor_with_project_scope(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
        project_id: uuid.UUID,
    ) -> None:
        """project_search should call search_vfolders_in_project with correct scope."""
        input_dto = SearchVFoldersInput(limit=10, offset=0)

        await adapter.project_search(project_id, input_dto)

        mock_processors.vfolder.search_vfolders_in_project.wait_for_complete.assert_called_once()
        action = mock_processors.vfolder.search_vfolders_in_project.wait_for_complete.call_args[0][
            0
        ]
        assert action.scope.project_id == project_id

    async def test_project_search_returns_payload(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
        project_id: uuid.UUID,
    ) -> None:
        """project_search should return SearchVFoldersPayload with items."""
        input_dto = SearchVFoldersInput(limit=10, offset=0)

        result = await adapter.project_search(project_id, input_dto)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False


class TestVFolderAdapterConvertFilter:
    """Tests for VFolderAdapter._convert_vfolder_filter() cloneable handling."""

    @pytest.fixture
    def adapter(self) -> VFolderAdapter:
        return VFolderAdapter(MagicMock())

    @pytest.mark.parametrize("value", [True, False])
    def test_cloneable_filter_produces_condition(
        self, adapter: VFolderAdapter, value: bool
    ) -> None:
        """cloneable filter produces exactly one callable condition."""
        f = VFolderFilter(cloneable=value)
        conditions = adapter._convert_vfolder_filter(f)
        assert len(conditions) == 1
        assert callable(conditions[0])

    def test_no_cloneable_produces_no_conditions(self, adapter: VFolderAdapter) -> None:
        """No cloneable filter produces no conditions."""
        f = VFolderFilter()
        conditions = adapter._convert_vfolder_filter(f)
        assert len(conditions) == 0

    def test_cloneable_true_sql_references_column(self, adapter: VFolderAdapter) -> None:
        """cloneable=True generates SQL referencing vfolders.cloneable."""
        f = VFolderFilter(cloneable=True)
        conditions = adapter._convert_vfolder_filter(f)
        sql = str(conditions[0]().compile(compile_kwargs={"literal_binds": True}))
        assert "vfolders.cloneable" in sql


class TestVFolderAdapterGetFolderUsage:
    """Tests for VFolderAdapter.get_folder_usage()."""

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> VFolderAdapter:
        return VFolderAdapter(mock_processors)

    async def test_maps_usage_data_to_dto(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Live measurements are mapped into the DTO with BinarySizeInfo
        conversion for byte values."""
        vfolder_uuid = uuid4()
        action_result = GetVFolderUsageActionResult(
            vfolder_uuid=vfolder_uuid,
            usage=VFolderUsageData(
                num_files=2,
                used_bytes=524308,
            ),
        )
        mock_processors.vfolder.get_folder_usage.wait_for_complete = AsyncMock(
            return_value=action_result,
        )

        dto = await adapter.get_folder_usage(vfolder_uuid)

        assert dto is not None
        assert dto.num_files == 2
        assert dto.used_bytes.value == 524308

    async def test_unmanaged_vfolder_returns_none(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """A None usage in the action result (unmanaged vfolder) yields None."""
        action_result = GetVFolderUsageActionResult(
            vfolder_uuid=uuid4(),
            usage=None,
        )
        mock_processors.vfolder.get_folder_usage.wait_for_complete = AsyncMock(
            return_value=action_result,
        )

        dto = await adapter.get_folder_usage(uuid4())

        assert dto is None


class TestVFolderAdapterRestore:
    """Tests for VFolderAdapter.restore() owner_id delegation."""

    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        processors = MagicMock()
        processors.vfolder.restore_vfolder_from_trash.wait_for_complete = AsyncMock()
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> VFolderAdapter:
        return VFolderAdapter(mock_processors)

    @pytest.mark.parametrize(
        "with_owner",
        [pytest.param(False, id="no-owner"), pytest.param(True, id="with-owner")],
    )
    async def test_restore_acting_user_follows_owner_id(
        self,
        adapter: VFolderAdapter,
        mock_processors: MagicMock,
        user_data: UserData,
        with_owner: bool,
    ) -> None:
        """Without owner_id the acting user is the caller; with owner_id it is the owner."""
        vfolder_id = uuid4()
        owner_id = UserID(uuid4()) if with_owner else None
        with patch(
            "ai.backend.manager.api.adapters.vfolder.adapter.current_user",
            return_value=user_data,
        ):
            await adapter.restore(vfolder_id, owner_id=owner_id)

        restore_mock = mock_processors.vfolder.restore_vfolder_from_trash.wait_for_complete
        action = restore_mock.call_args[0][0]
        expected_user = owner_id if with_owner else user_data.user_id
        assert action.user_uuid == expected_user
        assert action.vfolder_uuid == vfolder_id
        if with_owner:
            assert action.user_uuid != user_data.user_id
