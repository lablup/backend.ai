---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2025-01-11
Created-Version: 25.1.0
Target-Version:
Implemented-Version:
---

# Agent RPC 연결 풀링

## Related Issues

- JIRA: BA-3814, BA-3815
- Epic: BA-3813

## Motivation

현재 Manager에서 Agent로 RPC 호출 시 매번 새로운 ZeroMQ 연결을 생성하고 있다.

```python
# AgentRPCCache.rpc_context() - 매 호출마다 새 PeerInvoker 생성
peer = PeerInvoker(
    connect=ZeroMQAddress(agent_addr),
    transport=ZeroMQRPCTransport,
    ...
)
async with peer:  # 연결 생성
    yield peer
# 연결 종료
```

**문제점:**
1. **연결 오버헤드**: ZeroMQ 연결 설정 → CurveZMQ 인증 → RPC 호출 → 연결 종료가 매번 발생
2. **TCP Keepalive 무의미**: 코드에 keepalive 설정이 있지만, 매번 새 연결이라 실제로 작동하지 않음
3. **동시 호출 시 다중 연결**: 한 Agent에 여러 RPC 동시 호출 시 각각 별도 연결 생성

**영향 범위:**
- `AgentClient`의 30개 이상 메서드가 모두 이 패턴 사용
- 스케줄링 시 다수 Agent에 대한 빈번한 RPC 호출에서 성능 저하

## Current Design

### AgentRPCCache 구조

```python
class AgentRPCCache:
    _cache: dict[AgentId, tuple[str, PublicKey | None]]  # 메타데이터만 캐시

    @actxmgr
    async def rpc_context(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> AsyncIterator[PeerInvoker]:
        agent_addr, agent_public_key = await self.get_rpc_args(agent_id)
        # ... 인증 핸들러 설정 ...

        peer = PeerInvoker(...)
        async with peer:  # 매번 새 연결
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
        async with self._with_connection() as rpc:  # 매번 새 연결
            return await rpc.call.health()
```

### callosum Peer 동작 분석

- `__aenter__`: 연결 설정, send/recv 루프 시작
- `__aexit__`: 연결 종료
- `request_id = (method, order_key, client_seq_id)` 기반 응답 매핑
- **결론: 하나의 PeerInvoker를 여러 호출자가 공유해도 응답 매핑 정상 동작**

## Proposed Design

### 설계 원칙

1. **기존 코드 변경 최소화**: `AgentRPCCache` 수정하지 않음
2. **간결한 구현**: 필요한 최소한의 기능만 구현
3. **AgentClient 동작 방식 변경**: `PeerInvoker`를 내부에 보관하고 재사용
4. **관심사 분리**: `acquire()`는 클라이언트 획득만, `health_check_loop`가 연결 관리 책임
5. **향후 목표**: `AgentRPCCache` 의존성 분리 (현재는 그대로 사용)

### 파일 구조

```
src/ai/backend/manager/
├── clients/
│   └── agent/
│       ├── __init__.py
│       ├── abc.py             # 새로 추가: BackendAIClient ABC
│       ├── client.py          # AgentClient 수정
│       ├── pool.py            # 새로 추가: AgentClientPool
│       └── types.py           # 새로 추가: AgentPoolSpec
├── errors/
│   └── agent.py               # 새로 추가: AgentConnectionUnavailable
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
    """Agent 연결을 사용할 수 없을 때 발생"""

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

### 설정 데이터 클래스

```python
# manager/clients/agent/types.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPoolSpec:
    """AgentClientPool 설정"""
    health_check_interval: float  # 주기적 health check 간격 (초)
    failure_threshold: int        # unhealthy 마킹까지 실패 횟수
    recovery_timeout: float       # unhealthy 지속 시 삭제까지 대기 시간 (초)
```

### BackendAIClient ABC

```python
# manager/clients/agent/abc.py
from __future__ import annotations

from abc import ABC, abstractmethod


