# 메시지 큐: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 존재하는 이유

Redis stream(anycast)과 pub/sub(broadcast) 위의 전달 추상화다. 이 문서는 consumer 가 가정할 수 있는 전달 보장의 정확한 한계를 담는다.

## 토폴로지: stream 하나, channel 하나, 컴포넌트마다 group 하나

- 모든 컴포넌트가 anycast stream key 하나(`"events"`)와 broadcast channel 하나(`"events_all"`)를 공유하고, consumer group(`"manager"`, `"agent"`, `"storage-proxy"`, ...)으로만 구분한다.
- stream 이나 channel 을 추가하는 일은 국소 결정이 아니라 토폴로지 결정이다.

## anycast 는 at-least-once 다: 얕은 buffer 안에서만

- consumer group 이 읽고, auto-claim loop(60초마다)가 5분 동안 유휴인 메시지를 다시 claim 하며, 재시도 3회 후 메시지는 **ack 되고 폐기된다. DLQ 는 없다**.
- 재시도는 이전 메시지를 ack 하고 다시 추가하는 방식으로 구현된다. 재전달된 메시지는 stream 끝에서 새 id 를 받으므로 순서를 잃고, 메시지 id 는 중복 제거 key 가 아니다.
- 메시지를 추가할 때마다 stream 을 약 128개 항목으로 trim 한다. producer 가 consumer 보다 빠르면 ack 하지 않은 항목도 사라질 수 있다. 내구성 있는 전달이 아니다.
- 연결 실패는 loop 를 멈추지 않으며(상한 30초의 무제한 backoff), 사라진 consumer group 은 자동으로 다시 생성된다.

## broadcast 는 손실을 허용하는 타협이다

- 순수 pub/sub 이고 ack 경로가 없으므로, 내려가 있거나 restart/reconnect 중인 subscriber 는 메시지를 영구히 놓친다.
- 이것은 타협이지 설계 목표가 아니다. 전제는 broadcast 를 **손실이 허용되는 event 에만** 사용한다는 적용 규칙이다.
- "결국 관찰됨"이 필요하면 events 계층의 cache 와 polling 으로 보완한다([../events/KNOWLEDGE.md](../events/KNOWLEDGE.md)). 여기서 재전달을 가정하지 않는다.
