# 이벤트 유형과 등록 흐름 상세

> 상위 문서: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## 이벤트 유형 정의

서비스 디스커버리 event 는 기존 Valkey Stream event 인프라를 사용해 정의한다.

```python
# src/ai/backend/common/events/event_types/service_discovery/anycast.py

class ServiceEndpointInfo(BaseModel):
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, str] = Field(default_factory=dict)

class ServiceRegisteredEvent(AbstractAnycastEvent):
    """Service registration and heartbeat event (upsert semantics)"""
    instance_id: str        # Upsert by (service_group, instance_id)
    service_group: str
    display_name: str
    version: str
    labels: dict[str, str]
    endpoints: list[ServiceEndpointInfo]
    startup_time: datetime  # Service process start time
    config_hash: str        # Hash for config change detection

class ServiceDeregisteredEvent(AbstractAnycastEvent):
    """Service deregistration event"""
    instance_id: str
    service_group: str
```

- **Anycast**: consumer group 의 Manager instance 하나만 각 event 를 처리한다
- 기존 `EventDomain` 에 `SERVICE_DISCOVERY = "service_discovery"` 를 추가한다
- Valkey Stream `"events"`(DB 4)를 사용한다. 기존 event 와 같은 channel 이다

## 등록 흐름 상세

```
[Startup]
Each component server starts
  ↓
Read [service-discovery] config + compute config_hash
  ↓
Publish ServiceRegisteredEvent (anycast via Redis Stream)
  ↓
Manager EventDispatcher consumes
  ↓
UPSERT service_catalog + service_catalog_endpoint (DB)

[Heartbeat]
Re-publish ServiceRegisteredEvent every 60 seconds
  → Manager compares config_hash:
    - Changed: full UPSERT of service_catalog + endpoints
    - Unchanged: update last_heartbeat only (lightweight update)

[Shutdown]
Publish ServiceDeregisteredEvent on graceful shutdown
  → Manager sets status = DEREGISTERED

[Stale Detection]
Manager background sweep (every 5 minutes)
  → Mark status = UNHEALTHY when last_heartbeat > 5 minutes old
```

## config_hash 최적화

`config_hash` 는 `[service-discovery]` config 전체의 hash 다. 서비스 카탈로그 heartbeat 때 이전 hash 와 비교해서 변경되지 않았으면 `last_heartbeat` 시각만 변경한다. DB 부하를 줄인다.

## 컴포넌트별 event 발행 가능 여부

| 컴포넌트 | EventProducer | Valkey Stream | 필요한 변경 |
|-----------|:---:|:---:|:---:|
| Manager | O | O | 자기 등록 추가 |
| Agent | O | O | 서비스 디스커버리 event 발행 추가 |
| Storage Proxy | O | O | 서비스 디스커버리 event 발행 추가 |
| App Proxy Coordinator | O | O | 서비스 디스커버리 event 발행 추가 |
| App Proxy Worker | O | O | 서비스 디스커버리 event 발행 추가 |
| Webserver | X | X | EventProducer 추가 |
