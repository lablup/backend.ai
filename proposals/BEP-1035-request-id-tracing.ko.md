# 분산 환경 request ID 전파

## 개요

이 BEP 는 Backend.AI 분산 구조를 위한 request ID 추적 체계를 정의한다. Manager, Agent, Storage-Proxy, App-Proxy, Web Server 모든 컴포넌트에서 request ID 를 생성, 전파, 활용하는 기준을 정해 종단 간 request 추적과 디버깅, 관측성을 확보한다.

## 동기

Backend.AI 는 사용자 요청 하나가 여러 컴포넌트를 거칠 수 있는 분산 시스템이다.

1. 사용자 요청이 Manager 의 HTTP API 로 들어온다
2. Manager 가 Agent 에 RPC 를 보내거나 Storage-Proxy 에 HTTP 를 호출하거나 App-Proxy 와 통신할 수 있다
3. background task 와 event handler 가 작업을 비동기로 처리한다
4. 각 컴포넌트가 로그를 따로 남긴다

통합된 request ID 추적 체계가 없으면 다음 문제가 생긴다.

- **디버깅이 어렵다**: 에러가 나면 컴포넌트 사이 로그를 timestamp 로 직접 맞춰야 한다
- **근본 원인 분석이 느리다**: 실패한 요청의 전체 경로를 추적하려면 여러 컴포넌트의 로그를 살펴봐야 한다
- **관측성이 제한된다**: request 흐름 시각화를 구성하거나 종단 간 지연을 측정할 수 없다
- **감사 추적이 불완전하다**: 서비스 경계를 넘는 관련 동작을 확실히 연결할 수 없다

### 현재 상태

request ID 추적은 아직 체계적으로 구현하지 않는다.

- Manager 는 HTTP 요청용 `request_id_middleware` 가 있지만 다른 컴포넌트로 전파하지 않는다
- Agent RPC 는 request_id 를 지원하지 않는다
- background task 에는 request_id 가 없다
- App-Proxy 는 request_id 를 지원하지 않는다

그 결과는 다음과 같다.

- 컴포넌트 사이 로그를 연결할 방법이 없다
- 시스템을 지나는 요청의 전체 경로를 추적할 수 없다

## 설계 원칙

1. **context 기반 전파**: Python `contextvars` 로 비동기 호출 체인에 request ID 를 전달한다
2. **자동 생성**: 시스템 진입점에서 request ID 가 없으면 생성한다
3. **표준 header**: HTTP 와 RPC 프로토콜에서 같은 header 이름을 사용한다
4. **확장 가능한 구조**: 이후 추가(correlation_id, trace_id, span_id 등 OpenTelemetry)를 염두에 두고 설계한다
5. **최소 부담**: request ID 처리가 성능에 거의 영향을 주지 않아야 한다
6. **이전 호환**: 기존 배포를 깨지 않고 점진적으로 이관한다

## 범위

### 범위 안

| 컴포넌트 | 현재 | 제안 |
|-----------|---------|----------|
| 공통 인프라 | `request_id_middleware` 있음 | 유틸리티, RPC header 모델 추가 |
| Manager | HTTP middleware 만 | Agent, Storage-Proxy, App-Proxy 로 전파 |
| Agent | request_id 지원 없음 | RPC header 지원 추가 |
| Storage-Proxy | HTTP middleware 만 | background task 지원 추가 |
| App-Proxy coordinator | request_id 지원 없음 | middleware 와 전파 추가 |
| App-Proxy worker | request_id 지원 없음 | middleware 와 전파 추가 |

### 범위 밖(이후 작업)

| 컴포넌트 | 메모 |
|-----------|-------|
| Account Manager | 별도 서비스, 나중에 따를 수 있음 |
| Web Server | frontend proxy, middleware 를 추가할 수 있음 |
| WSProxy | WebSocket proxy, 통과 동작 |

## 구조 개요

```
  External Request              Background Task / Event Handler
        │                                  │
        ▼                                  ▼
  ┌───────────┐                    ┌─────────────────────────┐
  │   HTTP    │                    │ 1. Use propagated rid   │
  │ Middleware│                    │    (from event/context) │
  └─────┬─────┘                    │ 2. Auto-generate        │
        │                          │    (fallback only)      │
        │                          └───────────┬─────────────┘
        │                                      │
        └────────────────┬─────────────────────┘
                         ▼
         ┌───────────────────────────────────────┐
         │     _request_id_var (ContextVar)      │
         │                                       │
         │  current_request_id() → str | None    │
         │  bind_request_id(id) → context manager│
         └───────────────────┬───────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │    Agent    │   │   Storage   │   │  App-Proxy  │
    │    (RPC)    │   │    Proxy    │   │   (HTTP)    │
    │             │   │   (HTTP)    │   │             │
    │ headers: {  │   │ X-Backend-  │   │ X-Backend-  │
    │  request_id │   │ Request-ID  │   │ Request-ID  │
    │ }           │   │             │   │             │
    └─────────────┘   └─────────────┘   └─────────────┘
```

