<!-- context-for-ai
type: master-bep
scope: Unified service discovery design for all Backend.AI components
detail-docs: [data-model.md, config-schema.md, event-registration.md, cli-migration.md, client-pool.md]
key-decisions:
  - Redis Event as transport channel, DB as authoritative store
  - role+scope based multi-endpoint model
  - Config-driven endpoint registration (with CLI migration tool)
  - Self-preservation for failure resilience (Eureka pattern)
  - Agent multi-agent: minimize SD scope (sub-concept)
  - instance_id: SD config first, component-specific fallback, auto-generation
implementation: 4 phases, BA-4315~4318
-->

# DB 기반 서비스 카탈로그를 사용하는 통합 서비스 디스커버리

## 관련 이슈

- JIRA Epic: BA-4313
- JIRA: BA-4314 (BEP), BA-4315 (기반), BA-4316 (CLI 마이그레이션), BA-4317 (런타임), BA-4318 (클라이언트 pool)

## 상세 문서 색인

| 문서 | 내용 | 관련 단계 |
|----------|----------|---------------|
| [데이터 모델](BEP-1046/data-model.md) | DB DDL, 역할, 스코프 정의와 세부 사항 | 1단계 |
| [설정 스키마](BEP-1046/config-schema.md) | TOML 설정 예시, pydantic model, 컴포넌트별 instance_id 규칙 | 1단계 |
| [event 및 등록 흐름](BEP-1046/event-registration.md) | event 타입 정의, 등록 흐름 세부 사항, config_hash 최적화, 컴포넌트별 capability | 1단계, 3단계 |
| [CLI 마이그레이션](BEP-1046/cli-migration.md) | CLI 사용법, 컴포넌트별 매핑 규칙, 출력 예시 | 2단계 |
| [클라이언트 pool 과 조회 API](BEP-1046/client-pool.md) | ServiceCatalogCache, SDClientPool, 기존 주소 전환 전략, GraphQL 조회 API | 4단계 |

## 동기

Backend.AI 의 현재 서비스 디스커버리는 컴포넌트마다 다른 방식을 사용하고 일관성이 없으며, 서비스 상태를 조회해 사용자에게 노출하기 어렵다.

**현재 상태:**

| 컴포넌트 | 서비스 디스커버리 등록 | 다른 서비스가 찾는 방법 |
|-----------|----------------|-------------------------------|
| Agent | 에이전트 heartbeat event → Manager → `agents` table | Manager 가 DB 를 조회 |
| Manager | `ServiceDiscoveryLoop`(etcd/Valkey) | Webserver 가 설정에 주소를 직접 지정 |
| Storage Proxy | `ServiceDiscoveryLoop`(etcd/Valkey) | Manager 가 etcd 설정에서 주소를 읽음 |
| App Proxy Coordinator | `ServiceDiscoveryLoop`(Valkey 전용) | Manager 가 `scaling_groups` row 의 `wsproxy_addr` 를 사용 |
| App Proxy Worker | `ServiceDiscoveryLoop`(Valkey 전용) | Worker 가 Coordinator 에 연결을 요청 |
| Webserver | 등록하지 않음 | 이 서비스를 찾아야 하는 서버가 없음 |

**문제:**

1. **조회 방식 부적절**: Valkey hash 나 etcd 에 저장한 서비스 디스커버리 데이터를 구조화된 방식으로 사용자에게 노출하기 어렵다
2. **일관성 부족**: Agent 는 event 를, 나머지는 `ServiceDiscoveryLoop` 를 사용한다. App Proxy 주소는 자원 그룹 row 에, Manager 주소는 설정에 하드코딩하므로 방식이 모두 다르다
3. **엔드포인트 모델 없음**: 서비스는 역할(API, RPC, 지표)과 네트워크 맥락(container, cluster, public)에 따라 여러 엔드포인트를 가지지만 이를 표현할 구조가 없다
4. **클라이언트 pool 미통합**: `AgentClientPool` 과 `ClientPool` 이 서비스 디스커버리에 연결되지 않아 주소를 수동으로 주입해야 한다
5. **장애 대응 부족**: Valkey 나 etcd 장애 시 서비스 디스커버리 데이터가 유실될 위험이 있다

