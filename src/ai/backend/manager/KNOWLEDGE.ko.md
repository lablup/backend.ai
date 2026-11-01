# Manager: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다. 계층별 배경 지식은 각 하위 패키지의 `KNOWLEDGE.md` 에 있다.

## 이 컴포넌트가 존재하는 이유

Manager 는 **business logic 을 결정하는 컴포넌트**다. 실제 동작을 수행하고 확장이 필요한 일은 별도 컴포넌트로 나뉜다. kernel 실행은 agent, 파일은 Storage Proxy, 트래픽은 App Proxy 가 맡는다.

- 변경이 Manager 안에서 workload 를 실행해야 하는 것처럼 보이면 그 일은 다른 컴포넌트에 속한다.

## DB 가 기준이 되는 값이다

- 엔티티 상태는 DB 에 있고, 주요 경로는 cache 를 신뢰하지 않고 다시 조회한다. scheduler 는 tick 마다 resource group 을 다시 읽는다.
- Valkey 는 cache data 를 보유하고 event queue 를 겸한다. 기준이 되는 값은 유실되지 않지만 **event 의존이 커서 Valkey 가 실패하면 대부분의 동작이 중단될 수 있다**. 가용성 의존이 크다.
- etcd 는 설정과 Manager 상태만 담는다.
- 트랜잭션은 READ COMMITTED 에 충돌 시 재시도를 추가한다. 동시 writer 를 전제하고 배타성은 전제하지 않는다.

## distributed lock 은 줄어드는 중이다

- 여러 host 에 걸쳐 host 마다 N 개의 worker 프로세스가 있다. API 의 절반은 대칭이고 stateless 다.
- distributed lock 의존은 크지 않지만 scheduler 가 2 cycle 로 실행되어 coordinator tick 이 현재 lock 을 사용한다(`DistributedLockFactory`, 정수 `LockID`).
- 이 부분은 redis 기반 flag 를 설정하는 방식으로 대체할 예정이고 distributed lock 은 계속 줄어든다.
- leader election(Valkey lease)에서 leader 는 cron emitter(`LeaderCron`)만 실행한다. leader 의 일은 "publishing" 이고 실행은 queue 가 고른 프로세스가 맡는다.

## 컴포넌트 사이 통신 방향

- manager → agent / storage proxy / appproxy: 직접 호출한다(RPC, HTTP).
- 반대 방향(component → manager)의 직접 요청은 권장하지 않는다. 대신 **redis event 나 상태를 가진 source 로 값을 공유하는** 방식을 사용한다.
- 유실되면 안 되는 Manager 발 지시는 broadcast 만으로 보내지 않는다. 직접 호출하거나 reconcile tick 으로 다시 구동한다.
- Manager 프로세스는 하나의 consumer group 을 공유한다. anycast event 는 cluster 당 한 번, 어느 프로세스에서든 처리되므로 handler 는 프로세스 로컬 상태에 의존하지 않는다.

## 실행 경로 셋, domain 계층 하나

- API 기반: REST/GQL → adapters → processors.
- event 기반: `event_dispatcher/` 의 handler group.
- timer 기반: leader cron, coordinator tick, 프로세스별 task.
- 세 경로는 모두 같은 service 와 repository 로 모인다. API 경로에만 있는 검증은 규칙이 아니라 구멍이다.

## DI 는 고정된 stage 순서다

- `ManagerDependencyComposer` 는 10 개 stage 를 고정 순서로 구성한다: bootstrap → infra → components → plugins → messaging → domain → system → agents → orchestration → processing.
- event dispatcher 는 마지막에 등록된다. 모든 service 가 존재하기 전에는 event 를 소비하는 것이 없다.
- teardown 은 정확히 반대 순서다.
- 새 의존성은 소비자가 있는 stage 에 추가한다. `server.py` 에 추가하지 않는다.
