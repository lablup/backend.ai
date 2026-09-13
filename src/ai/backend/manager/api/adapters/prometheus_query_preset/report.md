## prometheus_query_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/prometheus_query_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/prometheus_query_preset/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 존재하지 않는 카테고리 id를 지정해 생성하면, 카테고리가 없다는 이유로 거부된다. 저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 존재하지 않는 카테고리 id 아래에 이름 cpu-by-kernel(으)로 생성

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [a-name-another-preset-already-holds-is-allowed](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

이미 다른 프리셋이 사용 중인 이름으로 슈퍼관리자가 다시 생성하면, 생성된다. 프리셋의 이름에는 유일 제약이 없다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이미 있는 이름 preset-1(으)로 다시 생성

Then

- 생성한 프리셋 전체가 반환된다
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

슈퍼관리자가 렌더러가 받지 않는 템플릿으로 생성하면, 템플릿 오류로 거부된다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 프리셋을 생성하려 하면, 역할 부족으로 거부된다

Given

- 프리셋이 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-preset-under-a-category-points-the-node-at-that-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

카테고리 하나가 있고 슈퍼관리자가 그 카테고리를 지정해 생성하면, 응답의 카테고리가 그것을 가리킨다

Given

- 카테고리 하나와, superadmin 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 미리 만들어 둔 카테고리 아래에 이름 cpu-by-kernel(으)로 생성

Then

- 생성한 프리셋 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id: 미리 만들어 둔 카테고리와 같다
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [creating-a-preset-with-a-window-carries-that-window-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

슈퍼관리자가 시간 창을 함께 지정해 생성하면, 노드에 그 시간 창이 담긴다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 생성한 프리셋 전체가 반환된다
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

슈퍼관리자가 이름, 지표 이름, 템플릿, 허용 라벨 목록만 지정해 생성하면, 순위는 0이고 카테고리·설명·시간 창은 비어 있는 노드 전체가 반환된다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 생성한 프리셋 전체가 반환된다
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

모니터 역할이 프리셋을 생성하려 하면, 역할 부족으로 거부된다. 전역 역할 검사는 읽기에만 그 역할을 허용한다

Given

- 프리셋이 하나도 없고, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py) — pass

권한 검사를 꺼도 프리셋 생성은 여전히 거부된다. 생성은 권한 그래프가 아니라 역할로 보호되기 때문이다

Given

- 프리셋이 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.create — user-1이 이름 cpu-by-kernel(으)로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-stored-template-the-renderer-refuses-does-not-block-renaming](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

렌더러가 받지 않는 템플릿을 가진 프리셋을 슈퍼관리자가 이름만 수정하면, 이름은 새 값이다. 템플릿 검증은 요청이 템플릿을 지정한 때만 실행된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 렌더러가 받지 않는 템플릿을 갖는다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (이름 변경)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'cpu-by-session'
  - description = '미리 만들어 둔 질의 프리셋'
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

슈퍼관리자가 렌더러가 받지 않는 템플릿으로 수정하면, 템플릿 오류로 거부된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (템플릿 변경)

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

같은 프리셋이 있고 아무 권한도 없는 사용자가 이름을 수정하면, 권한 부족으로 거부된다. 이 엔티티는 어느 스코프에도 속하지 않아 권한을 받을 방법이 없다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (이름 변경)

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-update-giving-no-value-answers-the-node-unchanged](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 값을 하나도 지정하지 않고 수정하면, 아무것도 바뀌지 않은 노드가 반환된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (빈 요청)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 질의 프리셋'
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

필터 라벨과 그룹 라벨이 모두 있는 프리셋을 슈퍼관리자가 필터 라벨만 수정하면, 필터 라벨은 새 값이고 그룹 라벨은 그대로다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 필터 라벨을 kernel_id(으)로 제한한다, 그룹 라벨을 agent_id(으)로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (필터 라벨 변경)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 질의 프리셋'
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

설명이 있는 프리셋을 슈퍼관리자가 설명을 비우도록 수정하면, 설명이 없어진다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (설명 비우기)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
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

슈퍼관리자가 존재하지 않는 id의 이름을 수정하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 존재하지 않는 id 수정 (이름 변경)

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [moving-a-preset-to-a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 카테고리 id로 수정하면, 카테고리가 없다는 이유로 거부된다. 저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (존재하지 않는 카테고리 id로 이동)

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [moving-a-preset-to-another-category-points-the-node-at-that-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

카테고리 둘 중 한쪽에 속한 프리셋을 슈퍼관리자가 다른 카테고리로 옮기면, 응답의 카테고리가 그것을 가리킨다

Given

- 카테고리 둘과 한쪽에 속한 프리셋 하나, superadmin 한 명
  - 카테고리 home-1
  - 카테고리 elsewhere-1
  - 질의 프리셋 preset-1: 카테고리에 속한다
  - 도메인 home-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (다른 카테고리로 이동)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 질의 프리셋'
  - rank = 0
  - category_id: 다른 카테고리와 같다
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-superadmin-changes-the-template-and-the-rest-stays](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py) — pass

프리셋 하나가 있고 슈퍼관리자가 템플릿만 수정하면, 템플릿은 새 값이고 나머지는 그대로다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (템플릿 변경)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 질의 프리셋'
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

권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 수정할 수 있다. 수정은 역할이 아니라 권한 그래프로 보호되기 때문이다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.update — user-1이 preset-1 수정 (이름 변경)

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'cpu-by-session'
  - description = '미리 만들어 둔 질의 프리셋'
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

필터 라벨을 제한해 둔 프리셋을 슈퍼관리자가 그 목록 안의 라벨로 실행하면, 모의 서버가 받은 질의에 그 라벨이 정확히 일치하는 조건으로 들어 있다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다, 필터 라벨을 kernel_id(으)로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (필터 라벨 kernel_id=k1)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{kernel_id="k1"}[1h]))')])]

