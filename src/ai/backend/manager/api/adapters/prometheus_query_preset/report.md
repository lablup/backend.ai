## prometheus_query_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/prometheus_query_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/prometheus_query_preset/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 아무것도 갖지 않은 분류 id를 지정해 만들면, 분류가 없다는 이유로 거부된다. 저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 아무것도 갖지 않은 분류 id 아래에 cpu-by-kernel으로 만듦

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [a-name-another-preset-already-holds-is-allowed](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

이미 어떤 정의가 쓰고 있는 이름으로 슈퍼관리자가 다시 만들면, 만들어진다. 정의의 이름에는 유일 제약이 없다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이미 있는 preset-1으로 다시 만듦

Then

- 만든 정의 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'preset-1'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-template-the-renderer-refuses-cannot-be-stored](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 렌더러가 받지 않는 템플릿을 주고 만들면, 템플릿으로 거부된다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 정의를 만들려 하면, 역할로 막힌다

Given

- 정의가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-preset-under-a-category-points-the-node-at-that-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

분류 하나가 있고 슈퍼관리자가 그 분류를 지정해 만들면, 답의 분류가 그것을 가리킨다

Given

- 분류 하나와, superadmin 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 심은 분류 아래에 cpu-by-kernel으로 만듦

Then

- 만든 정의 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id: 심은 분류와 같다
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [creating-a-preset-with-a-window-carries-that-window-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 창을 함께 주고 만들면, 노드에 그 창이 실린다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 만든 정의 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = '5m'
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [creating-a-preset-with-the-required-values-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 이름, 지표 이름, 템플릿, 허용 라벨 목록만 주고 만들면, 순위는 0이고 분류·설명·창은 비어 있는 노드 전체가 답으로 온다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 만든 정의 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-monitor-role-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

모니터 역할이 정의를 만들려 하면, 역할로 막힌다. 전역 문은 읽기에만 그 역할을 지나게 한다

Given

- 정의가 하나도 없고, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

엔티티 권한 집행을 꺼도 정의 만들기는 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 정의가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 cpu-by-kernel으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-stored-template-the-renderer-refuses-does-not-block-renaming](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

렌더러가 받지 않는 템플릿을 가진 정의를 슈퍼관리자가 이름만 고치면, 이름은 새 값이다. 템플릿 검증은 요청이 템플릿을 준 때만 돈다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 렌더러가 받지 않는 템플릿을 갖고 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'cpu-by-session'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'up${{ nope }}'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-template-the-renderer-refuses-cannot-replace-the-stored-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 렌더러가 받지 않는 템플릿으로 고치면, 템플릿으로 거부된다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 템플릿을 바꿈

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

같은 정의가 있고 아무 권한도 받지 않은 사용자가 이름을 고치면, 권한 부족으로 거부된다. 이 엔티티는 어느 스코프에도 없어 권한을 받을 길이 없다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-update-giving-no-value-answers-the-node-unchanged](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 값을 하나도 주지 않고 고치면, 아무것도 바뀌지 않은 노드가 답으로 온다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1을 아무것도 바꾸지 않고 고침

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [changing-only-the-filter-labels-keeps-the-group-labels](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

필터 라벨과 묶음 라벨이 모두 있는 정의를 슈퍼관리자가 필터 라벨만 고치면, 필터 라벨은 새 값이고 묶음 라벨은 그대로다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 필터 라벨을 kernel_id로 제한한다, 묶음 라벨을 agent_id로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 필터 라벨을 바꿈

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = ['session_id']
  - options.group_labels = ['agent_id']
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [clearing-the-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

설명이 있는 정의를 슈퍼관리자가 설명을 비우며 고치면, 설명이 없어진다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 설명을 비움

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id의 이름을 고치면, 대상이 없다는 것으로 거부된다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 아무것도 갖지 않은 id의 이름을 바꿈

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [moving-a-preset-to-a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 아무것도 갖지 않은 분류 id로 고치면, 분류가 없다는 이유로 거부된다. 저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 아무것도 갖지 않은 분류 id로 옮김

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [moving-a-preset-to-another-category-points-the-node-at-that-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

분류 둘 중 한쪽에 속한 정의를 슈퍼관리자가 다른 분류로 옮기면, 답의 분류가 그것을 가리킨다

Given

- 분류 둘과 한쪽에 속한 정의 하나, superadmin 한 명
  - 분류 home-1
  - 분류 elsewhere-1
  - 질의 정의 preset-1: 분류 아래에 있다
  - 도메인 home-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 다른 분류로 옮김

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id: 다른 분류와 같다
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-superadmin-changes-the-template-and-the-rest-stays](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

정의 하나가 있고 슈퍼관리자가 템플릿만 고치면, 템플릿은 새 값이고 나머지는 그대로다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 템플릿을 바꿈

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'sum by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-user-edit-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 고친다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'cpu-by-session'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### executing

#### [a-filter-label-the-preset-allows-reaches-the-query-as-an-exact-match](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

필터 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록 안의 라벨로 실행하면, 대역이 받은 질의에 그 라벨이 정확히 일치하는 조건으로 들어 있다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다, 필터 라벨을 kernel_id로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 kernel_id=k1 라벨로 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{kernel_id="k1"}[1h]))')])]

#### [a-filter-label-the-preset-does-not-allow-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

필터 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, 외부에 질의하기 전에 라벨로 거부된다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 필터 라벨을 kernel_id로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 session_id=s1 라벨로 실행

Then

- 거부된다
  - 거부: PrometheusQueryPresetInvalidLabel

#### [a-group-label-the-preset-allows-reaches-the-query](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

묶음 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록 안의 라벨로 실행하면, 대역이 받은 질의의 묶음에 그 라벨이 들어 있다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다, 묶음 라벨을 agent_id로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 agent_id로 묶어 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by (agent_id) (rate(container_cpu_seconds_total{}[1h]))')])]

#### [a-group-label-the-preset-does-not-allow-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

묶음 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, 같은 자리에서 라벨로 거부된다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 묶음 라벨을 agent_id로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 session_id로 묶어 실행

Then

- 거부된다
  - 거부: PrometheusQueryPresetInvalidLabel

#### [a-preset-and-a-request-naming-no-window-run-with-the-server-default](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

창이 없는 정의를 슈퍼관리자가 창 없이 실행하면, 대역이 받은 질의의 창이 서버 설정의 기본 창이다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 아무것도 주지 않고 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

#### [a-preset-restricting-no-label-runs-with-any-label](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

허용 라벨 목록이 빈 정의를 슈퍼관리자가 아무 라벨이나 주고 실행하면, 대역이 받은 질의에 그 라벨이 들어 있다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 session_id=s1 라벨로, agent_id로 묶어 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by (agent_id) (rate(container_cpu_seconds_total{session_id="s1"}[1h]))')])]

#### [a-query-prometheus-refuses-is-refused-as-a-failed-metric-read](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

라벨 없이는 빈 질의로 렌더되는 정의를 슈퍼관리자가 라벨 없이 실행하면, Prometheus가 그 질의를 거부하고 그 거부가 지표를 얻지 못했다는 이유로 그대로 올라온다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 라벨 없이는 빈 질의로 렌더되는 템플릿을 갖고 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 아무것도 주지 않고 실행

Then

- 거부된다
  - 거부: FailedToGetMetric

#### [a-request-naming-no-window-runs-with-the-window-of-the-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

창이 적힌 정의를 슈퍼관리자가 창 없이 실행하면, 대역이 받은 질의의 창이 정의의 창이다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 아무것도 주지 않고 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

#### [a-user-who-may-read-a-preset-may-not-run-it](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

아무 권한도 받지 않은 사용자는 정의를 읽을 수 있지만 실행하면 권한 부족으로 거부된다. 이 엔티티는 어느 스코프에도 없어 역할로는 권한을 받을 길이 없다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 아무것도 주지 않고 실행

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [running-a-preset-over-a-range-is-a-range-query](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

슈퍼관리자가 시작·끝·간격을 주고 실행하면, 대역이 범위 질의로 답한다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 구간을 주고 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'matrix'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

#### [running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

창이 없는 정의를 슈퍼관리자가 창을 주고 구간 없이 실행하면, 순간 질의로 답하고 대역이 받은 질의에 요청의 창이 들어 있다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 창 30s로 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[30s]))')])]

#### [running-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id로 실행하면, 대상이 없다는 것으로 거부된다. 실행은 서비스가 정의를 직접 읽어 내므로 고치기와 지우기의 대상 없음과 종류가 다르다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 아무것도 갖지 않은 id을 아무것도 주지 않고 실행

Then

- 거부된다
  - 거부: PrometheusQueryPresetNotFound

#### [running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

아무 권한도 받지 않은 사용자가 아무것도 갖지 않은 id로 실행하면, 대상이 없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 아무것도 갖지 않은 id을 아무것도 주지 않고 실행

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-window-a-request-names-wins-over-the-window-of-the-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

창이 적힌 정의를 슈퍼관리자가 다른 창을 주고 실행하면, 대역이 받은 질의의 창이 요청의 창이다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 창 30s로 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[30s]))')])]

#### [turning-enforcement-off-lets-a-user-run-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 실행한다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1: 창이 1h로 적혀 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1을 아무것도 주지 않고 실행

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

### loading

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py) — pass

정의가 있어도 빈 id 목록으로 읽으면, 빈 답이 온다

Given

- 정의 1개와, user 한 명
  - 질의 정의 wanted-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - answer = []

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py) — pass

