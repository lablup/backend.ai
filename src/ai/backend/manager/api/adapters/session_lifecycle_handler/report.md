## session_lifecycle_handler

[what it guarantees](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/adapter.py)

Scenario: complete

- no Action (1)
  - list_session_lifecycle_handlers — success present 2 · refusal absent

**list_session_lifecycle_handlers**

| scenario | verdict |
|---|---|
| [코디네이터에 등록된 처리기가 없으면 빈 목록이 반환된다](#listing-no-registered-handler-lists-nothing) | answered |
| [코디네이터에 등록된 처리기가 그 이름과 설명으로 반환된다](#listing-the-registered-handler-is-listed) | answered |

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

<a id="listing-the-registered-handler-is-listed"></a>

#### [the-registered-handler-is-listed](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py) — pass

코디네이터에 등록된 처리기가 그 이름과 설명으로 반환된다

Given

- 코디네이터에 세션 종료 처리기가 등록되어 있다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers — 세션 처리기 목록을 조회

Then

- 세션 종료 처리기 하나가 그 이름과 설명으로 반환된다
  - items = [SessionLifecycleHandlerNode(name='terminate-sessions', description='Terminates the kernels of sessions marked for termination.')]

