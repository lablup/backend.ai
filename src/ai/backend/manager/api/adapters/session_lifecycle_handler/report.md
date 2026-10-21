## session_lifecycle_handler

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/adapter.py)

시나리오: 완성

- Action 없음 (1)
  - list_session_lifecycle_handlers — 성공 있음 1 · 실패 없음

**list_session_lifecycle_handlers**

| 시나리오 | 판정 |
|---|---|
| [스케줄러가 만드는 세션 처리기 전부가 각자의 이름과 클래스 설명의 첫 줄로 반환된다](#listing-every-scheduler-handler-is-listed) | 성공 |

### list_session_lifecycle_handlers

<a id="listing-every-scheduler-handler-is-listed"></a>

#### [every-scheduler-handler-is-listed](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py) — pass

스케줄러가 만드는 세션 처리기 전부가 각자의 이름과 클래스 설명의 첫 줄로 반환된다

Given

- 스케줄러가 시작할 때 만드는 세션 처리기가 정해져 있다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers — 세션 처리기 목록을 조회

Then

- 처리기 전부가 각자의 이름과 클래스 설명의 첫 줄로 반환된다
  - items = [SessionLifecycleHandlerNode(name='schedule-sessions', description='Handler for scheduling pending sessions.'), SessionLifecycleHandlerNode(name='deprioritize-sessions', description='Handler for deprioritizing sessions that exceeded max scheduling retries.'), SessionLifecycleHandlerNode(name='check-precondition', description='Handler for checking session preconditions and triggering image pulling.'), SessionLifecycleHandlerNode(name='start-sessions', description='Handler for starting sessions that passed precondition checks.'), SessionLifecycleHandlerNode(name='terminate-sessions', description='Handler for terminating sessions marked for termination.'), SessionLifecycleHandlerNode(name='release-reserved-sessions', description="Advance RESERVED sessions once their victims' resources are freed."), SessionLifecycleHandlerNode(name='preempt-sessions', description='Handler that routes confirmed preemption victims (BEP-1055 eviction).'), SessionLifecycleHandlerNode(name='reschedule-sessions', description='Handler that returns RESCHEDULING sessions to the queue.'), SessionLifecycleHandlerNode(name='sweep-sessions', description='Handler for sweeping stale sessions (maintenance operation).')]