#### [a-filter-label-the-preset-does-not-allow-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

필터 라벨을 제한해 둔 프리셋을 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, 외부에 질의하기 전에 라벨 오류로 거부된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 필터 라벨을 kernel_id(으)로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (필터 라벨 session_id=s1)

Then

- 거부된다
  - 거부: PrometheusQueryPresetInvalidLabel

#### [a-group-label-the-preset-allows-reaches-the-query](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

그룹 라벨을 제한해 둔 프리셋을 슈퍼관리자가 그 목록 안의 라벨로 실행하면, 모의 서버가 받은 질의의 그룹에 그 라벨이 들어 있다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다, 그룹 라벨을 agent_id(으)로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (그룹 라벨 agent_id)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by (agent_id) (rate(container_cpu_seconds_total{}[1h]))')])]

#### [a-group-label-the-preset-does-not-allow-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

그룹 라벨을 제한해 둔 프리셋을 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, 같은 단계에서 라벨 오류로 거부된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 그룹 라벨을 agent_id(으)로 제한한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (그룹 라벨 session_id)

Then

- 거부된다
  - 거부: PrometheusQueryPresetInvalidLabel

#### [a-preset-and-a-request-naming-no-window-run-with-the-server-default](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

시간 창이 없는 프리셋을 슈퍼관리자가 시간 창 없이 실행하면, 모의 서버가 받은 질의의 시간 창이 서버 설정의 기본 시간 창이다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (아무것도 지정하지 않음)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

#### [a-preset-restricting-no-label-runs-with-any-label](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

허용 라벨 목록이 빈 프리셋을 슈퍼관리자가 아무 라벨이나 지정해 실행하면, 모의 서버가 받은 질의에 그 라벨이 들어 있다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (필터 라벨 session_id=s1, 그룹 라벨 agent_id)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by (agent_id) (rate(container_cpu_seconds_total{session_id="s1"}[1h]))')])]

#### [a-query-prometheus-refuses-is-refused-as-a-failed-metric-read](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

라벨 없이는 빈 질의로 렌더되는 프리셋을 슈퍼관리자가 라벨 없이 실행하면, Prometheus가 그 질의를 거부하고 그 거부가 지표를 얻지 못했다는 이유로 그대로 전파된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 라벨 없이는 빈 질의로 렌더되는 템플릿을 갖는다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (아무것도 지정하지 않음)

Then

- 거부된다
  - 거부: FailedToGetMetric

#### [a-request-naming-no-window-runs-with-the-window-of-the-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

시간 창이 설정된 프리셋을 슈퍼관리자가 시간 창 없이 실행하면, 모의 서버가 받은 질의의 시간 창이 프리셋의 시간 창이다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (아무것도 지정하지 않음)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

