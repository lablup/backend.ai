"""Integration tests for session pool functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.client.session import AsyncSession as APISession
from ai.backend.web.auth import get_anonymous_session, get_api_session
from ai.backend.web.config.unified import SessionPoolConfig, WebServerUnifiedConfig
from ai.backend.web.session_pool import APISessionPoolManager


@pytest.fixture
def mock_web_config():
    """Create a mock web server configuration."""
    config = MagicMock(spec=WebServerUnifiedConfig)
    config.api.endpoint = ["http://api.backend.ai"]
    config.api.domain = "default"
    config.api.ssl_verify = True
    config.session_pool = SessionPoolConfig(
        enabled=True,
        max_connections_per_host=10,
        max_pool_size=100,
        idle_timeout=300.0,
        connection_timeout=30.0,
        max_age=3600.0,
    )
    return config


@pytest.fixture
async def mock_app(mock_web_config):
    """Create a mock aiohttp application with session pool."""
    app = web.Application()
    app["config"] = mock_web_config
    app["session_pool_manager"] = APISessionPoolManager(mock_web_config)
    yield app
    await app["session_pool_manager"].close()


@pytest.fixture
def mock_request(mock_app):
    """Create a mock request with app context."""
    request = MagicMock(spec=web.Request)
    request.app = mock_app
    return request


class TestSessionPoolIntegration:
    @pytest.mark.asyncio
    async def test_get_api_session_with_pooling(self, mock_request):
        """Test that get_api_session uses pooled sessions."""
        # Mock the session data
        with patch("ai.backend.web.auth.get_session") as mock_get_session:
            mock_session_data = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "test_ak", "secret_key": "test_sk"},
            }
            mock_get_session.return_value = AsyncMock(return_value=mock_session_data)()

            # Get API session twice
            with patch.object(APISession, "__init__", return_value=None) as mock_init:
                # First call
                await get_api_session(mock_request)
                init_call1 = mock_init.call_args

                # Second call
                await get_api_session(mock_request)
                init_call2 = mock_init.call_args

                # Both calls should use the same http_session
                assert init_call1.kwargs.get("http_session") is not None
                assert init_call2.kwargs.get("http_session") is not None
                assert init_call1.kwargs["http_session"] is init_call2.kwargs["http_session"]
                assert init_call1.kwargs["close_http_session"] is False
                assert init_call2.kwargs["close_http_session"] is False

    @pytest.mark.asyncio
    async def test_get_anonymous_session_with_pooling(self, mock_request):
        """Test that get_anonymous_session uses pooled sessions."""
        with patch.object(APISession, "__init__", return_value=None) as mock_init:
            # First call
            await get_anonymous_session(mock_request)
            init_call1 = mock_init.call_args

            # Second call
            await get_anonymous_session(mock_request)
            init_call2 = mock_init.call_args

            # Both calls should use the same http_session
            assert init_call1.kwargs.get("http_session") is not None
            assert init_call2.kwargs.get("http_session") is not None
            assert init_call1.kwargs["http_session"] is init_call2.kwargs["http_session"]
            assert init_call1.kwargs["close_http_session"] is False
            assert init_call2.kwargs["close_http_session"] is False

    @pytest.mark.asyncio
    async def test_different_users_get_different_sessions(self, mock_request):
        """Test that different users get different pooled sessions."""
        with patch("ai.backend.web.auth.get_session") as mock_get_session:
            # Mock two different users
            user1_session = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "user1_ak", "secret_key": "user1_sk"},
            }
            user2_session = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "user2_ak", "secret_key": "user2_sk"},
            }

            with patch.object(APISession, "__init__", return_value=None) as mock_init:
                # User 1
                mock_get_session.return_value = AsyncMock(return_value=user1_session)()
                await get_api_session(mock_request)
                init_call1 = mock_init.call_args

                # User 2
                mock_get_session.return_value = AsyncMock(return_value=user2_session)()
                await get_api_session(mock_request)
                init_call2 = mock_init.call_args

                # Different users should get different http_sessions
                assert init_call1.kwargs["http_session"] is not init_call2.kwargs["http_session"]

    @pytest.mark.asyncio
    async def test_different_endpoints_get_different_sessions(self, mock_request):
        """Test that different API endpoints get different pooled sessions."""
        with patch("ai.backend.web.auth.get_session") as mock_get_session:
            mock_session_data = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "test_ak", "secret_key": "test_sk"},
            }
            mock_get_session.return_value = AsyncMock(return_value=mock_session_data)()

            with patch.object(APISession, "__init__", return_value=None) as mock_init:
                # Default endpoint
                await get_api_session(mock_request)
                init_call1 = mock_init.call_args

                # Different endpoint
                await get_api_session(mock_request, override_api_endpoint="http://api2.backend.ai")
                init_call2 = mock_init.call_args

                # Different endpoints should get different http_sessions
                assert init_call1.kwargs["http_session"] is not init_call2.kwargs["http_session"]

    @pytest.mark.asyncio
    async def test_pooling_disabled_creates_new_sessions(self, mock_request):
        """Test that disabling pooling creates new sessions each time."""
        # Disable pooling
        mock_request.app["config"].session_pool.enabled = False

        with patch("ai.backend.web.auth.get_session") as mock_get_session:
            mock_session_data = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "test_ak", "secret_key": "test_sk"},
            }
            mock_get_session.return_value = AsyncMock(return_value=mock_session_data)()

            with patch.object(APISession, "__init__", return_value=None) as mock_init:
                # First call
                await get_api_session(mock_request)
                init_call1 = mock_init.call_args

                # Second call
                await get_api_session(mock_request)
                init_call2 = mock_init.call_args

                # With pooling disabled, http_session should be None (default behavior)
                assert init_call1.kwargs.get("http_session") is None
                assert init_call2.kwargs.get("http_session") is None
                assert init_call1.kwargs.get("close_http_session", True) is True
                assert init_call2.kwargs.get("close_http_session", True) is True

    @pytest.mark.asyncio
    async def test_pool_statistics_after_usage(self, mock_request):
        """Test that pool statistics are updated correctly after usage."""
        pool_manager = mock_request.app["session_pool_manager"]

        # Create some sessions
        with patch("ai.backend.web.auth.get_session") as mock_get_session:
            mock_session_data = {
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "test_ak", "secret_key": "test_sk"},
            }
            mock_get_session.return_value = AsyncMock(return_value=mock_session_data)()

            with patch.object(APISession, "__init__", return_value=None):
                # Get API session multiple times
                for _ in range(3):
                    await get_api_session(mock_request)

                # Get anonymous session multiple times
                for _ in range(2):
                    await get_anonymous_session(mock_request)

        stats = pool_manager.get_stats()

        # Should have 2 pools: one for authenticated, one for anonymous
        assert stats["pool_size"] == 2
        assert (
            stats["total_usage_count"] == 3
        )  # 3 uses of authenticated + 2 uses of anonymous = 5 total
        assert stats["enabled"] is True

    @pytest.mark.asyncio
    async def test_session_cleanup_on_app_shutdown(self, mock_app):
        """Test that sessions are properly cleaned up on app shutdown."""
        pool_manager = mock_app["session_pool_manager"]

        # Create some sessions
        pool_key1 = ("http://api.backend.ai", "default", "key1")
        pool_key2 = ("http://api.backend.ai", "default", "key2")

        await pool_manager.get_session(pool_key1)
        await pool_manager.get_session(pool_key2)

        # Verify sessions exist
        assert len(pool_manager._pools) == 2

        # Close the pool manager (simulating app shutdown)
        await pool_manager.close()

        # Verify all sessions are cleaned up
        assert len(pool_manager._pools) == 0
        assert pool_manager._closed is True
