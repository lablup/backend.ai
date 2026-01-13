---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Implemented
Created: 2025-01-11
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version: 26.1.0
---

# Agent RPC Connection Pooling

## Related Issues

- JIRA: BA-3814, BA-3815
- Epic: BA-3813

## Motivation

Currently, the Manager creates a new ZeroMQ connection for every RPC call to an Agent.

```python
# AgentRPCCache.rpc_context() - Creates new PeerInvoker for each call
peer = PeerInvoker(
    connect=ZeroMQAddress(agent_addr),
    transport=ZeroMQRPCTransport,
    ...
)
async with peer:  # Connection established
    yield peer
# Connection closed
```

**Problems:**
1. **Connection overhead**: ZeroMQ connection setup → CurveZMQ authentication → RPC call → connection teardown happens every time
2. **TCP Keepalive ineffective**: Keepalive settings exist in code but don't work since connections are recreated each time
3. **Multiple connections for concurrent calls**: Multiple simultaneous RPC calls to the same Agent create separate connections

**Impact:**
- Over 30 methods in `AgentClient` all use this pattern
- Performance degradation during scheduling when making frequent RPC calls to many Agents

## Current Design

### AgentRPCCache Structure

```python
class AgentRPCCache:
    _cache: dict[AgentId, tuple[str, PublicKey | None]]  # Only metadata cached

    @actxmgr
    async def rpc_context(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> AsyncIterator[PeerInvoker]:
        agent_addr, agent_public_key = await self.get_rpc_args(agent_id)
        # ... authentication handler setup ...

        peer = PeerInvoker(...)
        async with peer:  # New connection every time
            yield peer
```

### AgentClient Structure

```python
class AgentClient:
    def __init__(
        self,
        agent_cache: AgentRPCCache,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> None:
        self._agent_cache = agent_cache
        self._agent_id = agent_id

    @actxmgr
    async def _with_connection(self) -> AsyncIterator[PeerInvoker]:
        async with self._agent_cache.rpc_context(self._agent_id, ...) as rpc:
            yield rpc

    async def health(self) -> Mapping[str, Any]:
        async with self._with_connection() as rpc:  # New connection every time
            return await rpc.call.health()
```

### callosum Peer Behavior Analysis

- `__aenter__`: Establishes connection, starts send/recv loops
- `__aexit__`: Closes connection
- `request_id = (method, order_key, client_seq_id)` based response mapping
- **Conclusion: A single PeerInvoker can be safely shared among multiple callers with proper response mapping**

## Proposed Design

### Design Principles

1. **Minimize existing code changes**: Do not modify `AgentRPCCache`
2. **Simple implementation**: Implement only the minimum required functionality
3. **Change AgentClient behavior**: Store and reuse `PeerInvoker` internally
4. **Separation of concerns**: `acquire()` only acquires clients, `health_check_loop` manages connections
5. **Future goal**: Decouple `AgentRPCCache` dependency (currently used as-is)

### File Structure

```
src/ai/backend/manager/
├── clients/
│   └── agent/
│       ├── __init__.py
│       ├── abc.py             # New: BackendAIClient ABC
│       ├── client.py          # Modified AgentClient
│       ├── pool.py            # New: AgentClientPool
│       └── types.py           # New: AgentPoolSpec
├── errors/
│   └── agent.py               # New: AgentConnectionUnavailable
```

### Exception Definition

```python
# manager/errors/agent.py
from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import AgentId


class AgentConnectionUnavailable(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when Agent connection is unavailable"""

    error_type = "https://api.backend.ai/probs/agent-connection-unavailable"
    error_title = "Agent connection unavailable."

    def __init__(self, agent_id: AgentId, reason: str) -> None:
        self.agent_id = agent_id
        self.reason = reason
        super().__init__(f"Agent {agent_id} connection unavailable: {reason}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
```

### Configuration Dataclass