## 현재 설계

<details>
<summary>현재 ServiceDiscoveryLoop 코드(참조)</summary>

```python
class ServiceDiscoveryLoop:
    async def start(self):
        await self._service_discovery.register(self._service_metadata)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())  # 60s

    async def stop(self):
        await self._service_discovery.unregister(...)
```

- Valkey backend: `service_discovery.{group}.{id}` key 에 hash 를 저장하고 TTL 3분을 둔다
- etcd backend: `ai/backend/service_discovery/{group}/{id}` prefix 에 저장한다

</details>

<details>
<summary>현재 엔드포인트 모델(참조)</summary>

현재 `ServiceEndpoint` 는 주소 하나만 표현하지만 컴포넌트마다 실제로 여러 주소를 가진다.

- **Agent**: `rpc_listen_addr`, `advertised_rpc_addr`, `service_addr`, `announce_internal_addr`
- **Storage Proxy**: `client.service_addr`, `manager.service_addr`, `manager.announce_addr`, `manager.announce_internal_addr`
- **App Proxy Worker**: `api_bind_addr`, `api_advertised_addr`, `wildcard_domain.bind_addr`, `port_proxy.bind_host`

</details>

- Agent 는 Valkey Stream anycast 로 `AgentHeartbeatEvent` 를 발행하고 Manager 가 `agents` table 로 동기화한다
- 다른 컴포넌트는 `ServiceDiscoveryLoop` 로 Valkey/etcd 에 등록한다
- 엔드포인트 모델은 단일 주소 구조라 여러 주소를 표현할 수 없다

## 제안 설계

### 설계 원칙

1. **Valkey event 를 전송 채널로 사용**: 기존 Valkey Stream event 인프라를 재사용한다
2. **DB 를 기준 저장소로 사용**: SQL 조회, GraphQL 노출, 감사 추적이 가능해진다
3. **역할과 스코프 기반 다중 엔드포인트**: 엔드포인트의 용도인 역할과 접근 위치인 스코프로 구분한다
4. **설정 기반**: `[service-discovery.endpoints]` section 으로 명시적으로 선언한다. CLI 마이그레이션 도구를 제공한다
5. **자기 보존**: backend 장애 시 마지막으로 확인한 상태를 고정해 서비스 제거를 방지한다(Netflix Eureka 패턴)

### 데이터 모델

`service_catalog` 와 `service_catalog_endpoint` table 로 구성한다. 각 서비스는 `(service_group, instance_id)` 로 식별하고, 엔드포인트는 `(role, scope)` 조합으로 여러 주소를 표현한다.

- **role**: 엔드포인트의 기능 목적. `api`, `rpc`, `metrics`, `client-api`, `internal-api`
- **scope**: 네트워크 접근 맥락. `cluster`, `container`, `public`

> DDL 과 역할, 스코프 세부 사항은 [데이터 모델 세부 사항](BEP-1046/data-model.md)을 참조한다.

### instance_id 전략

서비스 재시작에도 유지되는 안정적인 식별자다. 설정 `instance-id` 를 우선 사용하고, 없으면 컴포넌트별 규칙을 따른다. 인스턴스가 여러 개인 서비스(Storage Proxy, App Proxy Coordinator)는 설정에 반드시 지정해야 한다.