정의 둘과 없는 id 하나를 섞어 한 번에 읽으면, 있는 둘은 노드로 없는 하나는 빈 자리로 오고 순서가 준 순서와 같다

Given

- 정의 2개와, user 한 명
  - 질의 정의 wanted-1
  - 질의 정의 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.batch_load_by_ids — user-1이 심은 정의 2개의 id와 없는 id 하나를 한 번에 조회

Then

- 준 순서대로, 없는 id 자리는 비어서 온다
  - len = 3
  - [0]: 1번째로 준 id의 정의 전체와 같다
  - [1]: 2번째로 준 id의 정의 전체와 같다
  - [2] = None

### previewing

#### [a-query-prometheus-refuses-is-refused-as-an-evaluation-failure](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 빈 질의로 렌더되는 템플릿을 미리 보면, Prometheus가 그 질의를 거부하고 그 거부가 평가 실패로 바뀌어 올라온다. 실행의 같은 줄과 다른 것으로 거부된다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 빈 질의로 렌더되는 템플릿을 미리 봄

Then

- 거부된다
  - 거부: PrometheusQueryEvaluationFailed

#### [a-template-the-renderer-refuses-cannot-be-previewed](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 렌더러가 받지 않는 템플릿을 미리 보면, 외부에 묻기 전에 템플릿으로 거부된다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 렌더러가 받지 않는 템플릿을 미리 봄

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-who-is-not-the-superadmin-may-not-preview-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 아닌 사용자가 미리 보려 하면, 역할로 막힌다