```python
# manager/clients/agent/types.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPoolSpec:
    """AgentClientPool configuration"""
    health_check_interval: float  # Periodic health check interval (seconds)
    failure_threshold: int        # Number of failures before marking unhealthy
    recovery_timeout: float       # Time to wait before removing unhealthy connection (seconds)
```

### BackendAIClient ABC

```python
# manager/clients/agent/abc.py
from __future__ import annotations

from abc import ABC, abstractmethod


class BackendAIClient(ABC):
    """Abstract base class for Backend.AI clients"""

    @abstractmethod
    async def connect(self) -> None:
        """Start connection"""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close connection"""
        raise NotImplementedError
```

### AgentClient Changes

```python
# manager/clients/agent/client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.types import AgentId
from ai.backend.manager.agent_cache import PeerInvoker

from .abc import BackendAIClient


class AgentClient(BackendAIClient):
    """
    Agent RPC client.

    Created by the Pool and reuses internal PeerInvoker.
    """

    def __init__(self, peer: PeerInvoker, agent_id: AgentId) -> None:
        self._peer = peer
        self._agent_id = agent_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    async def connect(self) -> None:
        """Start connection"""
        await self._peer.__aenter__()

    async def close(self) -> None:
        """Close connection"""
        try:
            await self._peer.__aexit__(None, None, None)
        except Exception:
            pass

    async def ping(self) -> None:
        """Ping for connection status check"""
        await self._peer.call.ping()

    async def health(self) -> Mapping[str, Any]:
        return await self._peer.call.health()

    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        return await self._peer.call.gather_hwinfo()

    # ... remaining methods also use self._peer.call.xxx()
```

### Internal Cache Entry

```python
# manager/clients/agent/pool.py (internal use)
@dataclass(slots=True)
class _CachedEntry:
    """Cache entry managed internally by Pool"""
    client: AgentClient
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None  # Time when marked unhealthy
```

### AgentClientPool Implementation