## 상세 설계

상세 명세는 컴포넌트별 문서로 나눈다.

| 문서 | 설명 |
|----------|-------------|
| [manager.md](./BEP-1035/manager.md) | Manager 컴포넌트: 진입점, 외부 전파 |
| [agent.md](./BEP-1035/agent.md) | Agent 컴포넌트: RPC header 설계 |
| [storage-proxy.md](./BEP-1035/storage-proxy.md) | Storage-Proxy 컴포넌트 |
| [app-proxy.md](./BEP-1035/app-proxy.md) | App-Proxy coordinator 와 worker |

## 구현 상태

| 컴포넌트 | 현재 상태 | 목표 상태 | 우선순위 |
|-----------|--------------|--------------|----------|
| 공통 | HTTP middleware 만 | 유틸리티, RPC header 모델 추가 | 높음 |
| Manager | HTTP middleware 만 | 모든 외부 호출로 전파 | 높음 |
| Agent | request_id 지원 없음 | RPC header 지원 | 높음 |
| Storage-Proxy | HTTP middleware 만 | background task 용 context 바인딩 추가 | 낮음 |
| App-Proxy | request_id 지원 없음 | middleware 추가 | 중간 |

## 이관 계획

### 1단계: 공통 인프라

1. background task, event handler 의 context 바인딩용 decorator 를 추가한다
2. request ID 전파를 위해 context 유틸리티를 보강한다

### 2단계: Agent RPC header

1. Agent 에 RPC header 모델을 추가한다(메시지 라우팅용 agent_id 포함)
2. header 를 내장한 새 RPC API 를 구현한다
3. Manager 가 header 를 사용하는 새 API 를 사용하도록 수정한다

### 3단계: App-Proxy 표준화

1. Manager 가 App-Proxy 로 request_id 를 전파하도록 수정한다(HTTP header)
2. coordinator 와 worker 에 request ID 용 HTTP middleware 를 추가한다
3. worker 와 coordinator 사이의 전파를 보장한다

### 4단계: 전체 반영

1. 모든 background task 와 event handler 에 context 바인딩 decorator 를 적용한다
2. event 시스템 metadata 에 request_id 를 추가한다

## 이전 호환

### Manager 에서 Agent 로의 통신

새 RPC API 는 기존 API 와 분리해 header 를 내장한 형태로 생성한다. 이렇게 하면 이전 호환 문제가 아예 생기지 않는다. 기존 Agent 는 기존 API 를 계속 사용하고, 새 Agent 는 header 를 지원하는 새 API 를 사용한다.

### HTTP 컴포넌트

HTTP 를 제공하는 컴포넌트는 breaking change 없이 request ID middleware 를 점진적으로 도입할 수 있다.

## 아이디어

이후 반복에서 검토할 아이디어다. 이번 제안에는 포함하지 않는다.

### 구조화한 request ID 데이터

일반 UUID 문자열 대신 구조화한 타입으로 발생 출처 metadata 를 담는다.

```python
@dataclass
class RequestIdData:
    request_id: str                    # UUID string
    component_source: str              # Where generated: "manager", "agent", "storage-proxy"
    source_detail: str | None = None   # Optional detail: "event_handler", "background_task", "rpc_handler"
```

| component_source | source_detail (예시) | 설명 |
|------------------|--------------------------|-------------|
| `manager` | `None` | HTTP API 요청 |
| `manager` | `event_handler` | event handler 처리 |
| `manager` | `background_task` | background task 실행 |
| `agent` | `rpc_handler` | Agent RPC handler |
| `storage-proxy` | `background_task` | storage background task |

**장점:**
- 디버깅할 때 request 출처를 빨리 파악한다
- 컴포넌트와 세부 값으로 로그를 필터링한다
- 구조화한 데이터라 질의가 더 쉽다
- 문자열 parsing 이 필요 없다(접두사 방식과 다름)

**고려 사항:**
- 구조화한 데이터를 다루도록 context 유틸리티를 수정해야 한다
- RPC, HTTP header 의 직렬화 형식(JSON 또는 별도 header)

## 참고

- [OpenTelemetry Trace Context](https://www.w3.org/TR/trace-context/)
- [BEP-1002: Agent Architecture](./BEP-1002-agent-architecture.md)
