# Events: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다. 전송 계층의 전달 한도는 [../message_queue/KNOWLEDGE.md](../message_queue/KNOWLEDGE.md) 에 있다.

## 이 패키지가 있는 이유

message queue 위에 event type, dispatcher, cache 를 두는 컴포넌트 간 event 계층이다. handler 작성자가 따라야 하는 동작 규칙을 이 문서가 담는다.

## handler 는 idempotent 해야 한다

- anycast 메시지는 등록된 handler 가 **모두** 반환한 뒤에야 ack 응답을 보낸다.
- handler 하나라도 실패하면 메시지를 재전달하고 **이미 성공한 handler 까지 모두 다시 실행한다**. 모든 handler 는 재실행을 견뎌야 한다.
- 그래서 handler 가 여럿인 anycast event 는 위험한 구조이다. anycast event 하나에는 소비 handler 하나를 선호한다.
- handler 실패는 pump 를 멈추지 않는다. event 사이에도, event 하나의 handler 사이에도 순서 보장이 없다.

## 처리할 handler 가 없는 event 는 조용히 사라진다

- 등록된 handler 가 없는 event 는 즉시 ack 응답을 보내고 폐기한다.
- 일부 worker 에만 handler 를 등록하면 다른 worker 가 event 를 가져갈 때마다 유실된다. 기동 시 handler 를 무조건 등록한다.

## 호출자 context 는 event 를 따라 전파된다

- `EventProducer` 가 `current_request_id()`, `current_user()`, `triggered_user()` 를 `MessageMetadata` 에 담고, dispatcher 가 handler 실행 전에 `apply_context()` 로 다시 주입한다.
- relay 가 metadata 를 보존할 때만 tracing 이 이어진다. metadata 없이 후속 event 를 내보내는 handler 는 trace 를 끊는다.

## cache 는 유실되는 broadcast 를 보완한다

- broadcast 는 fire-and-forget 이다. 그래서 두 도메인(bgtask, session scheduler)이 최신 payload 를 `cache_id` 아래에 TTL 5분으로 또한 저장한다.
- SSE subscriber 는 cache 에 저장된 마지막 event 를 먼저 재생해 발생 후 구독하는 경쟁 조건을 해소하고, 30초 침묵마다 cache 를 다시 조회하는 polling 안전망을 사용한다.
- cache 는 id 마다 최신 event 하나만 보관한다. 다시 연결한 client 는 놓친 중간 event 가 아니라 snapshot 을 받는다.
