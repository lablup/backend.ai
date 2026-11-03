# App-Proxy 컴포넌트

App-Proxy 는 두 컴포넌트로 이뤄진다.

- **Coordinator**: circuit 수명 주기, worker 등록, 세션 매핑을 관리한다
- **Worker**: 애플리케이션 엔드포인트(kernel container)로의 실제 proxy 를 처리한다

## 구조 개요

```
Manager                   Coordinator                  Worker                    App
   │                           │                          │                       │
   │  POST /v2/proxy/auth      │                          │                       │
   │  (create circuit)         │                          │                       │
   ├──────────────────────────▶│                          │                       │
   │                           │                          │                       │
   │                           │  Redis Event             │                       │
   │                           │  (circuit created)       │                       │
   │                           ├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│                       │
   │                           │                          │                       │
   │  ◀── redirect URL ────────┤                          │                       │
   │                           │                          │                       │
   │                           │                          │                       │
   │      Client (after redirect)                         │                       │
   │             │                                        │                       │
   │             │  HTTP Request (direct)                 │                       │
   │             ├───────────────────────────────────────▶│                       │
   │             │                                        │  Proxy to App         │
   │             │                                        ├──────────────────────▶│
   │             │                                        │                       │
   │             │                                        │◀──────────────────────┤
   │             │◀───────────────────────────────────────┤                       │
```

**핵심:**
- Manager 가 coordinator API 로 circuit 생성을 시작한다
- coordinator 가 Valkey event 로 circuit 을 worker 에 배치한다
- client 트래픽은 coordinator 를 거치지 않고 worker 로 직접 간다

## 현재 상태

coordinator 는 Manager 의 circuit 생성 요청에서 request_id 를 저장하지 않는다.

## 제안 변경

### 1. App-Proxy 에서 request ID 를 생성하지 않음

App-Proxy 는 request_id 를 생성하지 않는다. 모든 request_id 는 Manager 에서 시작한다.
coordinator 는 Manager 요청에서 `X-Backend-Request-ID` 를 추출해 추적용으로 저장할 뿐이다.

### 2. Circuit 생성 추적

Manager 가 coordinator API 로 circuit 을 생성할 때:
- coordinator 가 Manager 요청에서 `X-Backend-Request-ID` 를 추출한다
- 감사, 디버깅용으로 circuit database record 에 `origin_request_id` 로 저장한다

## Request 흐름

### Circuit 생성(Manager 를 통해)

```
Manager                   Coordinator
   │                           │
   │  POST /v2/proxy/auth      │
   │  X-Backend-Request-ID     │
   ├──────────────────────────▶│
   │                           │
   │     extract request_id    │
   │     store as origin_rid   │
   │                           │
   │  redirect URL + token     │
   │◀──────────────────────────┤
```

## 구현 체크리스트

### Coordinator

- [ ] Manager 요청에서 `X-Backend-Request-ID` 를 추출한다(생성하지 않음)
- [ ] circuit database record 에 origin_request_id 를 저장한다

### Worker

request_id 처리가 필요 없다. worker 는 Manager 와 직접 상호작용하지 않는다.