> 컴포넌트별 규칙과 코드는 [설정 스키마](BEP-1046/config-schema.md#instance_id-strategy)를 참조한다.

### 등록 흐름 개요

```
Startup → Read config + compute config_hash
        → Publish ServiceRegisteredEvent (Redis Stream anycast)
        → Manager consumes → DB UPSERT

Heartbeat (60s) → Compare config_hash → Full UPSERT if changed, update last_heartbeat only if same
Shutdown → ServiceDeregisteredEvent → status = DEREGISTERED
Stale detection (5min) → Manager sweep → status = UNHEALTHY
```

> event 타입 정의와 세부 사항은 [event 및 등록 흐름 세부 사항](BEP-1046/event-registration.md)을 참조한다.

### 멀티 에이전트 고려 사항

Agent 의 멀티 에이전트 모드(PRIMARY + AUXILIARY)에서 서비스 디스커버리는 프로세스당 항목 하나만 등록한다. PRIMARY Agent 의 `agent_id` 를 `instance_id` 로 사용하고, AUXILIARY Agent 는 기존 `AgentHeartbeatEvent` → `agents` table 경로를 계속 사용한다. 멀티 에이전트는 서비스 디스커버리의 하위 개념으로 다루고 현재 범위에서는 최소한으로 통합한다.

## 마이그레이션, 호환성

### 하위 호환성

- 기존 `ServiceDiscoveryLoop` 를 즉시 제거하지 않고 deprecated 로 표시한다
- `[service-discovery]` 설정 section 이 없으면 기존 서비스 디스커버리 방식을 사용한다
- `config migrate service-discovery` CLI 로 기존 배포를 마이그레이션할 수 있다

### 깨지는 변경

- 새 DB table 추가(Alembic 마이그레이션 필요)
- Webserver 에 EventProducer 추가(기존 동작에 영향 없음)
- `EventDomain` 에 새 값 추가

### 마이그레이션 단계

1. Alembic 마이그레이션으로 `service_catalog` 와 `service_catalog_endpoint` table 생성
2. `config migrate service-discovery` CLI 로 기존 설정 파일에 `[service-discovery]` section 생성
3. 새 설정으로 서비스 재시작 → 서비스 디스커버리 event 발행 시작
4. 모든 컴포넌트를 전환한 뒤 기존 `ServiceDiscoveryLoop` 를 별도 task 로 제거

### 이후 확장

```
Current: Component → Redis Event → Manager (consumer) → DB
Future:  Component → Redis Event → SD Server (consumer) → DB
```

event 발행 쪽(각 컴포넌트)은 변경이 필요 없다.

## 구현 계획

### 1단계: 공통 기반(BA-4315)

1. `ServiceDiscoveryConfig`, `ServiceEndpointConfig` pydantic model 추가
2. 각 컴포넌트의 통합 설정에 `[service-discovery]` section 추가
3. `ServiceRegisteredEvent`, `ServiceDeregisteredEvent` event 타입 정의
4. `EventDomain.SERVICE_DISCOVERY` 추가
5. `service_catalog`, `service_catalog_endpoint` DB model 과 Alembic 마이그레이션
6. `generate-sample` 명령 수정

### 2단계: CLI 마이그레이션(BA-4316)

1. `MappingRule` 데이터 구조 정의
2. 컴포넌트별 mapping rule 작성(Agent, Manager, Storage, App Proxy)
3. `config migrate service-discovery` CLI 명령 구현
4. mapping rule 단위 테스트

### 3단계: 런타임 통합(BA-4317)

1. 각 컴포넌트에 서비스 디스커버리 event 발행 로직 추가(시작, 서비스 카탈로그 heartbeat, 종료)
2. Webserver 에 EventProducer 추가
3. Manager 에 서비스 디스커버리 event handler 구현(DB upsert)
4. Manager 백그라운드 sweep 구현(오래된 서비스를 UNHEALTHY 로 표시)
5. GraphQL 조회 API 구현
6. `ServiceDiscoveryLoop` 를 deprecated 로 표시

### 4단계: 클라이언트 pool(BA-4318)

1. `ServiceCatalogCache` 구현(인메모리 캐시와 자기 보존)
2. `SDClientPool` 구현(역할, 스코프 기반 엔드포인트 선택)
3. Manager 의 Storage Proxy client 를 서비스 디스커버리 기반으로 전환
4. Manager 의 App Proxy client 를 서비스 디스커버리 기반으로 전환
5. `AgentClientPool` 주소 결정을 서비스 디스커버리 기반으로 전환

## 결정 기록

| 날짜 | 결정 | 근거 | 검토한 대안 |
|------|----------|-----------|------------------------|
| 2026-02-07 | Valkey event → DB 아키텍처 채택 | 기존 event 인프라 재사용과 SQL 조회 가능성 | DB 직접 polling(지연), etcd watch(복잡도) |
| 2026-02-07 | 역할과 스코프 2차원 엔드포인트 모델 | 역할과 네트워크 스코프를 독립적으로 표현 | 단일 이름 field(모호함), 역할만(네트워크 구분 없음) |
| 2026-02-07 | 설정 기반 엔드포인트 등록 | 명시적이고 감사 가능하며 CLI 마이그레이션 도구를 제공할 수 있다 | 코드 기반 자동 추론(암묵적), 혼합(복잡) |
| 2026-02-07 | 자기 보존(Eureka 패턴) | backend 장애 시 기존 연결을 유지하고 연쇄 장애를 방지한다 | 즉시 제거(연쇄 장애 위험), TTL 만 사용(유연성 부족) |
| 2026-02-07 | scope 에서 host 제거 → cluster/container/public | localhost 를 cluster 에 포함하고 독립 host scope 는 불필요하다 | host 유지(과도한 분할) |
| 2026-02-07 | Agent 서비스 디스커버리: 프로세스당 항목 하나 | 멀티 에이전트는 하위 개념이고 복잡도를 최소화한다 | auxiliary 마다 등록(과도하고 기존 에이전트 heartbeat 와 중복) |
| 2026-02-07 | instance_id: 서비스 디스커버리 설정 우선 + 컴포넌트별 대체 | 모든 컴포넌트에 일관된 우선순위 규칙 | 컴포넌트별 별도 규칙(불일치), 고정 UUID(파일 관리 부담) |
| 2026-02-07 | Webserver: EventProducer 만 추가 | 서비스 디스커버리 등록은 필요하지만 event 소비(Dispatcher)는 불필요하다 | event 시스템 전체 채택(과도) |

## 열린 질문

1. **서비스 카탈로그 heartbeat 의 DB 부하 최적화**
   - `config_hash` 가 바뀌지 않으면 `last_heartbeat` 만 갱신하도록 설계했다
   - 서비스 수가 매우 많아지면 모니터링이 필요하다

2. **기존 에이전트 heartbeat 와의 연관성**
   - `AgentHeartbeatEvent` 는 자원 슬롯, 이미지 목록 등 큰 데이터를 담는다
   - 목적이 달라 서비스 디스커버리와 분리하는 편이 적절해 보이지만, 기존 통합 구조(AgentRow, 자원 그룹 등)를 검토한 뒤 최종 결정이 필요하다

3. **App Proxy Coordinator 와 자원 그룹 매핑**
   - 지금 `wsproxy_addr`/`wsproxy_api_token` 은 `scaling_groups` row 에 저장된다
   - 서비스 카탈로그로 전환할 때 레이블 기반 매핑을 사용하는 방안과 별도 junction table 을 사용하는 방안 중 선택이 필요하다

### 확정된 항목

- **Webserver EventProducer**: Valkey Stream 연결과 EventProducer 만 추가한다. EventDispatcher(event 소비)는 Manager 에만 둔다
- **스코프 조회 방식**: 등록은 설정 기반이고 스코프별 엔드포인트를 명시적으로 선언한다. 조회는 원하는 스코프를 지정해 필터링한다

## 참고

- [BEP-1024: Agent RPC Connection Pooling](BEP-1024-agent-rpc-connection-pooling.md) - 기존 클라이언트 pool 패턴
- [BEP-1023: Unified Config Consolidation](BEP-1023-unified-config-consolidation.md) - 설정 구조 참조
- HashiCorp Consul - Catalog API, 에이전트 캐시, blocking query, anti-entropy
- Netflix Eureka - 클라이언트 쪽 registry 캐시, 자기 보존 모드
- Kubernetes - EndpointSlices, kube-proxy iptables 규칙 유지
- Apache ZooKeeper - Ephemeral node, Curator ServiceCache