```python
# manager/clients/agent/pool.py
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import zmq
from aiotools import cancel_and_wait

from ai.backend.common import msgpack
from ai.backend.common.auth import ManagerAuthHandler
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport

from .client import AgentClient
from .types import AgentPoolSpec

if TYPE_CHECKING:
    from ai.backend.manager.agent_cache import AgentRPCCache, PeerInvoker

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Connection-related error types
CONNECTION_ERRORS = (
    ConnectionError,
    asyncio.TimeoutError,
    OSError,
)


@dataclass(slots=True)
class _CachedEntry:
    client: AgentClient
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None


class AgentClientPool:
    """
    Agent RPC connection pool.

    Connection state management:
    1. Periodic health check: Verify connection status via ping, remove if unrecoverable
    2. Usage-time failure tracking: Increment failure_count on connection errors during acquire()

    Separation of concerns:
    - acquire(): Only acquires clients (raises exception if unhealthy)
    - health_check_loop: Manages connection state and removal
    """

    def __init__(
        self,
        agent_cache: AgentRPCCache,
        spec: AgentPoolSpec,
    ) -> None:
        self._agent_cache = agent_cache
        self._spec = spec
        self._entries: dict[AgentId, _CachedEntry] = {}
        self._lock = asyncio.Lock()

        # Start background task in constructor
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="AgentClientPool._health_check_loop",
        )

    async def close(self) -> None:
        """Close the pool"""
        await cancel_and_wait(self._health_check_task)

        async with self._lock:
            for entry in self._entries.values():
                await entry.client.close()
            self._entries.clear()

    @asynccontextmanager
    async def acquire(self, agent_id: AgentId) -> AsyncIterator[AgentClient]:
        """
        Acquire and use an Agent client.

        On connection errors during use, increments failure count and
        marks connection as unhealthy if threshold exceeded.
        Unhealthy connections raise exceptions (removal handled by health_check_loop).

        Business logic errors do not affect failure count.
        """
        client = await self._get_or_create(agent_id)
        try:
            yield client
        except CONNECTION_ERRORS as e:
            self._record_failure(agent_id)
            raise
        except Exception:
            # Non-connection errors don't increment failure count
            raise
        else:
            self._record_success(agent_id)

    def invalidate(self, agent_id: AgentId) -> None:
        """
        Mark a specific Agent connection as unhealthy.

        Called from event handlers like Agent exit or heartbeat failure.
        Actual removal is performed by health_check_loop.
        """
        entry = self._entries.get(agent_id)
        if entry is not None:
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()

    async def _get_or_create(self, agent_id: AgentId) -> AgentClient:
        """Return healthy client, create if not exists"""
        async with self._lock:
            entry = self._entries.get(agent_id)

            # Raise exception if unhealthy (removal handled by health_check_loop)
            if entry is not None and not entry.is_healthy:
                from ai.backend.manager.errors.agent import AgentConnectionUnavailable
                raise AgentConnectionUnavailable(agent_id, "connection unhealthy")

            # Create new connection if not exists
            if entry is None:
                entry = await self._create_entry(agent_id)
                self._entries[agent_id] = entry

            return entry.client

    async def _create_entry(self, agent_id: AgentId) -> _CachedEntry:
        """Create new entry (called within lock)"""
        try:
            agent_addr, agent_public_key = await self._agent_cache.get_rpc_args(agent_id)
        except ValueError as e:
            from ai.backend.manager.errors.agent import AgentConnectionUnavailable
            raise AgentConnectionUnavailable(agent_id, str(e)) from e

        # Authentication handler setup
        if agent_public_key:
            auth_handler = ManagerAuthHandler(
                "local",
                agent_public_key,
                self._agent_cache.manager_public_key,
                self._agent_cache.manager_secret_key,
            )
        else:
            auth_handler = None

        peer = PeerInvoker(
            connect=ZeroMQAddress(agent_addr),
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            transport_opts={
                "zsock_opts": {
                    zmq.TCP_KEEPALIVE: 1,
                    zmq.TCP_KEEPALIVE_IDLE: 60,
                    zmq.TCP_KEEPALIVE_INTVL: 20,
                    zmq.TCP_KEEPALIVE_CNT: 3,
                },
            },
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
        )

        client = AgentClient(peer, agent_id)
        try:
            await client.connect()
        except Exception as e:
            from ai.backend.manager.errors.agent import AgentConnectionUnavailable
            raise AgentConnectionUnavailable(agent_id, str(e)) from e

        return _CachedEntry(
            client=client,
            is_healthy=True,
            failure_count=0,
            unhealthy_since=None,
        )

    def _record_failure(self, agent_id: AgentId) -> None:
        """Record failure on connection error, mark unhealthy if threshold exceeded"""
        entry = self._entries.get(agent_id)
        if entry is None:
            return

        entry.failure_count += 1
        if entry.failure_count >= self._spec.failure_threshold:
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
            log.debug(
                "Agent {} marked unhealthy after {} connection failures",
                agent_id,
                entry.failure_count,
            )

    def _record_success(self, agent_id: AgentId) -> None:
        """Reset state on success"""
        entry = self._entries.get(agent_id)
        if entry is not None:
            entry.failure_count = 0
            entry.is_healthy = True
            entry.unhealthy_since = None

    async def _health_check_loop(self) -> None:
        """Periodically health check all connections"""
        while True:
            await asyncio.sleep(self._spec.health_check_interval)
            await self._check_all_health()

    async def _check_all_health(self) -> None:
        """Health check all connections (using asyncio.gather)"""
        async with self._lock:
            entries = list(self._entries.items())

        if not entries:
            return

        await asyncio.gather(
            *[self._check_one_health(agent_id, entry) for agent_id, entry in entries],
            return_exceptions=True,
        )

    async def _check_one_health(self, agent_id: AgentId, entry: _CachedEntry) -> None:
        """Health check single connection and remove if unrecoverable"""
        try:
            async with asyncio.timeout(5.0):
                await entry.client.ping()
            # ping success → recover
            entry.is_healthy = True
            entry.failure_count = 0
            entry.unhealthy_since = None
        except Exception:
            # ping failure → mark unhealthy
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
                log.debug("Health check failed for agent {}", agent_id)

        # Remove if recovery_timeout exceeded
        if (
            not entry.is_healthy
            and entry.unhealthy_since is not None
            and time.perf_counter() - entry.unhealthy_since > self._spec.recovery_timeout
        ):
            async with self._lock:
                if agent_id in self._entries:
                    await entry.client.close()
                    del self._entries[agent_id]
            log.info(
                "Removed unrecoverable connection for agent {} after {}s",
                agent_id,
                self._spec.recovery_timeout,
            )
```

