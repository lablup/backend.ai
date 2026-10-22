## session_lifecycle_handler

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/adapter.py)

시나리오: 완성

- Action 없음 (1)
  - list_session_lifecycle_handlers — 성공 있음 2 · 실패 없음

**list_session_lifecycle_handlers**

| 시나리오 | 판정 |
|---|---|
| [코디네이터에 등록된 처리기가 없으면 빈 목록이 반환된다](#listing-no-registered-handler-lists-nothing) | 성공 |
| [코디네이터에 등록된 처리기가 이름 순으로, 각자의 이름과 클래스 설명의 첫 줄로 반환된다](#listing-registered-handlers-are-listed-in-name-order) | 성공 |

### list_session_lifecycle_handlers

<a id="listing-no-registered-handler-lists-nothing"></a>

#### [no-registered-handler-lists-nothing](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py) — pass

코디네이터에 등록된 처리기가 없으면 빈 목록이 반환된다

Given

- 코디네이터에 등록된 처리기가 없다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers — 세션 처리기 목록을 조회

Then

- 빈 목록이 반환된다
  - items = []

<a id="listing-registered-handlers-are-listed-in-name-order"></a>

#### [registered-handlers-are-listed-in-name-order](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py) — pass

코디네이터에 등록된 처리기가 이름 순으로, 각자의 이름과 클래스 설명의 첫 줄로 반환된다

Given

- 코디네이터에 세션 종료 처리기와 사전 조건 검사 처리기가 이 순서로 등록되어 있다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers — 세션 처리기 목록을 조회

Then

- 사전 조건 검사 처리기, 세션 종료 처리기 순으로 각자의 이름과 클래스 설명의 첫 줄로 반환된다
  - items = [SessionLifecycleHandlerNode(name='check-precondition', description='Handler for checking session preconditions and triggering image pulling.'), SessionLifecycleHandlerNode(name='terminate-sessions', description='Handler for terminating sessions marked for termination.')]