#### [a-user-who-may-read-a-preset-may-not-run-it](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

아무 권한도 없는 사용자는 프리셋을 조회할 수 있지만 실행하면 권한 부족으로 거부된다. 이 엔티티는 어느 스코프에도 속하지 않아 역할로는 권한을 받을 방법이 없다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (아무것도 지정하지 않음)

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [running-a-preset-over-a-range-is-a-range-query](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

슈퍼관리자가 시작·끝·간격을 지정해 실행하면, 모의 서버가 범위 질의로 응답한다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (조회 구간 지정)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'matrix'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

#### [running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

시간 창이 없는 프리셋을 슈퍼관리자가 시간 창을 지정하고 조회 구간 없이 실행하면, 순간 질의로 응답하고 모의 서버가 받은 질의에 요청의 시간 창이 들어 있다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (시간 창 30s)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[30s]))')])]

#### [running-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

슈퍼관리자가 존재하지 않는 id로 실행하면, 대상을 찾을 수 없다는 이유로 거부된다. 실행은 서비스가 프리셋을 직접 읽어서 내는 오류라 수정과 삭제의 대상 없음과 종류가 다르다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 존재하지 않는 id 실행 (아무것도 지정하지 않음)

Then

- 거부된다
  - 거부: PrometheusQueryPresetNotFound

#### [running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 id로 실행하면, 대상 없음이 아니라 권한 부족으로 거부된다. 없는 행에는 부여된 권한도 없기 때문이다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 존재하지 않는 id 실행 (아무것도 지정하지 않음)

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-window-a-request-names-wins-over-the-window-of-the-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

시간 창이 설정된 프리셋을 슈퍼관리자가 다른 시간 창을 지정해 실행하면, 모의 서버가 받은 질의의 시간 창이 요청의 시간 창이다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (시간 창 30s)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[30s]))')])]

#### [turning-enforcement-off-lets-a-user-run-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 실행할 수 있다. 실행은 역할이 아니라 권한 그래프로 보호되기 때문이다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1: 시간 창이 1h(으)로 설정돼 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.execute_preset — user-1이 preset-1 실행 (아무것도 지정하지 않음)

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

### loading

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py) — pass

프리셋이 있어도 빈 id 목록으로 조회하면, 빈 응답이 반환된다

Given

- 프리셋 1개와, user 한 명
  - 질의 프리셋 wanted-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - answer = []

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py) — pass

프리셋 둘과 없는 id 하나를 섞어 한 번에 조회하면, 있는 둘은 노드로 없는 하나는 빈 항목으로 반환되고 순서가 요청한 순서와 같다

Given

- 프리셋 2개와, user 한 명
  - 질의 프리셋 wanted-1
  - 질의 프리셋 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 프리셋 2개의 id와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로, 없는 id 자리는 비어서 반환된다
  - len = 3
  - [0]: 1번째로 요청한 id의 프리셋 전체와 같다
  - [1]: 2번째로 요청한 id의 프리셋 전체와 같다
  - [2] = None

### previewing

#### [a-query-prometheus-refuses-is-refused-as-an-evaluation-failure](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 빈 질의로 렌더되는 템플릿을 미리 보면, Prometheus가 그 질의를 거부하고 그 거부가 평가 실패로 바뀌어 전파된다. 실행의 같은 시나리오와 다른 오류로 거부된다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 빈 질의로 렌더되는 템플릿 미리 보기

Then

- 거부된다
  - 거부: PrometheusQueryEvaluationFailed

#### [a-template-the-renderer-refuses-cannot-be-previewed](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 렌더러가 받지 않는 템플릿을 미리 보면, 외부에 질의하기 전에 템플릿 오류로 거부된다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 렌더러가 받지 않는 템플릿 미리 보기

Then

- 거부된다
  - 거부: InvalidMetricPresetTemplate

#### [a-user-who-is-not-the-superadmin-may-not-preview-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 아닌 사용자가 미리 보려 하면, 역할 부족으로 거부된다

Given

