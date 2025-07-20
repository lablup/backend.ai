import asyncio
import time
from typing import Dict, Optional, Tuple

import aiohttp
from aiohttp import TCPConnector

from ai.backend.web.config.unified import WebServerUnifiedConfig


class SessionPoolEntry:
    """Represents a pooled session with metadata."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.usage_count = 0

    def mark_used(self) -> None:
        """Update last used timestamp and increment usage counter."""
        self.last_used_at = time.time()
        self.usage_count += 1

    def is_expired(self, max_age: float, idle_timeout: float) -> bool:
        """Check if the session should be considered expired."""
        current_time = time.time()
        age = current_time - self.created_at
        idle_time = current_time - self.last_used_at
        return age > max_age or idle_time > idle_timeout


class APISessionPoolManager:
    """Manages a pool of reusable aiohttp.ClientSession instances."""

    def __init__(self, config: WebServerUnifiedConfig):
        self._config = config
        self._pools: Dict[Tuple, SessionPoolEntry] = {}
        self._pool_locks: Dict[Tuple, asyncio.Lock] = {}
        self._closed = False

        # Default configuration values (can be overridden by config)
        self.max_connections_per_host = 100
        self.max_pool_size = 1000
        self.idle_timeout = 300.0  # 5 minutes
        self.connection_timeout = 30.0
        self.max_age = 3600.0  # 1 hour
        self.enabled = True

        # Apply configuration if available
        if hasattr(config, "session_pool"):
            pool_config = config.session_pool
            self.max_connections_per_host = getattr(
                pool_config, "max_connections_per_host", self.max_connections_per_host
            )
            self.max_pool_size = getattr(pool_config, "max_pool_size", self.max_pool_size)
            self.idle_timeout = getattr(pool_config, "idle_timeout", self.idle_timeout)
            self.connection_timeout = getattr(
                pool_config, "connection_timeout", self.connection_timeout
            )
            self.enabled = getattr(pool_config, "enabled", self.enabled)
            self.max_age = getattr(pool_config, "max_age", self.max_age)

    async def get_session(
        self, pool_key: Tuple, ssl_verify: bool = True, connector_params: Optional[Dict] = None
    ) -> aiohttp.ClientSession:
        """Get or create a session for the given pool key."""
        if self._closed:
            raise RuntimeError("Session pool manager is closed")

        if not self.enabled:
            # If pooling is disabled, return a new session each time
            return self._create_new_session(ssl_verify, connector_params)

        # Ensure we have a lock for this pool key
        if pool_key not in self._pool_locks:
            self._pool_locks[pool_key] = asyncio.Lock()

        async with self._pool_locks[pool_key]:
            # Check if we have a valid pooled session
            if pool_key in self._pools:
                entry = self._pools[pool_key]

                # Check if session is still valid
                if not entry.is_expired(self.max_age, self.idle_timeout):
                    entry.mark_used()
                    return entry.session
                else:
                    # Session expired, close and remove it
                    await entry.session.close()
                    del self._pools[pool_key]

            # Check pool size limit
            if len(self._pools) >= self.max_pool_size:
                # Find and remove the least recently used session
                await self._evict_lru_session()

            # Create new session
            session = self._create_new_session(ssl_verify, connector_params)
            self._pools[pool_key] = SessionPoolEntry(session)

            return session

    def _create_new_session(
        self, ssl_verify: bool = True, connector_params: Optional[Dict] = None
    ) -> aiohttp.ClientSession:
        """Create a new aiohttp ClientSession with configured parameters."""
        conn_params = connector_params or {}

        # Apply our configuration
        conn_params.setdefault("limit", self.max_connections_per_host)
        conn_params.setdefault("limit_per_host", self.max_connections_per_host)
        conn_params.setdefault("ssl", ssl_verify)

        connector = TCPConnector(**conn_params)

        timeout = aiohttp.ClientTimeout(
            connect=self.connection_timeout,
            total=None,  # No total timeout by default
        )

        return aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def _evict_lru_session(self) -> None:
        """Remove the least recently used session from the pool."""
        if not self._pools:
            return

        # Find LRU session
        lru_key = min(self._pools.keys(), key=lambda k: self._pools[k].last_used_at)

        # Close and remove it
        entry = self._pools[lru_key]
        await entry.session.close()
        del self._pools[lru_key]

        # Remove associated lock if no longer needed
        if lru_key in self._pool_locks:
            del self._pool_locks[lru_key]

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned."""
        if self._closed:
            return 0

        cleaned = 0
        keys_to_remove = []

        for key, entry in self._pools.items():
            if entry.is_expired(self.max_age, self.idle_timeout):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            if key in self._pool_locks:
                async with self._pool_locks[key]:
                    if key in self._pools:
                        entry = self._pools[key]
                        await entry.session.close()
                        del self._pools[key]
                        cleaned += 1

        return cleaned

    async def close(self) -> None:
        """Close all pooled sessions and mark manager as closed."""
        if self._closed:
            return

        self._closed = True

        # Close all sessions
        for entry in self._pools.values():
            await entry.session.close()

        self._pools.clear()
        self._pool_locks.clear()

    def get_stats(self) -> Dict:
        """Get current pool statistics."""
        total_usage = sum(entry.usage_count for entry in self._pools.values())
        avg_usage = total_usage / len(self._pools) if self._pools else 0

        return {
            "pool_size": len(self._pools),
            "enabled": self.enabled,
            "total_usage_count": total_usage,
            "average_usage_per_session": avg_usage,
            "max_pool_size": self.max_pool_size,
            "idle_timeout": self.idle_timeout,
            "max_age": self.max_age,
        }