### Usage Example

```python
# Usage in Sokovan scheduler
class SchedulingController:
    def __init__(self, agent_cache: AgentRPCCache, ...):
        spec = AgentPoolSpec(
            health_check_interval=30.0,
            failure_threshold=3,
            recovery_timeout=60.0,
        )
        self._agent_pool = AgentClientPool(agent_cache, spec)

    async def close(self):
        await self._agent_pool.close()

    async def check_agent_status(self, agent_id: AgentId) -> dict:
        async with self._agent_pool.acquire(agent_id) as client:
            return await client.health()

    def on_agent_lost(self, agent_id: AgentId) -> None:
        """Event handler for Agent heartbeat failure, etc."""
        self._agent_pool.invalidate(agent_id)
```

## Migration / Compatibility

### Backward Compatibility

- No changes to existing `AgentRPCCache`
- Existing `AgentClient` usage can be maintained (outside Sokovan)
- **Within Sokovan scheduler, only `AgentClientPool` is used instead of `AgentRPCCache`**

### Breaking Changes

- `AgentClient` constructor signature changed: `(agent_cache, agent_id)` → `(peer, agent_id)`
- Code directly creating `AgentClient` instances needs modification

### Migration Steps

1. Add `manager/errors/agent.py`
2. Add `manager/clients/agent/abc.py`
3. Add `manager/clients/agent/types.py`
4. Add `manager/clients/agent/pool.py`
5. Modify `manager/clients/agent/client.py`
6. Use `AgentClientPool` in Sokovan scheduler

## Implementation Plan

### Phase 1: Basic Structure

1. `manager/errors/agent.py` - Exception class definition
2. `manager/clients/agent/abc.py` - `BackendAIClient` ABC
3. `manager/clients/agent/types.py` - `AgentPoolSpec`
4. `manager/clients/agent/pool.py` - Basic `AgentClientPool` implementation

### Phase 2: AgentClient Changes

1. Inherit from `BackendAIClient` ABC
2. Implement `connect()`, `close()` methods
3. Remove `_with_connection()`
4. Use `self._peer.call.xxx()` directly in each method

### Phase 3: Integration

1. Integrate `AgentClientPool` into Sokovan scheduler
2. Connect Agent events (exit, heartbeat failure) with `invalidate()`

### Phase 4: Testing

1. Write unit tests
2. Integration tests

## Open Questions

1. **Health check interval**
   - Is 30 seconds appropriate?
   - May cause load with many Agents

2. **recovery_timeout value**
   - Is 60 seconds appropriate?
   - Temporary network issue recovery time vs. fast reconnection

3. **failure_threshold value**
   - Is 3 appropriate?
   - Distinguishing temporary issues vs. actual connection problems

4. **Generalization timing**
   - Generalize to `common/clients/connection_pool.py` after behavior verification?

## Future Work

- **Decouple `AgentRPCCache` dependency**: Currently receives `agent_cache`, but future work to separate connection creation logic and remove dependency
- **Make `_create_entry` injectable**: Apply factory pattern to allow external injection of client creation logic during generalization

## References

- [common/clients/http_client/client_pool.py](../src/ai/backend/common/clients/http_client/client_pool.py) - Reference pattern
- [callosum RPC library](https://github.com/lablup/callosum)
- BA-3813: Manager Client Connection Pooling Improvements (Epic)
- BA-3815: Implement Agent RPC Connection Pool
