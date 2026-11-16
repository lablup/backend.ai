# Manager 컴포넌트

Manager 는 Backend.AI 구조의 중심이다. client 요청을 받아 Agent, Storage-Proxy, App-Proxy 에서 수행하는 동작을 조정한다.

## 진입점

### HTTP API

aiohttp 애플리케이션에 HTTP middleware 를 적용한다. middleware 는 다음을 수행한다.

1. `X-Backend-Request-ID` header 가 있으면 추출한다
2. 없으면 새 request ID 를 생성한다
3. request ID 를 context 에 바인딩한다
4. 응답 header 에 `X-Backend-Request-ID` 를 추가한다

### Background task

HTTP 요청에서 시작하지 않은 background task 에 context 바인딩 decorator 를 적용한다. decorator 는 request ID 를 자동 생성해 비동기 context 에 바인딩한다.

### 메시지 큐 event handler

인과 추적을 위해 event metadata 에서 request ID 를 복원한다.

## 외부 전파

### Agent RPC 호출

Manager 는 Callosum RPC 로 Agent 와 통신한다. request body 에 request ID 를 담는다.

```python
request_body = {
    "headers": {"request_id": get_current_request_id()},  # from context
    "args": args,
    "kwargs": kwargs,
}
```

header 를 지원하지 않는 기존 Agent 는 `headers` 필드를 무시한다.

### HTTP 호출(Storage-Proxy, App-Proxy, WSProxy)

모든 외부 HTTP 요청에 `X-Backend-Request-ID` header 를 포함한다.

## Event 시스템 연동

- **EventProducer**: event metadata 에 request_id 를 추가한다
- **EventDispatcher**: event 를 처리할 때 metadata 에서 request_id 를 복원한다

## Request 흐름

```
Client                    Manager                   Service
   │                         │                    (Agent/Storage/App-Proxy)
   │  HTTP Request           │                         │
   ├────────────────────────▶│                         │
   │                         │                         │
   │         middleware generates request_id           │
   │                         │                         │
   │                         │  RPC or HTTP call       │
   │                         │  (with request_id)      │
   │                         ├────────────────────────▶│
   │                         │                         │
   │                         │◀────────────────────────┤
   │                         │                         │
   │  X-Backend-Request-ID   │                         │
   │◀────────────────────────┤                         │
```

## 구현 체크리스트

- [ ] main app 과 sub-app 에 HTTP middleware 를 적용한다
- [ ] background task 에 context 바인딩 decorator 를 적용한다
- [ ] Agent RPC 호출에 header 를 포함한다
- [ ] Storage-Proxy, App-Proxy HTTP 호출에 header 를 포함한다
- [ ] event 시스템이 request_id 를 전파한다
