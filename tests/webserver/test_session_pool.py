import asyncio
import time
from unittest.mock import MagicMock, patch

import aiohttp
import pytest

from ai.backend.web.config.unified import SessionPoolConfig, WebServerUnifiedConfig
from ai.backend.web.session_pool import APISessionPoolManager, SessionPoolEntry


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock(spec=WebServerUnifiedConfig)
    config.session_pool = SessionPoolConfig(
        enabled=True,
        max_connections_per_host=10,
        max_pool_size=100,
        idle_timeout=5.0,
        connection_timeout=2.0,
        max_age=10.0,
    )
    return config


@pytest.fixture
def disabled_pool_config():
    """Create a mock configuration with pooling disabled."""
    config = MagicMock(spec=WebServerUnifiedConfig)
    config.session_pool = SessionPoolConfig(
        enabled=False,
    )
    return config


class TestSessionPoolEntry:
    def test_session_pool_entry_creation(self):
        """Test creating a session pool entry."""
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        entry = SessionPoolEntry(mock_session)

        assert entry.session == mock_session
        assert entry.usage_count == 0
        assert isinstance(entry.created_at, float)
        assert isinstance(entry.last_used_at, float)
        assert entry.created_at == entry.last_used_at

    def test_mark_used(self):
        """Test marking a session as used."""
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        entry = SessionPoolEntry(mock_session)

        initial_time = entry.last_used_at
        time.sleep(0.01)  # Small delay to ensure time difference

        entry.mark_used()

        assert entry.usage_count == 1
        assert entry.last_used_at > initial_time

        entry.mark_used()
        assert entry.usage_count == 2

    def test_is_expired_by_age(self):
        """Test checking if a session is expired by age."""
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        entry = SessionPoolEntry(mock_session)

        # Not expired initially
        assert not entry.is_expired(max_age=10.0, idle_timeout=5.0)

        # Mock time to make it expired by age
        entry.created_at = time.time() - 15.0
        assert entry.is_expired(max_age=10.0, idle_timeout=5.0)

    def test_is_expired_by_idle_timeout(self):
        """Test checking if a session is expired by idle timeout."""
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        entry = SessionPoolEntry(mock_session)

        # Not expired initially
        assert not entry.is_expired(max_age=10.0, idle_timeout=5.0)

        # Mock time to make it expired by idle timeout
        entry.last_used_at = time.time() - 7.0
        assert entry.is_expired(max_age=10.0, idle_timeout=5.0)


