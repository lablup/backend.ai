"""
Tests for _report_all_kernel_commit_status_map.

Mock-based unit tests to verify commit status scanning handles
filesystem errors gracefully and prevents FD leaks.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai.backend.agent.agent import COMMIT_STATUS_EXPIRE, AbstractAgent


@dataclass
class CommitScanScenario:
    """Describes a directory layout and expected kernel IDs after scanning."""

    id: str
    user_kernels: dict[str, list[str]] = field(default_factory=dict)
    expected_kernel_ids: set[str] = field(default_factory=set)


class TestReportAllKernelCommitStatusMap:
    """Tests for _report_all_kernel_commit_status_map timer callback."""

    @pytest.fixture
    def mock_agent(self, tmp_path: Path) -> AsyncMock:
        agent = AsyncMock(spec=AbstractAgent)
        agent.local_config = Mock()
        agent.local_config.agent = Mock()
        agent.local_config.agent.image_commit_path = tmp_path / "commit"
        agent.local_config.agent.image_commit_path.mkdir(parents=True)
        agent.valkey_stat_client = AsyncMock()
        agent.valkey_stat_client.update_kernel_commit_statuses = AsyncMock()
        return agent

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario",
        [
            CommitScanScenario(
                id="single_user_two_kernels",
                user_kernels={"user1@example.com": ["kernel-1", "kernel-2"]},
                expected_kernel_ids={"kernel-1", "kernel-2"},
            ),
            CommitScanScenario(
                id="multiple_users",
                user_kernels={"user1": ["kernel-a"], "user2": ["kernel-b"]},
                expected_kernel_ids={"kernel-a", "kernel-b"},
            ),
            CommitScanScenario(
                id="empty_directory",
                user_kernels={},
                expected_kernel_ids=set(),
            ),
        ],
    )
    async def test_scans_lock_files_and_reports_kernel_ids(
        self,
        mock_agent: AsyncMock,
        scenario: CommitScanScenario,
    ) -> None:
        base = mock_agent.local_config.agent.image_commit_path
        # Given: Set up directory structure based on scenario
        for user, kernels in scenario.user_kernels.items():
            lock_dir = base / user / "lock"
            lock_dir.mkdir(parents=True)
            for kernel in kernels:
                (lock_dir / kernel).touch()

        # When: Call the method under test
        await AbstractAgent._report_all_kernel_commit_status_map(mock_agent, 7.0)

        # Then: Verify update_kernel_commit_statuses called with expected kernel IDs and expire time
        mock_agent.valkey_stat_client.update_kernel_commit_statuses.assert_called_once()
        call_args = mock_agent.valkey_stat_client.update_kernel_commit_statuses.call_args
        kernel_ids = set(call_args[0][0])
        expire_sec = call_args[0][1]
        assert kernel_ids == scenario.expected_kernel_ids
        assert expire_sec == COMMIT_STATUS_EXPIRE

    @pytest.mark.asyncio
    async def test_nonexistent_path_skips_scan(
        self,
        mock_agent: AsyncMock,
    ) -> None:
        # Given: Just make path, not a directory, so it doesn't exist for iterdir()
        mock_agent.local_config.agent.image_commit_path = Path("/nonexistent/path")

        # When: Call the method under test
        await AbstractAgent._report_all_kernel_commit_status_map(mock_agent, 7.0)

        # Then: Verify update_kernel_commit_statuses called with empty list and expire time
        call_args = mock_agent.valkey_stat_client.update_kernel_commit_statuses.call_args
        kernel_ids = call_args[0][0]
        assert kernel_ids == []

    @pytest.fixture
    def mock_log(self) -> Generator[Mock, None, None]:
        with patch("ai.backend.agent.agent.log") as _mock_log:
            yield _mock_log

    @pytest.mark.asyncio
    async def test_exception_during_scan_is_caught_and_logged(
        self,
        mock_agent: AsyncMock,
        mock_log: Mock,
        tmp_path: Path,
    ) -> None:
        # Given: Create a file instead of a directory to cause an exception during scanning
        file_path = tmp_path / "a-file"
        file_path.touch()
        mock_agent.local_config.agent.image_commit_path = file_path

        # When: Call the method under test
        await AbstractAgent._report_all_kernel_commit_status_map(mock_agent, 7.0)

        # Then: Verify exception was logged and update_kernel_commit_statuses was not called
        mock_log.exception.assert_called_once()
        mock_agent.valkey_stat_client.update_kernel_commit_statuses.assert_not_called()
