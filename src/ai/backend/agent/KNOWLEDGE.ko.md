# Agent: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 컴포넌트가 있는 이유

Agent 는 **실제로 커널(container)을 생성하고 관리하는 컴포넌트**다. manager 가 결정한 세션을 node 에서 실행 상태로 생성하고 유지하는 일이 모두 여기서 일어난다: 종료, node 자원 할당, 상태 수집과 보고.

## node 가 기준이다

- node 에서 실제로 실행되는 것은 Agent 가 소유한다. manager 의 DB 는 Agent 가 보고한 값의 projection 이다.
- 통신은 의도적으로 비대칭이다. manager→Agent 는 ZeroMQ RPC 이고, Agent→manager 는 event 와 주기적 heartbeat 이다.
- heartbeat payload 는 전체 이미지 목록과 자원 슬롯을 담는다. `AgentInfo` 확장은 manager 호환성 문제다.

## 세 세대의 RPC 가 공존한다

- v1, v2 class 수준 registry 는 시작 시점에 여전히 바인딩된다.
- 새 handler 는 주입 가능한 v3 registry(`rpc/routing.py`)에 들어간다.
- v3 dispatch 는 호출 envelope 의 `agent_id` 로 대상 Agent 를 정한다.

## 한 process 가 여러 Agent 를 호스팅할 수 있다

- `AgentRuntime` 은 공유 커널 registry 와 resource allocator 를 두고 `AgentId → AbstractAgent` 를 매핑한다.
- module 수준이나 process 수준 singleton 이 특정 Agent 의 것이라고 가정하지 않는다.

## 상태는 재시작 후에도 남아야 한다

- docker Agent 는 커널마다 recovery 기록을 자기 scratch config 디렉터리에 저장하고, boot 때 그 기록으로 커널 registry 를 다시 생성한다(`kernel_registry/recovery/`). kubernetes Agent 는 영속 registry 가 없어 빈 상태로 시작한다.
- 재시작 후에도 남아야 하는 새 field 는 메모리 객체에만 두지 말고 recovery data 에도 추가해야 한다.

## watcher 는 별도의 특권 process 다

- watcher 는 자체 aiohttp process 이며 Agent 를 시작, 중지, 재설정할 수 있다. Agent 가 자기 재시작을 소유한다고 가정하지 않는다.
- 인증 token(etcd `config/watcher/token`)의 기본값은 문자열 `"insecure"` 다. 배포에서는 반드시 설정해야 한다.
- watcher 의 역할을 Agent server 에 합치지 않는다.
- 이 구조는 Agent 만의 최종 형태가 아니다. **모든 server 를 같은 방식으로 실행할 수 있게 일반화할 계획이다(watcher 가 server process 를 관리한다).**