class TestAPISessionPoolManager:
    @pytest.mark.asyncio
    async def test_pool_manager_creation(self, mock_config):
        """Test creating a session pool manager."""
        manager = APISessionPoolManager(mock_config)

        assert manager.enabled is True
        assert manager.max_connections_per_host == 10
        assert manager.max_pool_size == 100
        assert manager.idle_timeout == 5.0
        assert manager.connection_timeout == 2.0
        assert manager.max_age == 10.0
        assert not manager._closed
        assert len(manager._pools) == 0
        assert len(manager._pool_locks) == 0

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, mock_config):
        """Test getting a session creates a new one when pool is empty."""
        manager = APISessionPoolManager(mock_config)
        pool_key = ("http://api.test.com", "default", "test_key")

        with patch.object(manager, "_create_new_session") as mock_create:
            mock_session = MagicMock(spec=aiohttp.ClientSession)
            mock_create.return_value = mock_session

            session = await manager.get_session(pool_key)

            assert session == mock_session
            assert pool_key in manager._pools
            assert pool_key in manager._pool_locks
            assert manager._pools[pool_key].session == mock_session
            assert manager._pools[pool_key].usage_count == 0

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, mock_config):
        """Test getting a session reuses an existing one from the pool."""
        manager = APISessionPoolManager(mock_config)
        pool_key = ("http://api.test.com", "default", "test_key")

        # Create initial session
        with patch.object(manager, "_create_new_session") as mock_create:
            mock_session = MagicMock(spec=aiohttp.ClientSession)
            mock_create.return_value = mock_session

            session1 = await manager.get_session(pool_key)
            usage_count1 = manager._pools[pool_key].usage_count

            # Get the same session again
            session2 = await manager.get_session(pool_key)
            usage_count2 = manager._pools[pool_key].usage_count

            assert session1 == session2
            assert mock_create.call_count == 1  # Only called once
            assert usage_count2 == usage_count1 + 1

    @pytest.mark.asyncio
    async def test_get_session_removes_expired(self, mock_config):
        """Test getting a session removes expired sessions."""
        manager = APISessionPoolManager(mock_config)
        pool_key = ("http://api.test.com", "default", "test_key")

        # Create initial session
        with patch.object(manager, "_create_new_session") as mock_create:
            mock_session1 = MagicMock(spec=aiohttp.ClientSession)
            mock_session2 = MagicMock(spec=aiohttp.ClientSession)
            mock_create.side_effect = [mock_session1, mock_session2]

            # Get first session
            session1 = await manager.get_session(pool_key)

            # Mark it as expired
            manager._pools[pool_key].created_at = time.time() - 20.0

            # Get session again - should create new one
            session2 = await manager.get_session(pool_key)

            assert session1 != session2
            assert mock_create.call_count == 2
            mock_session1.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_disabled_pooling(self, disabled_pool_config):
        """Test getting a session when pooling is disabled."""
        manager = APISessionPoolManager(disabled_pool_config)
        pool_key = ("http://api.test.com", "default", "test_key")

        with patch.object(manager, "_create_new_session") as mock_create:
            mock_session1 = MagicMock(spec=aiohttp.ClientSession)
            mock_session2 = MagicMock(spec=aiohttp.ClientSession)
            mock_create.side_effect = [mock_session1, mock_session2]

            session1 = await manager.get_session(pool_key)
            session2 = await manager.get_session(pool_key)

            assert session1 != session2
            assert mock_create.call_count == 2
            assert len(manager._pools) == 0  # No pooling

    @pytest.mark.asyncio
    async def test_evict_lru_session(self, mock_config):
        """Test LRU eviction when pool is full."""
        mock_config.session_pool.max_pool_size = 2
        manager = APISessionPoolManager(mock_config)

        with patch.object(manager, "_create_new_session") as mock_create:
            mock_sessions = [MagicMock(spec=aiohttp.ClientSession) for _ in range(3)]
            mock_create.side_effect = mock_sessions

            # Fill the pool
            pool_key1 = ("http://api1.test.com", "default", "key1")
            pool_key2 = ("http://api2.test.com", "default", "key2")
            pool_key3 = ("http://api3.test.com", "default", "key3")

            await manager.get_session(pool_key1)
            await asyncio.sleep(0.01)  # Ensure different timestamps
            await manager.get_session(pool_key2)
            await asyncio.sleep(0.01)

            # This should evict the first session (LRU)
            await manager.get_session(pool_key3)

            assert pool_key1 not in manager._pools
            assert pool_key2 in manager._pools
            assert pool_key3 in manager._pools
            mock_sessions[0].close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, mock_config):
        """Test cleaning up expired sessions."""
        manager = APISessionPoolManager(mock_config)

        with patch.object(manager, "_create_new_session") as mock_create:
            mock_sessions = [MagicMock(spec=aiohttp.ClientSession) for _ in range(3)]
            mock_create.side_effect = mock_sessions

            # Create sessions
            pool_keys = [
                ("http://api1.test.com", "default", "key1"),
                ("http://api2.test.com", "default", "key2"),
                ("http://api3.test.com", "default", "key3"),
            ]

            for key in pool_keys:
                await manager.get_session(key)

            # Mark some as expired
            manager._pools[pool_keys[0]].created_at = time.time() - 20.0
            manager._pools[pool_keys[1]].last_used_at = time.time() - 10.0

            # Run cleanup
            cleaned = await manager.cleanup_expired()

            assert cleaned == 2
            assert pool_keys[0] not in manager._pools
            assert pool_keys[1] not in manager._pools
            assert pool_keys[2] in manager._pools
            mock_sessions[0].close.assert_called_once()
            mock_sessions[1].close.assert_called_once()
            mock_sessions[2].close.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_manager(self, mock_config):
        """Test closing the pool manager."""
        manager = APISessionPoolManager(mock_config)

        with patch.object(manager, "_create_new_session") as mock_create:
            mock_sessions = [MagicMock(spec=aiohttp.ClientSession) for _ in range(2)]
            mock_create.side_effect = mock_sessions

            # Create sessions
            await manager.get_session(("http://api1.test.com", "default", "key1"))
            await manager.get_session(("http://api2.test.com", "default", "key2"))

            # Close manager
            await manager.close()

            assert manager._closed is True
            assert len(manager._pools) == 0
            assert len(manager._pool_locks) == 0
            for session in mock_sessions:
                session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_after_close(self, mock_config):
        """Test getting a session after manager is closed raises error."""
        manager = APISessionPoolManager(mock_config)
        await manager.close()

        with pytest.raises(RuntimeError, match="Session pool manager is closed"):
            await manager.get_session(("http://api.test.com", "default", "key"))

    def test_get_stats(self, mock_config):
        """Test getting pool statistics."""
        manager = APISessionPoolManager(mock_config)

        # Create mock entries
        entry1 = MagicMock()
        entry1.usage_count = 5
        entry2 = MagicMock()
        entry2.usage_count = 3

        manager._pools = {
            ("key1",): entry1,
            ("key2",): entry2,
        }

        stats = manager.get_stats()

        assert stats["pool_size"] == 2
        assert stats["enabled"] is True
        assert stats["total_usage_count"] == 8
        assert stats["average_usage_per_session"] == 4.0
        assert stats["max_pool_size"] == 100
        assert stats["idle_timeout"] == 5.0
        assert stats["max_age"] == 10.0

    def test_create_new_session(self, mock_config):
        """Test creating a new aiohttp session with proper configuration."""
        manager = APISessionPoolManager(mock_config)

        with (
            patch("aiohttp.TCPConnector") as mock_connector_class,
            patch("aiohttp.ClientSession") as mock_session_class,
        ):
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            manager._create_new_session(ssl_verify=False)

            # Check connector was created with correct params
            mock_connector_class.assert_called_once_with(limit=10, limit_per_host=10, ssl=False)

            # Check session was created with connector and timeout
            mock_session_class.assert_called_once()
            call_args = mock_session_class.call_args
            assert call_args.kwargs["connector"] == mock_connector
            assert call_args.kwargs["timeout"].connect == 2.0
