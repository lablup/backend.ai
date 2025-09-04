"""Tests for failure threshold behavior in leader election."""

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
async def config_with_threshold():
    """Create a config with specific failure threshold."""
    return ValkeyLeaderElectionConfig(
        server_id="test-server-001",
        leader_key="test:leader",
        lease_duration=10,
        renewal_interval=0.5,  # Short interval for testing
        failure_threshold=3,  # Allow 3 failures before losing leadership
    )


@pytest.fixture
async def leader_election_with_threshold(mock_leader_client, config_with_threshold):
    """Create a ValkeyLeaderElection instance with failure threshold."""
    return ValkeyLeaderElection(
        leader_client=mock_leader_client,
        config=config_with_threshold,
    )


class TestFailureThreshold:
    """Test cases for failure threshold behavior."""

    async def test_maintains_leadership_within_threshold(
        self, leader_election_with_threshold, mock_leader_client
    ):
        """Test that leadership is maintained when failures are within threshold."""
        # First call succeeds (become leader), then 2 failures, then success
        mock_leader_client.acquire_or_renew_leadership.side_effect = [
            True,  # Become leader
            Exception("Network error"),  # Failure 1
            Exception("Network error"),  # Failure 2
            True,  # Success - should reset counter
            True,  # Continue as leader
            True,  # Continue as leader
        ]

        # Start the election
        await leader_election_with_threshold.start()

        # Wait for initial leadership acquisition
        await asyncio.sleep(0.7)
        assert leader_election_with_threshold.is_leader is True

        # Wait for 2 failures
        await asyncio.sleep(1.0)
        # Should still be leader (2 failures < threshold of 3)
        assert leader_election_with_threshold.is_leader is True

        # Wait for successful renewal
        await asyncio.sleep(0.6)
        # Should still be leader (counter is reset internally)
        assert leader_election_with_threshold.is_leader is True

        # Stop the election
        await leader_election_with_threshold.stop()

    async def test_loses_leadership_at_threshold(
        self, leader_election_with_threshold, mock_leader_client
    ):
        """Test that leadership is lost when failures reach threshold."""
        # First call succeeds (become leader), then 3 consecutive failures
        mock_leader_client.acquire_or_renew_leadership.side_effect = [
            True,  # Become leader
            Exception("Network error"),  # Failure 1
            Exception("Network error"),  # Failure 2
            Exception("Network error"),  # Failure 3 - should lose leadership
            False,  # After losing, continue as non-leader
        ]

        # Start the election
        await leader_election_with_threshold.start()

        # Wait for initial leadership acquisition
        await asyncio.sleep(0.7)
        assert leader_election_with_threshold.is_leader is True

        # Wait for 3 failures (threshold)
        await asyncio.sleep(1.7)
        # Should have lost leadership after 3 failures
        assert leader_election_with_threshold.is_leader is False

        # Stop the election
        await leader_election_with_threshold.stop()

    async def test_no_false_positives_when_not_leader(
        self, leader_election_with_threshold, mock_leader_client
    ):
        """Test that failures don't affect non-leader status."""
        # All calls fail (never become leader)
        mock_leader_client.acquire_or_renew_leadership.side_effect = Exception("Network error")

        # Start the election
        await leader_election_with_threshold.start()

        # Wait for multiple failure cycles
        await asyncio.sleep(2.0)

        # Should never have been leader
        assert leader_election_with_threshold.is_leader is False

        # Stop the election
        await leader_election_with_threshold.stop()

    async def test_counter_reset_on_success(
        self, leader_election_with_threshold, mock_leader_client
    ):
        """Test that failure counter resets on successful renewal."""
        # Pattern: success, 2 failures, success (should reset), 2 failures
        mock_leader_client.acquire_or_renew_leadership.side_effect = [
            True,  # Become leader
            Exception("Network error"),  # Failure 1
            Exception("Network error"),  # Failure 2
            True,  # Success - should reset counter
            Exception("Network error"),  # Failure 1 (after reset)
            Exception("Network error"),  # Failure 2 (after reset)
            True,  # Still leader
        ]

        # Start the election
        await leader_election_with_threshold.start()

        # Wait for initial leadership
        await asyncio.sleep(0.7)
        assert leader_election_with_threshold.is_leader is True

        # Wait through the entire sequence
        await asyncio.sleep(3.5)

        # Should still be leader (never reached 3 consecutive failures)
        assert leader_election_with_threshold.is_leader is True

        # Stop the election
        await leader_election_with_threshold.stop()