Given

- 정의가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿을 미리 봄

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [previewing-a-template-is-an-instant-query-with-the-server-window-and-no-label](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 템플릿만 주고 미리 보면, 순간 질의로 답하고 대역이 받은 질의의 창은 서버 설정의 기본 창이며 라벨은 비어 있다

Given

- 정의가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿을 미리 봄

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

#### [the-monitor-role-previews-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

모니터 역할이 템플릿을 미리 보면, 대역이 답한 결과가 온다. 전역 문은 읽기에 한해 그 역할을 지나게 한다

Given

- 정의가 하나도 없고, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿을 미리 봄

Then

- 대역이 받은 질의를 실은 결과가 온다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

### purging

#### [a-user-granted-nothing-may-not-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

같은 정의가 있고 아무 권한도 받지 않은 사용자가 지우면, 권한 부족으로 거부된다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-removes-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

정의 하나가 있고 슈퍼관리자가 지우면, 지운 id를 실은 답이 온다

Given

- 이미 있는 정의 하나와, superadmin 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 지운 정의를 답한다
  - id: 심은 정의와 같다

#### [turning-enforcement-off-lets-a-user-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 지운 정의를 답한다
  - id: 심은 정의와 같다

### reading

#### [a-call-carrying-no-user-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py) — pass

정의 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증으로 거부된다

Given

- 이미 있는 정의 하나, 부를 사람 없음
  - 질의 정의 preset-1

When

- PrometheusQueryPresetAdapter.get — 사용자 컨텍스트 없이 preset-1을 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py) — pass

정의 하나가 있고 아무 권한도 받지 않은 사용자가 id로 조회하면, 그 정의 전체가 답으로 온다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.get — user-1이 preset-1로 조회

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - name = 'preset-1'
  - description = '심어둔 질의 정의'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-anyone](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 읽기는 인증만 보므로 권한 문이 먼저 막지 않는다

Given

- 이미 있는 정의 하나와, user 한 명
  - 질의 정의 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.get — user-1이 아무것도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### searching

#### [a-call-carrying-no-user-may-not-search-presets](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

정의 하나가 있고 사용자 컨텍스트 없이 훑으면, 인증으로 거부된다

Given

- 이미 있는 정의 하나, 부를 사람 없음
  - 질의 정의 preset-1

When

- PrometheusQueryPresetAdapter.search — 사용자 컨텍스트 없이 전체 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-counts-every-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

정의 둘이 있고 아무 권한도 받지 않은 사용자가 필터 없이 훑으면, 둘을 모두 센다

Given

- 정의 2개와, user 한 명
  - 질의 정의 wanted-1
  - 질의 정의 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 심은 정의가 모두, 그리고 그것만 세어진다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-category-keeps-only-the-presets-filed-under-it](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

두 분류에 정의가 나뉘어 있을 때 한 분류로 걸러 훑으면, 그 분류의 것만 남는다

Given

- 두 분류에 나뉜 정의 셋과, user 한 명
  - 분류 wanted-1
  - 분류 other-1
  - 질의 정의 wanted-2: 분류 아래에 있다
  - 질의 정의 beside-1: 분류 아래에 있다
  - 질의 정의 elsewhere-1: 분류 아래에 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 분류로 걸러 조회

Then

- 심은 정의가 모두, 그리고 그것만 세어진다
  - items = ['beside-1', 'wanted-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-name-keeps-only-the-preset-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

이름이 다른 정의 셋이 있을 때 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 정의 3개와, user 한 명
  - 질의 정의 wanted-1
  - 질의 정의 other-1
  - 질의 정의 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 이름 wanted-1으로 걸러 조회

Then

- 이름으로 고른 하나만 세어진다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

정의 열하나가 있을 때 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 정의 11개와, user 한 명
  - 질의 정의 wanted-1
  - 질의 정의 other-1
  - 질의 정의 other-2
  - 질의 정의 other-3
  - 질의 정의 other-4
  - 질의 정의 other-5
  - 질의 정의 other-6
  - 질의 정의 other-7
  - 질의 정의 other-8
  - 질의 정의 other-9
  - 질의 정의 other-10
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 한 쪽만 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

