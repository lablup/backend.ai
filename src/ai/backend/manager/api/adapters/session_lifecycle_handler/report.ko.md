## session_lifecycle_handler

[배경](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/adapter.py)

시나리오: 완성

- Action 없음 (1)
  - list_session_lifecycle_handlers: 성공 있음 2 · 거부 없음

**list_session_lifecycle_handlers**

| 시나리오 | 판정 |
|---|---|
| [코디네이터가 등록한 처리기가 없으면 빈 목록이 반환됩니다](#listing-no-registered-handler-lists-nothing) | 성공 |
| [코디네이터가 등록한 처리기가 그 이름과 설명으로 반환됩니다](#listing-the-registered-handler-is-listed) | 성공 |

### list_session_lifecycle_handlers

<a id="listing-no-registered-handler-lists-nothing"></a>

#### [no-registered-handler-lists-nothing](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py): pass

코디네이터가 등록한 처리기가 없으면 빈 목록이 반환됩니다

Given

- 코디네이터가 등록한 처리기가 없습니다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers: 세션 처리기 목록을 조회합니다

Then

- 빈 목록이 반환됩니다
  - items = []

<a id="listing-the-registered-handler-is-listed"></a>

#### [the-registered-handler-is-listed](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py): pass

코디네이터가 등록한 처리기가 그 이름과 설명으로 반환됩니다

Given

- 코디네이터가 세션 종료 처리기를 등록했습니다

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers: 세션 처리기 목록을 조회합니다

Then

- 세션 종료 처리기 하나가 그 이름과 설명으로 반환됩니다
  - items = [SessionLifecycleHandlerNode(name='terminate-sessions', description='Terminates the kernels of sessions marked for termination.')]

