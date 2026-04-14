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
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.api.adapters.vfolder import VFolderAdapter
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.user import UserRole
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
            id=uuid4(),
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
            "ai.backend.manager.api.adapters.vfolder.current_user",
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
            "ai.backend.manager.api.adapters.vfolder.current_user",
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
            id=uuid4(),
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
