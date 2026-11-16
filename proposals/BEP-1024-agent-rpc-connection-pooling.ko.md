# Agent RPC 연결 풀링

## 관련 이슈

- JIRA: BA-3814, BA-3815
- Epic: BA-3813

## 동기

현재 Manager 는 Agent 로 보내는 RPC 호출마다 ZeroMQ 연결을 새로 생성한다.

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

**문제:**
1. **연결 비용**: ZeroMQ 연결 수립 → CurveZMQ 인증 → RPC 호출 → 연결 해제가 매번 일어난다
2. **TCP Keepalive 가 동작하지 않는다**: Keepalive 설정은 코드에 있지만 연결을 매번 새로 생성하므로 효과가 없다
3. **동시 호출마다 연결이 늘어난다**: 같은 Agent 로 보내는 RPC 호출이 동시에 여러 개면 각각 별도 연결을 생성한다

**영향:**
- `AgentClient` 의 30개 이상 method 가 모두 이 패턴을 사용한다
- 많은 Agent 로 RPC 를 자주 호출하는 스케줄링 중에 성능이 떨어진다

## 현재 설계

### AgentRPCCache 구조

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

### AgentClient 구조

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

### callosum Peer 동작 분석

- `__aenter__`: 연결을 수립하고 송수신 loop 를 시작한다
- `__aexit__`: 연결을 닫는다
- `request_id = (method, order_key, client_seq_id)` 를 기준으로 응답을 매핑한다
- **결론: 응답 매핑이 제대로 되면 PeerInvoker 하나를 여러 caller 가 안전하게 공유할 수 있다**

## 제안 설계

### 설계 원칙

1. **기존 코드 변경 최소화**: `AgentRPCCache` 는 수정하지 않는다
2. **단순한 구현**: 필요한 최소 기능만 구현한다
3. **AgentClient 동작 변경**: `PeerInvoker` 를 내부에 보관하고 재사용한다
4. **관심사 분리**: `acquire()` 는 client 를 획득하는 일만 하고 `health_check_loop` 가 연결을 관리한다
5. **향후 목표**: `AgentRPCCache` 의존성을 분리한다. 현재는 그대로 사용한다

### 파일 구조

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

### 예외 정의

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

### 설정 dataclass

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

### AgentClient 변경

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

### 내부 cache 항목

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

### AgentClientPool 구현

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

### 사용 예

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

## 이전 / 호환성

### 이전 버전 호환성

- 기존 `AgentRPCCache` 는 수정하지 않는다
- Sokovan 밖에서는 기존 `AgentClient` 사용 방식을 유지할 수 있다
- **Sokovan scheduler 안에서는 `AgentRPCCache` 대신 `AgentClientPool` 만 사용한다**

### 호환성을 깨는 변경

- `AgentClient` 생성자 signature 가 `(agent_cache, agent_id)` 에서 `(peer, agent_id)` 로 변경된다
- `AgentClient` instance 를 직접 생성하는 코드는 수정해야 한다

### 이전 단계

1. `manager/errors/agent.py` 를 추가한다
2. `manager/clients/agent/abc.py` 를 추가한다
3. `manager/clients/agent/types.py` 를 추가한다
4. `manager/clients/agent/pool.py` 를 추가한다
5. `manager/clients/agent/client.py` 를 수정한다
6. Sokovan scheduler 에서 `AgentClientPool` 을 사용한다

## 구현 계획

### 1단계: 기본 구조

1. `manager/errors/agent.py` - 예외 class 정의
2. `manager/clients/agent/abc.py` - `BackendAIClient` ABC
3. `manager/clients/agent/types.py` - `AgentPoolSpec`
4. `manager/clients/agent/pool.py` - `AgentClientPool` 기본 구현

### 2단계: AgentClient 변경

1. `BackendAIClient` ABC 를 상속한다
2. `connect()`, `close()` method 를 구현한다
3. `_with_connection()` 를 제거한다
4. 각 method 에서 `self._peer.call.xxx()` 를 직접 사용한다

### 3단계: 통합

1. Sokovan scheduler 에 `AgentClientPool` 를 통합한다
2. Agent event 인 exit, heartbeat failure 를 `invalidate()` 에 연결한다

### 4단계: 테스트

1. unit test 를 작성한다
2. 통합 테스트

## 열린 질문

1. **health check 주기**
   - 30초의 적절 여부에 대한 결정이 필요하다
   - Agent 가 많으면 부하가 생길 수 있다

2. **recovery_timeout 값**
   - 60초의 적절 여부에 대한 결정이 필요하다
   - 일시적인 network 문제의 복구 시간과 빠른 재연결 사이의 균형

3. **failure_threshold 값**
   - 3의 적절 여부에 대한 결정이 필요하다
   - 일시적인 문제와 실제 연결 문제를 구분하는 기준

4. **일반화 시점**
   - 동작을 검증한 뒤 `common/clients/connection_pool.py` 로 일반화한다

## 향후 작업

- **`AgentRPCCache` 의존성 분리**: 현재는 `agent_cache` 를 받지만, 앞으로 연결 생성 로직을 분리하고 의존성을 제거한다
- **`_create_entry` 를 주입 가능하게 변경**: 일반화할 때 client 생성 로직을 외부에서 주입할 수 있도록 factory 패턴을 적용한다

## 참고

- [common/clients/http_client/client_pool.py](../src/ai/backend/common/clients/http_client/client_pool.py) - 참고 패턴
- [callosum RPC 라이브러리](https://github.com/lablup/callosum)
- BA-3813: Manager client 연결 풀링 개선 (Epic)
- BA-3815: Agent RPC 연결 풀 구현