class BackendAIClient(ABC):
    """Backend.AI 클라이언트 추상 베이스 클래스"""

    @abstractmethod
    async def connect(self) -> None:
        """연결 시작"""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """연결 종료"""
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
    Agent RPC 클라이언트.

    Pool에서 생성되며, 내부 PeerInvoker를 재사용한다.
    """

    def __init__(self, peer: PeerInvoker, agent_id: AgentId) -> None:
        self._peer = peer
        self._agent_id = agent_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    async def connect(self) -> None:
        """연결 시작"""
        await self._peer.__aenter__()

    async def close(self) -> None:
        """연결 종료"""
        try:
            await self._peer.__aexit__(None, None, None)
        except Exception:
            pass

    async def ping(self) -> None:
        """연결 상태 확인용 ping"""
        await self._peer.call.ping()

    async def health(self) -> Mapping[str, Any]:
        return await self._peer.call.health()

    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        return await self._peer.call.gather_hwinfo()

    # ... 나머지 메서드들도 동일하게 self._peer.call.xxx() 사용
```

### 내부 캐시 엔트리

```python
# manager/clients/agent/pool.py (내부용)
@dataclass(slots=True)
class _CachedEntry:
    """Pool 내부에서 관리하는 캐시 엔트리"""
    client: AgentClient
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None  # unhealthy 시작 시간
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

# connection 관련 에러 타입
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
    Agent RPC 연결 풀.

    연결 상태 관리:
    1. 주기적 health check: ping으로 연결 상태 확인, 복구 불가 시 삭제
    2. 사용 시점 실패 추적: acquire() 사용 중 connection error 시 failure_count 증가

    관심사 분리:
    - acquire(): 클라이언트 획득만 (unhealthy면 예외)
    - health_check_loop: 연결 상태 관리 및 삭제
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

        # 생성자에서 백그라운드 태스크 시작
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="AgentClientPool._health_check_loop",
        )

    async def close(self) -> None:
        """풀 종료"""
        await cancel_and_wait(self._health_check_task)

        async with self._lock:
            for entry in self._entries.values():
                await entry.client.close()
            self._entries.clear()

    @asynccontextmanager
    async def acquire(self, agent_id: AgentId) -> AsyncIterator[AgentClient]:
        """
        Agent 클라이언트를 획득하여 사용.

        사용 중 connection error 발생 시 실패 카운트를 증가시키고,
        threshold 초과 시 연결을 unhealthy로 마킹한다.
        unhealthy 연결은 예외를 발생시킨다 (삭제는 health_check_loop에서).

        비즈니스 로직 에러는 failure count에 영향을 주지 않는다.
        """
        client = await self._get_or_create(agent_id)
        try:
            yield client
        except CONNECTION_ERRORS as e:
            self._record_failure(agent_id)
            raise
        except Exception:
            # connection error가 아닌 경우 failure count 증가 안 함
            raise
        else:
            self._record_success(agent_id)

    def invalidate(self, agent_id: AgentId) -> None:
        """
        특정 Agent 연결을 unhealthy로 마킹.

        Agent exit, heartbeat 실패 등의 이벤트에서 호출.
        실제 삭제는 health_check_loop에서 수행.
        """
        entry = self._entries.get(agent_id)
        if entry is not None:
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()

    async def _get_or_create(self, agent_id: AgentId) -> AgentClient:
        """healthy한 클라이언트 반환, 없으면 생성"""
        async with self._lock:
            entry = self._entries.get(agent_id)

            # unhealthy면 예외 발생 (삭제는 health_check_loop에서)
            if entry is not None and not entry.is_healthy:
                from ai.backend.manager.errors.agent import AgentConnectionUnavailable
                raise AgentConnectionUnavailable(agent_id, "connection unhealthy")

            # 연결 없으면 새로 생성
            if entry is None:
                entry = await self._create_entry(agent_id)
                self._entries[agent_id] = entry

            return entry.client

    async def _create_entry(self, agent_id: AgentId) -> _CachedEntry:
        """새 엔트리 생성 (lock 내부에서 호출)"""
        try:
            agent_addr, agent_public_key = await self._agent_cache.get_rpc_args(agent_id)
        except ValueError as e:
            from ai.backend.manager.errors.agent import AgentConnectionUnavailable
            raise AgentConnectionUnavailable(agent_id, str(e)) from e

        # 인증 핸들러 설정
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
        """connection error 시 실패 기록 및 threshold 초과 시 unhealthy 마킹"""
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
        """성공 시 상태 리셋"""
        entry = self._entries.get(agent_id)
        if entry is not None:
            entry.failure_count = 0
            entry.is_healthy = True
            entry.unhealthy_since = None

    async def _health_check_loop(self) -> None:
        """주기적으로 모든 연결 health check"""
        while True:
            await asyncio.sleep(self._spec.health_check_interval)
            await self._check_all_health()

    async def _check_all_health(self) -> None:
        """모든 연결 health check (asyncio.gather 사용)"""
        async with self._lock:
            entries = list(self._entries.items())

        if not entries:
            return

        await asyncio.gather(
            *[self._check_one_health(agent_id, entry) for agent_id, entry in entries],
            return_exceptions=True,
        )

    async def _check_one_health(self, agent_id: AgentId, entry: _CachedEntry) -> None:
        """단일 연결 health check 및 복구 불가 시 삭제"""
        try:
            async with asyncio.timeout(5.0):
                await entry.client.ping()
            # ping 성공 → 복구
            entry.is_healthy = True
            entry.failure_count = 0
            entry.unhealthy_since = None
        except Exception:
            # ping 실패 → unhealthy 마킹
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
                log.debug("Health check failed for agent {}", agent_id)

        # recovery_timeout 초과 시 삭제
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

### 사용 예시

```python
# Sokovan 스케줄러에서 사용
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
        """Agent heartbeat 실패 등의 이벤트 핸들러"""
        self._agent_pool.invalidate(agent_id)
```

## Migration / Compatibility

### Backward Compatibility

- 기존 `AgentRPCCache` 변경 없음
- 기존 `AgentClient` 사용처는 그대로 유지 가능 (Sokovan 외부)
- **Sokovan 스케줄러 하위에서는 `AgentRPCCache` 대신 `AgentClientPool`만 사용**

### Breaking Changes

- `AgentClient` 생성자 시그니처 변경: `(agent_cache, agent_id)` → `(peer, agent_id)`
- 기존 `AgentClient` 직접 생성 코드가 있다면 수정 필요

### Migration Steps

1. `manager/errors/agent.py` 추가
2. `manager/clients/agent/abc.py` 추가
3. `manager/clients/agent/types.py` 추가
4. `manager/clients/agent/pool.py` 추가
5. `manager/clients/agent/client.py` 수정
6. Sokovan 스케줄러에서 `AgentClientPool` 사용

## Implementation Plan

### Phase 1: 기본 구조

1. `manager/errors/agent.py` - 예외 클래스 정의
2. `manager/clients/agent/abc.py` - `BackendAIClient` ABC
3. `manager/clients/agent/types.py` - `AgentPoolSpec`
4. `manager/clients/agent/pool.py` - `AgentClientPool` 기본 구현

### Phase 2: AgentClient 변경

1. `BackendAIClient` ABC 상속
2. `connect()`, `close()` 메서드 구현
3. `_with_connection()` 제거
4. 각 메서드에서 `self._peer.call.xxx()` 직접 사용

### Phase 3: 통합

1. Sokovan 스케줄러에 `AgentClientPool` 통합
2. Agent 이벤트(exit, heartbeat 실패)와 `invalidate()` 연동

### Phase 4: 테스트

1. 단위 테스트 작성
2. 통합 테스트

## Open Questions

1. **Health check 주기**
   - 30초가 적절한가?
   - Agent 수가 많으면 부하가 될 수 있음

2. **recovery_timeout 값**
   - 60초가 적절한가?
   - 일시적 네트워크 문제 복구 시간 vs 빠른 재연결

3. **failure_threshold 값**
   - 3회가 적절한가?
   - 일시적 문제 vs 실제 연결 불량 구분

4. **일반화 시점**
   - 동작 검증 후 `common/clients/connection_pool.py`로 일반화할 것인가?

## Future Work

- **`AgentRPCCache` 의존성 분리**: 현재는 `agent_cache`를 받지만, 향후 연결 생성 로직을 분리하여 의존성 제거
- **`_create_entry` 주입 가능하도록**: 일반화 시 클라이언트 생성 로직을 외부에서 주입받을 수 있도록 팩토리 패턴 적용

## References

- [common/clients/http_client/client_pool.py](../src/ai/backend/common/clients/http_client/client_pool.py) - 참조 패턴
- [callosum RPC 라이브러리](https://github.com/lablup/callosum)
- BA-3813: Manager Client Connection Pooling Improvements (Epic)
- BA-3815: Implement Agent RPC Connection Pool