- 프리셋이 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿 미리 보기

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [previewing-a-template-is-an-instant-query-with-the-server-window-and-no-label](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

슈퍼관리자가 템플릿만 지정해 미리 보면, 순간 질의로 응답하고 모의 서버가 받은 질의의 시간 창은 서버 설정의 기본 시간 창이며 라벨은 비어 있다

Given

- 프리셋이 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿 미리 보기

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

#### [the-monitor-role-previews-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py) — pass

모니터 역할이 템플릿을 미리 보면, 모의 서버가 응답한 결과가 반환된다. 전역 역할 검사는 읽기에 한해 그 역할을 허용한다

Given

- 프리셋이 하나도 없고, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.admin_preview — user-1이 템플릿 미리 보기

Then

- 모의 서버가 받은 질의를 담은 결과가 반환된다
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

### purging

#### [a-user-granted-nothing-may-not-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

같은 프리셋이 있고 아무 권한도 없는 사용자가 삭제하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-removes-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

프리셋 하나가 있고 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 삭제한 프리셋을 응답한다
  - id: 미리 만들어 둔 프리셋와 같다

#### [turning-enforcement-off-lets-a-user-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 삭제할 수 있다. 삭제는 역할이 아니라 권한 그래프로 보호되기 때문이다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 삭제한 프리셋을 응답한다
  - id: 미리 만들어 둔 프리셋와 같다

### reading

#### [a-call-carrying-no-user-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py) — pass

프리셋 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증 실패로 거부된다

Given

- 이미 있는 프리셋 하나, 호출자 없음
  - 질의 프리셋 preset-1

When

- PrometheusQueryPresetAdapter.get — 사용자 컨텍스트 없이 preset-1 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py) — pass

프리셋 하나가 있고 아무 권한도 없는 사용자가 id로 조회하면, 그 프리셋 전체가 반환된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.get — user-1이 preset-1(으)로 조회

Then

- 미리 만들어 둔 프리셋 전체가 반환된다
  - id: 미리 만들어 둔 프리셋와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 질의 프리셋'
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

아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 조회는 인증만 확인하므로 권한 검사가 먼저 막지 않는다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 질의 프리셋 preset-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.get — user-1이 존재하지 않는 id(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### searching

#### [a-call-carrying-no-user-may-not-search-presets](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

프리셋 하나가 있고 사용자 컨텍스트 없이 검색하면, 인증 실패로 거부된다

Given

- 이미 있는 프리셋 하나, 호출자 없음
  - 질의 프리셋 preset-1

When

- PrometheusQueryPresetAdapter.search — 사용자 컨텍스트 없이 전체 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-counts-every-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

프리셋 둘이 있고 아무 권한도 없는 사용자가 필터 없이 검색하면, 둘 다 집계된다

Given

- 프리셋 2개와, user 한 명
  - 질의 프리셋 wanted-1
  - 질의 프리셋 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 미리 만들어 둔 프리셋이 모두, 그리고 그것만 집계된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-category-keeps-only-the-presets-filed-under-it](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

두 카테고리에 프리셋이 나뉘어 있을 때 한 카테고리 필터로 검색하면, 그 카테고리의 프리셋만 반환된다

Given

- 두 카테고리에 나뉜 프리셋 셋과, user 한 명
  - 카테고리 wanted-1
  - 카테고리 other-1
  - 질의 프리셋 wanted-2: 카테고리에 속한다
  - 질의 프리셋 beside-1: 카테고리에 속한다
  - 질의 프리셋 elsewhere-1: 카테고리에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 카테고리 필터로 조회

Then

- 미리 만들어 둔 프리셋이 모두, 그리고 그것만 집계된다
  - items = ['beside-1', 'wanted-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-name-keeps-only-the-preset-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

이름이 다른 프리셋 셋이 있을 때 이름 필터로 검색하면, 그 이름의 프리셋만 반환된다

Given

- 프리셋 3개와, user 한 명
  - 질의 프리셋 wanted-1
  - 질의 프리셋 other-1
  - 질의 프리셋 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 wanted-1 이름 필터로 조회

Then

- 이름 필터에 맞는 하나만 집계된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py) — pass

프리셋 11개가 있을 때 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 프리셋 11개와, user 한 명
  - 질의 프리셋 wanted-1
  - 질의 프리셋 other-1
  - 질의 프리셋 other-2
  - 질의 프리셋 other-3
  - 질의 프리셋 other-4
  - 질의 프리셋 other-5
  - 질의 프리셋 other-6
  - 질의 프리셋 other-7
  - 질의 프리셋 other-8
  - 질의 프리셋 other-9
  - 질의 프리셋 other-10
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 한 페이지만 반환되고 다음 페이지가 있다고 응답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

