## scheduling_handler

[어댑터](/src/ai/backend/manager/api/adapters/scheduling_handler/adapter.py)

시나리오: 완성

- Action 없음 (1)
  - list_scheduling_handlers: 성공 있음 2 · 거부 없음

**list_scheduling_handlers**

| 시나리오 | 판정 |
|---|---|
| [코디네이터가 등록한 처리기가 없으면 빈 목록이 반환됩니다](#listing-no-registered-handler-lists-nothing) | 성공 |
| [코디네이터가 등록한 처리기가 이름, 분류, 설명으로 반환됩니다](#listing-the-registered-handlers-are-listed) | 성공 |

### list_scheduling_handlers

<a id="listing-no-registered-handler-lists-nothing"></a>

#### [no-registered-handler-lists-nothing](/tests/scenario/bai_scenario/manager/scheduling_handler/test_listing.py): pass

코디네이터가 등록한 처리기가 없으면 빈 목록이 반환됩니다

Given

- 코디네이터가 등록한 처리기가 없습니다

When

- SchedulingHandlerAdapter.list_scheduling_handlers: 배포 처리기 목록을 조회합니다

Then

- 빈 목록이 반환됩니다
  - items = []

<a id="listing-the-registered-handlers-are-listed"></a>

#### [the-registered-handlers-are-listed](/tests/scenario/bai_scenario/manager/scheduling_handler/test_listing.py): pass

코디네이터가 등록한 처리기가 이름, 분류, 설명으로 반환됩니다

Given

- 코디네이터가 복제본 점검 처리기와 배포 초기화 처리기를 등록했습니다

When

- SchedulingHandlerAdapter.list_scheduling_handlers: 배포 처리기 목록을 조회합니다

Then

- 등록된 순서대로 처리기마다 이름, 분류, 설명의 첫 줄이 반환됩니다
  - items = [SchedulingHandlerNode(name='check-replica-deployments', category=<SchedulingHandlerCategory.SCALING: 'scaling'>, description='Handler for checking and managing deployment replicas.'), SchedulingHandlerNode(name='deploying-initializing', category=<SchedulingHandlerCategory.LIFECYCLE: 'lifecycle'>, description='DEPLOYING / INITIALIZING: register the appproxy endpoint for deployments that entered')]

