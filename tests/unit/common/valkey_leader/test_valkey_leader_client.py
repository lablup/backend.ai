"""Tests for Valkey-based leader election client."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from glide import Script

from ai.backend.common.clients.valkey_client.valkey_leader.client import (
    ValkeyLeaderClient,
)
from ai.backend.common.exception import BackendAIError, ErrorCode


@pytest.fixture
async def mock_valkey_client():
    """Create a mock Valkey client."""
    client_mock = AsyncMock()
    client_mock.client = AsyncMock()
    return client_mock


@pytest.fixture
async def leader_client(mock_valkey_client):
    """Create a ValkeyLeaderClient instance with mocked dependencies."""
    return ValkeyLeaderClient(
        client=mock_valkey_client,
    )


class TestValkeyLeaderClient:
    """Test cases for ValkeyLeaderClient."""

    async def test_initialization(self, leader_client):
        """Test that ValkeyLeaderClient is initialized correctly."""
        assert isinstance(leader_client._leader_script, Script)
        assert isinstance(leader_client._release_script, Script)

    async def test_acquire_leadership_when_no_leader(self, leader_client, mock_valkey_client):
        """Test acquiring leadership when no current leader exists."""
        # Mock the Lua script to return 1 (successfully acquired)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=1)

        result = await leader_client.acquire_or_renew_leadership(
            server_id="test-server-001",
            leader_key="test:leader",
            lease_duration=10,
        )

        assert result is True
        mock_valkey_client.client.invoke_script.assert_called_once()

        # Check the script was called with correct parameters
        call_args = mock_valkey_client.client.invoke_script.call_args
        assert call_args.kwargs["keys"] == ["test:leader"]
        assert call_args.kwargs["args"] == ["test-server-001", "10"]

    async def test_renew_leadership_when_already_leader(self, leader_client, mock_valkey_client):
        """Test renewing leadership when already the leader."""
        # Mock the Lua script to return 1 (successfully renewed)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=1)

        result = await leader_client.acquire_or_renew_leadership(
            server_id="test-server-001",
            leader_key="test:leader",
            lease_duration=15,
        )

        assert result is True
        mock_valkey_client.client.invoke_script.assert_called_once()

        # Check the script was called with correct parameters
        call_args = mock_valkey_client.client.invoke_script.call_args
        assert call_args.kwargs["keys"] == ["test:leader"]
        assert call_args.kwargs["args"] == ["test-server-001", "15"]

    async def test_fail_to_acquire_when_another_leader_exists(
        self, leader_client, mock_valkey_client
    ):
        """Test failing to acquire leadership when another server is leader."""
        # Mock the Lua script to return 0 (failed to acquire)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=0)

        result = await leader_client.acquire_or_renew_leadership(
            server_id="test-server-001",
            leader_key="test:leader",
            lease_duration=10,
        )

        assert result is False
        mock_valkey_client.client.invoke_script.assert_called_once()

    async def test_handle_exception_during_acquire(self, leader_client, mock_valkey_client):
        """Test that exceptions are propagated during acquire_or_renew_leadership."""

        # Mock the Lua script to raise an exception
        class MockBackendAIError(BackendAIError):
            @classmethod
            def error_code(cls) -> ErrorCode:
                return ErrorCode.default()

        mock_valkey_client.client.invoke_script = AsyncMock(
            side_effect=MockBackendAIError("Connection error")
        )

        with pytest.raises(Exception, match="Connection error"):
            await leader_client.acquire_or_renew_leadership(
                server_id="test-server-001",
                leader_key="test:leader",
                lease_duration=10,
            )

        # The decorator with retry_count=1 means no retries (try once)
        assert mock_valkey_client.client.invoke_script.call_count == 1

    async def test_release_leadership_when_leader(self, leader_client, mock_valkey_client):
        """Test releasing leadership when this server is the leader."""
        # Mock the Lua script to return 1 (successfully released)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=1)

        result = await leader_client.release_leadership(
            server_id="test-server-001", leader_key="test:leader"
        )

        assert result is True
        mock_valkey_client.client.invoke_script.assert_called_once()

        # Check the script was called with correct parameters
        call_args = mock_valkey_client.client.invoke_script.call_args
        assert call_args.kwargs["keys"] == ["test:leader"]
        assert call_args.kwargs["args"] == ["test-server-001"]

    async def test_release_leadership_when_not_leader(self, leader_client, mock_valkey_client):
        """Test releasing leadership when another server is the leader."""
        # Mock the Lua script to return 0 (not the leader)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=0)

        result = await leader_client.release_leadership(
            server_id="test-server-001", leader_key="test:leader"
        )

        assert result is False
        mock_valkey_client.client.invoke_script.assert_called_once()

    async def test_release_leadership_when_no_leader(self, leader_client, mock_valkey_client):
        """Test releasing leadership when no leader exists."""
        # Mock the Lua script to return 0 (no leader to release)
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=0)

        result = await leader_client.release_leadership(
            server_id="test-server-001", leader_key="test:leader"
        )

        assert result is False
        mock_valkey_client.client.invoke_script.assert_called_once()

    async def test_release_leadership_with_exception(self, leader_client, mock_valkey_client):
        """Test that exceptions are propagated during release_leadership."""
        # Mock the Lua script to raise an exception
        mock_valkey_client.client.invoke_script = AsyncMock(
            side_effect=Exception("Connection error")
        )

        with pytest.raises(Exception, match="Connection error"):
            await leader_client.release_leadership(
                server_id="test-server-001", leader_key="test:leader"
            )

        # The decorator retries 3 times by default
        assert mock_valkey_client.client.invoke_script.call_count == 3

    async def test_close(self, leader_client, mock_valkey_client):
        """Test closing the ValkeyLeaderClient."""
        mock_valkey_client.disconnect = AsyncMock()

        await leader_client.close()

        mock_valkey_client.disconnect.assert_called_once()

    @pytest.mark.parametrize("lease_duration", [5, 10, 30, 60])
    async def test_different_lease_durations(
        self, leader_client, mock_valkey_client, lease_duration
    ):
        """Test acquire_or_renew_leadership with different lease durations."""
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=1)

        result = await leader_client.acquire_or_renew_leadership(
            server_id="test-server-001",
            leader_key="test:leader",
            lease_duration=lease_duration,
        )

        assert result is True
        call_args = mock_valkey_client.client.invoke_script.call_args
        assert call_args.kwargs["args"][1] == str(lease_duration)

    @pytest.mark.parametrize(
        "leader_key",
        [
            "leader:scheduler",
            "leader:event_producer",
            "leader:cleanup",
            "test:leader:custom",
        ],
    )
    async def test_different_leader_keys(self, leader_client, mock_valkey_client, leader_key):
        """Test acquire_or_renew_leadership with different leader keys."""
        mock_valkey_client.client.invoke_script = AsyncMock(return_value=1)

        result = await leader_client.acquire_or_renew_leadership(
            server_id="test-server-001",
            leader_key=leader_key,
            lease_duration=10,
        )

        assert result is True
        call_args = mock_valkey_client.client.invoke_script.call_args
        assert call_args.kwargs["keys"][0] == leader_key
