## deployment_revision_preset

[what it guarantees](/src/ai/backend/manager/api/adapters/deployment_revision_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/deployment_revision_preset/adapter.py)

Scenario: incomplete 10 / 10

- built from ops (8)
  - available_presets — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - batch_load_by_ids — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - create — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - get — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - partial_bulk_purge — representative success ✓ · representative refusal ✗ — SCENARIO-GAP
  - purge — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - search — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
  - search_resource_slots — representative success ✗ · representative refusal ✗ — SCENARIO-GAP
- ops + direct implementation (2)
  - partial_bulk_update — success present 2 · refusal absent (partial_bulk, single_get_ops) — SCENARIO-GAP
  - update — success absent · refusal absent (single_entity, single_get_ops) — SCENARIO-GAP

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk-a-preset-reader-purges-none-of-several-presets) | answered |
| [슈퍼관리자가 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk-purging-several-presets-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk-a-preset-reader-edits-none-of-several-presets) | answered |
| [슈퍼관리자가 프리셋 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다](#partial_bulk-the-superadmin-edits-several-presets-at-once) | answered |

### partial_bulk_purge

<a id="partial_bulk-a-preset-reader-purges-none-of-several-presets"></a>

#### [a-preset-reader-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py) — pass

프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 public-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge — user-1이 프리셋 2개를 한 번에 purge 함

Then

- 처리된 프리셋 없이 프리셋이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 심은 프리셋의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 심은 프리셋의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-purging-several-presets-answers-for-the-missing-one"></a>

#### [purging-several-presets-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py) — pass

슈퍼관리자가 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 슈퍼관리자 한 명
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 public-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 슈퍼관리자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge — user-1이 프리셋 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 프리셋이 모두 설명 '미리 만들어 둔 프리셋'으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 심은 프리셋의 id와 같다
  - successes[0].description = '미리 만들어 둔 프리셋'
  - successes[1].id: 심은 프리셋의 id와 같다
  - successes[1].description = '미리 만들어 둔 프리셋'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk-a-preset-reader-edits-none-of-several-presets"></a>

#### [a-preset-reader-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py) — pass

프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 public-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 설명을 한 번에 고침

Then

- 처리된 프리셋 없이 프리셋이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 심은 프리셋의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 심은 프리셋의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py) — pass

슈퍼관리자가 프리셋 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 슈퍼관리자 한 명
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 레플리카 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 public-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 슈퍼관리자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 설명을 한 번에 고침

Then

- 프리셋이 모두 설명 '한 번에 고친 설명'으로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 심은 프리셋의 id와 같다
  - successes[0].description = '한 번에 고친 설명'
  - successes[1].id: 심은 프리셋의 id와 같다
  - successes[1].description = '한 번에 고친 설명'
  - failed = []

