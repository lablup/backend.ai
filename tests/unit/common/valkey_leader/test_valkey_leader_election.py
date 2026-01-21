"""Tests for Valkey-based leader election manager."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
from ai.backend.common.leader.valkey_leader_election import (
    ValkeyLeaderElection,
    ValkeyLeaderElectionConfig,
)


@pytest.fixture
async def mock_leader_client():
    """Create a mock ValkeyLeaderClient."""
    client = AsyncMock(spec=ValkeyLeaderClient)
    client.acquire_or_renew_leadership = AsyncMock(return_value=False)
    client.release_leadership = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
async def leader_election_config():
    """Create a ValkeyLeaderElectionConfig."""
    return ValkeyLeaderElectionConfig(
        server_id="test-server-001",
        leader_key="test:leader",
        lease_duration=10,
        renewal_interval=1.0,  # Short interval for testing
    )


@pytest.fixture
async def leader_election(mock_leader_client, leader_election_config):
    """Create a ValkeyLeaderElection instance."""
    return ValkeyLeaderElection(
        leader_client=mock_leader_client,
        config=leader_election_config,
    )


class TestValkeyLeaderElection:
    """Test cases for ValkeyLeaderElection."""

    async def test_initialization(self, leader_election, leader_election_config):
        """Test ValkeyLeaderElection initialization."""
        assert leader_election.server_id == "test-server-001"
        assert leader_election._config == leader_election_config
        assert leader_election._config.leader_key == "test:leader"
        assert leader_election._config.lease_duration == 10
        assert leader_election._config.renewal_interval == 1.0
        assert leader_election.is_leader is False
        assert leader_election._stopped is False

    async def test_start_stop(self, leader_election, mock_leader_client):
        """Test starting and stopping the election."""
        # Start the election
        await leader_election.start()

        # Verify election task was created
        assert leader_election._election_task is not None
        assert not leader_election._stopped

        # Give it a moment to run
        await asyncio.sleep(0.1)

        # Stop the election
        await leader_election.stop()

        # Verify everything was stopped
        assert leader_election._stopped is True

    async def test_leader_acquisition(self, leader_election, mock_leader_client):
        """Test leader acquisition process."""
        # Configure mock to simulate becoming leader
        mock_leader_client.acquire_or_renew_leadership.side_effect = [False, True, True]

        # Start the election
        await leader_election.start()

        # Wait for a few renewal cycles
        await asyncio.sleep(2.5)

        # Should have tried to acquire leadership multiple times
        assert mock_leader_client.acquire_or_renew_leadership.call_count >= 2

        # Check that it became leader
        assert leader_election.is_leader is True

        # Stop the election
        await leader_election.stop()

    async def test_leader_loss(self, leader_election, mock_leader_client):
        """Test losing leadership."""
        # Configure mock to simulate becoming leader then losing it
        mock_leader_client.acquire_or_renew_leadership.side_effect = [True, True, False]

        # Start the election
        await leader_election.start()

        # Wait for renewal cycles
        await asyncio.sleep(3.5)

        # Should have lost leadership
        assert leader_election.is_leader is False

        # Stop the election
        await leader_election.stop()

    async def test_release_leadership_on_stop(self, leader_election, mock_leader_client):
        """Test that leadership is released when stopping."""
        # Set up as leader
        mock_leader_client.acquire_or_renew_leadership.return_value = True

        # Start and become leader
        await leader_election.start()
        await asyncio.sleep(1.5)

        assert leader_election.is_leader is True

        # Stop the election
        await leader_election.stop()

        # Verify leadership was released
        mock_leader_client.release_leadership.assert_called_once_with(
            server_id="test-server-001",
            leader_key="test:leader",
        )
        assert leader_election.is_leader is False

    async def test_error_handling_in_renewal_loop(self, leader_election, mock_leader_client):
        """Test error handling in the renewal loop."""
        # Configure mock to raise an exception
        mock_leader_client.acquire_or_renew_leadership.side_effect = Exception("Connection error")

        # Start the election
        await leader_election.start()

        # Wait for a renewal cycle
        await asyncio.sleep(1.5)

        # Should not be leader due to error
        assert leader_election.is_leader is False

        # Stop the election
        await leader_election.stop()

    async def test_leadership_renewal(self, leader_election, mock_leader_client):
        """Test continuous leadership renewal."""
        # Configure mock to always return True (maintain leadership)
        mock_leader_client.acquire_or_renew_leadership.return_value = True

        # Start the election
        await leader_election.start()

        # Wait for multiple renewal cycles
        await asyncio.sleep(3.5)

        # Should have renewed leadership multiple times
        assert mock_leader_client.acquire_or_renew_leadership.call_count >= 3

        # Should still be leader
        assert leader_election.is_leader is True

        # Stop the election
        await leader_election.stop()
