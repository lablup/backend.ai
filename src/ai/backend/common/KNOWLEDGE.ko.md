# Common: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다. 이벤트와 큐의 동작 규칙은 [message_queue/KNOWLEDGE.md](message_queue/KNOWLEDGE.md) 와 [events/KNOWLEDGE.md](events/KNOWLEDGE.md) 에 있다.

## 이 패키지가 있는 이유

모든 컴포넌트가 의존하는 공용 기반이다. 여기에 속하는 type 을 정하는 기준이 이 문서의 핵심이다.

## 소속 기준은 두 부분이다

- 명시된 기준은 **둘 이상의 컴포넌트가 공유하는** 항목이다.
- 두 번째 기준은 더 높은 계층에 두면 **상위 방향 import 를 강제하는** type 이다. `common/schema/` 가 이를 명시하고, manager 만 사용한다.
- 단일 소비자 하위 패키지(`stage/` 는 agent 전용, `resilience/` 는 manager 전용)는 결함이 아니다.
- "중립적인 곳에 두면 편하다" 는 소속 이유가 아니다.
