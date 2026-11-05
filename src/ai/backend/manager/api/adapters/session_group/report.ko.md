## session_group

[배경](/src/ai/backend/manager/api/adapters/session_group/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session_group/adapter.py)

시나리오: 완성

- ops 구성 (5)
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - global_search: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (2)
  - bulk_get_ids: 성공 있음 2 · 거부 있음 1 (partial_bulk)
  - get: 성공 있음 1 · 거부 있음 2 (single_entity)

**create**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 그 사용자가 소유자이고 입력한 배치 정책을 가진 세션 그룹이 옵니다](#creating-a-user-granted-create-in-a-project-creates-a-session-group-there) | 성공 |
| [다른 프로젝트에서만 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 권한 부족으로 거부되고 세션 그룹은 생기지 않습니다](#creating-a-user-granted-create-only-in-another-project-may-not-create-a-session-group) | 거부 |
| [프로젝트에서 세션 그룹 읽기 권한만 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 권한 부족으로 거부되고 세션 그룹은 생기지 않습니다](#creating-a-user-granted-only-read-in-a-project-may-not-create-a-session-group) | 거부 |

**global_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 그 프로젝트를 방향 pack 으로 걸러 전체 검색하면, 사용자가 만든 세션 그룹만 오고 방향이 spread 인 배포의 세션 그룹은 빠집니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#searching-a-filter-on-the-placement-direction-leaves-the-packed-group) | 성공 |
| [superadmin 이 그 프로젝트의 세션 그룹을 방향 오름차순으로 검색하면, 방향이 pack 인 사용자의 세션 그룹이 먼저 오고 방향이 spread 인 배포의 세션 그룹이 그다음에 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#searching-ordering-by-the-placement-direction-puts-pack-before-spread) | 성공 |
| [아무 권한도 받지 않은 superadmin 이 한 프로젝트를 필터로 전체 검색하면, 그 프로젝트의 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹이 모두 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#searching-the-superadmin-finds-a-users-group-and-a-deployments-group) | 성공 |
| [그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 superadmin 이 아닌 사용자가 전체 검색하면, 역할로 거부됩니다](#searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 그 세션 그룹의 id 가 오고 멤버 세션은 세션 그룹이 비워진 채 남습니다](#purging-the-owner-purges-a-users-session-group-keeping-its-members) | 성공 |
| [자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 배포의 replica group 이 가진 세션 그룹을 삭제하면, replica group 이 사용 중이라는 것으로 거부되고 세션 그룹은 남습니다](#purging-a-deployments-session-group-is-refused-as-in-use) | 거부 |
| [아무 권한도 받지 않은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 권한 부족으로 거부되고 세션 그룹은 남습니다](#purging-a-user-granted-nothing-may-not-purge-a-session-group) | 거부 |
| [자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 권한 부족으로 거부되고 세션 그룹은 남습니다](#purging-a-user-granted-only-read-may-not-purge-a-session-group) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그 프로젝트 범위로 검색하면, 배포의 replica group 이 가진 세션 그룹과 다른 프로젝트의 세션 그룹은 빠지고 그 프로젝트의 사용자가 생성한 세션 그룹만 옵니다](#scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project) | 성공 |
| [자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 두 스코프를 함께 넘겨 검색하면, 자기가 생성한 세션 그룹과 그 프로젝트에서 다른 사용자가 생성한 세션 그룹이 합쳐져 오고 배포의 replica group 이 가진 세션 그룹은 빠집니다](#scoped_searching-a-user-scope-and-a-project-scope-are-joined) | 성공 |
| [자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자가 자기 스코프로 검색하면, 두 프로젝트에 자기가 생성한 세션 그룹이 오고 배포의 replica group 이 가진 세션 그룹과 다른 사용자가 생성한 세션 그룹은 빠집니다](#scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope) | 성공 |
| [다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들이 있는 프로젝트 범위로 검색하면, 권한 부족으로 거부됩니다](#scoped_searching-searching-a-project-not-granted-is-refused) | 거부 |
| [세션 그룹들이 있는 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들을 생성한 사용자의 스코프로 검색하면, 권한 부족으로 거부됩니다](#scoped_searching-searching-another-users-scope-is-refused) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 생성한 세션 그룹의 방향만 변경하면, 강제 수준은 그대로인 그 세션 그룹이 옵니다](#updating-an-owner-changes-only-the-direction) | 성공 |
| [자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 생성한 세션 그룹의 방향과 강제 수준을 변경하면, 두 항목이 변경된 그 세션 그룹이 옵니다](#updating-an-owner-changes-the-direction-and-the-enforcement) | 성공 |
| [자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기 배포의 replica group 이 가진 세션 그룹 정책을 변경하면, 권한이 아니라 사용 중이라는 것으로 거부됩니다](#updating-a-deployments-session-group-is-refused-as-in-use) | 거부 |
| [자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 생성한 세션 그룹의 정책을 변경하면, 권한 부족으로 거부됩니다](#updating-an-owner-granted-only-read-may-not-update) | 거부 |

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹을 함께 읽으면, 요청한 순서대로 그 세션 그룹과 빈 값이 옵니다](#bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group) | 성공 |
| [superadmin 이 아무 세션 그룹도 갖지 않은 id 로 여럿 읽기로 조회하면, 그 항목이 빈 값으로 옵니다. 권한 검사를 통과하는 사람이어야 읽기의 응답을 볼 수 있어 요청한 사용자가 superadmin 입니다](#bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자가 생성한 세션 그룹을 id 로 여럿 읽기로 조회하면, 그 항목이 권한 부족으로 거부됩니다](#bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 생성한 세션 그룹을 id 로 조회하면, 그 세션 그룹이 옵니다](#reading-a-granted-user-reads-a-users-session-group) | 성공 |
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 배포의 replica group 이 가진 세션 그룹을 id 로 조회하면, 권한이 아니라 대상이 없다는 것으로 거부됩니다](#reading-a-deployments-session-group-is-not-found-even-when-granted) | 거부 |
| [아무 권한도 받지 않은 사용자가 사용자가 생성한 세션 그룹을 id 로 조회하면, 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-session-group) | 거부 |

### create

<a id="creating-a-user-granted-create-in-a-project-creates-a-session-group-there"></a>

#### [a-user-granted-create-in-a-project-creates-a-session-group-there](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

프로젝트에서 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 그 사용자가 소유자이고 입력한 배치 정책을 가진 세션 그룹이 옵니다

Given

- 한 도메인의 두 프로젝트, 그리고 세션 그룹을 생성할 프로젝트에서 세션 그룹 생성 권한을 받은 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트에서 세션 그룹 생성 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-creator-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-creator-1: session_group 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 session-group-creator-1 보유

When

- SessionGroupAdapter.create: user-1 이 그 프로젝트에 방향은 퍼뜨리기, 강제 수준은 선호인 세션 그룹을 생성합니다

Then

- 생성한 사용자가 소유자이고 입력한 배치 정책을 가진 세션 그룹 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: id 와 같다
  - domain_id: 그 도메인의 id 와 같다
  - project_id: 그 프로젝트의 id 와 같다
  - owner_user_id: 생성한 사용자의 id 와 같다
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.PREFERRED: 'preferred'>
  - created_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="creating-a-user-granted-create-only-in-another-project-may-not-create-a-session-group"></a>

#### [a-user-granted-create-only-in-another-project-may-not-create-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

다른 프로젝트에서만 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 권한 부족으로 거부되고 세션 그룹은 생기지 않습니다

Given

- 한 도메인의 두 프로젝트, 그리고 다른 프로젝트에서만 세션 그룹 생성 권한을 받은 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트에서 세션 그룹 생성 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-creator-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-creator-1: session_group 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 session-group-creator-1 보유

When

- SessionGroupAdapter.create: user-1 이 그 프로젝트에 방향은 퍼뜨리기, 강제 수준은 선호인 세션 그룹을 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="creating-a-user-granted-only-read-in-a-project-may-not-create-a-session-group"></a>

#### [a-user-granted-only-read-in-a-project-may-not-create-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

프로젝트에서 세션 그룹 읽기 권한만 받은 사용자가 그 프로젝트에 세션 그룹을 생성하면, 권한 부족으로 거부되고 세션 그룹은 생기지 않습니다

Given

- 한 도메인의 두 프로젝트, 그리고 세션 그룹을 생성할 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.create: user-1 이 그 프로젝트에 방향은 퍼뜨리기, 강제 수준은 선호인 세션 그룹을 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### global_search

<a id="searching-a-filter-on-the-placement-direction-leaves-the-packed-group"></a>

#### [a-filter-on-the-placement-direction-leaves-the-packed-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

superadmin 이 그 프로젝트를 방향 pack 으로 걸러 전체 검색하면, 사용자가 만든 세션 그룹만 오고 방향이 spread 인 배포의 세션 그룹은 빠집니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.global_search: user-3 이 team-1 프로젝트와 방향 pack 를 필터로 전체 검색합니다

Then

- 그 방향으로 배치하는 세션 그룹 하나만 옵니다
  - items: 사용자가 만든 세션 그룹와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-ordering-by-the-placement-direction-puts-pack-before-spread"></a>

#### [ordering-by-the-placement-direction-puts-pack-before-spread](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

superadmin 이 그 프로젝트의 세션 그룹을 방향 오름차순으로 검색하면, 방향이 pack 인 사용자의 세션 그룹이 먼저 오고 방향이 spread 인 배포의 세션 그룹이 그다음에 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.global_search: user-3 이 team-1 프로젝트를 필터로 두고 방향 순서로 전체 검색합니다

Then

- 방향이 pack 인 세션 그룹이 먼저, spread 인 세션 그룹이 그다음에 옵니다
  - items: 사용자가 만든 세션 그룹, 그리고 배포의 replica group 이 가진 세션 그룹와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-finds-a-users-group-and-a-deployments-group"></a>

#### [the-superadmin-finds-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

아무 권한도 받지 않은 superadmin 이 한 프로젝트를 필터로 전체 검색하면, 그 프로젝트의 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹이 모두 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.global_search: user-3 이 team-1 프로젝트를 필터로 전체 검색합니다

Then

- 그 프로젝트의 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹이 모두 옵니다
  - items: 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group"></a>

#### [a-user-who-is-not-a-superadmin-may-not-search-every-session-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 superadmin 이 아닌 사용자가 전체 검색하면, 역할로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.global_search: user-3 이 team-1 프로젝트를 필터로 전체 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### purge

<a id="purging-the-owner-purges-a-users-session-group-keeping-its-members"></a>

#### [the-owner-purges-a-users-session-group-keeping-its-members](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 그 세션 그룹의 id 가 오고 멤버 세션은 세션 그룹이 비워진 채 남습니다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.purge: user-1 이 사용자가 생성한 세션 그룹을 영구 삭제합니다

Then

- 삭제한 사용자가 생성한 세션 그룹의 id 가 옵니다
  - entity_id: 사용자가 생성한 세션 그룹의 id 와 같다

<a id="purging-a-deployments-session-group-is-refused-as-in-use"></a>

#### [a-deployments-session-group-is-refused-as-in-use](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 배포의 replica group 이 가진 세션 그룹을 삭제하면, replica group 이 사용 중이라는 것으로 거부되고 세션 그룹은 남습니다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.purge: user-1 이 배포의 replica group 이 가진 세션 그룹을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: SessionGroupInUse

<a id="purging-a-user-granted-nothing-may-not-purge-a-session-group"></a>

#### [a-user-granted-nothing-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

아무 권한도 받지 않은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 권한 부족으로 거부되고 세션 그룹은 남습니다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 그리고 아무 권한도 받지 않은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.purge: user-1 이 사용자가 생성한 세션 그룹을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-a-user-granted-only-read-may-not-purge-a-session-group"></a>

#### [a-user-granted-only-read-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 생성한 세션 그룹을 삭제하면, 권한 부족으로 거부되고 세션 그룹은 남습니다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다립니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.purge: user-1 이 사용자가 생성한 세션 그룹을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project"></a>

#### [a-granted-user-finds-only-the-users-group-of-the-project](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

그 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그 프로젝트 범위로 검색하면, 배포의 replica group 이 가진 세션 그룹과 다른 프로젝트의 세션 그룹은 빠지고 그 프로젝트의 사용자가 생성한 세션 그룹만 옵니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search: user-3 이 team-1 프로젝트 범위에서 조회합니다

Then

- 그 프로젝트의 사용자가 생성한 세션 그룹만 남습니다
  - items: 그 프로젝트의 사용자가 생성한 세션 그룹
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-scope-and-a-project-scope-are-joined"></a>

#### [a-user-scope-and-a-project-scope-are-joined](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 두 스코프를 함께 넘겨 검색하면, 자기가 생성한 세션 그룹과 그 프로젝트에서 다른 사용자가 생성한 세션 그룹이 합쳐져 오고 배포의 replica group 이 가진 세션 그룹은 빠집니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프와 한 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-reader-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.scoped_search: user-1 이 자기 스코프와 other-1 프로젝트 범위를 함께 조회합니다

Then

- 그 사용자가 생성한 세션 그룹과 다른 프로젝트의 세션 그룹이 합쳐져 남습니다
  - items: 그 사용자가 생성한 세션 그룹과 다른 프로젝트의 세션 그룹
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope"></a>

#### [an-owner-finds-the-groups-they-made-in-their-own-scope](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자가 자기 스코프로 검색하면, 두 프로젝트에 자기가 생성한 세션 그룹이 오고 배포의 replica group 이 가진 세션 그룹과 다른 사용자가 생성한 세션 그룹은 빠집니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.scoped_search: user-1 이 자기 스코프에서 조회합니다

Then

- 그 사용자가 두 프로젝트에 생성한 세션 그룹만 남습니다
  - items: 그 사용자가 두 프로젝트에 생성한 세션 그룹
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-searching-a-project-not-granted-is-refused"></a>

#### [searching-a-project-not-granted-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들이 있는 프로젝트 범위로 검색하면, 권한 부족으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search: user-3 이 team-1 프로젝트 범위에서 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-searching-another-users-scope-is-refused"></a>

#### [searching-another-users-scope-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

세션 그룹들이 있는 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들을 생성한 사용자의 스코프로 검색하면, 권한 부족으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search: user-3 이 user-1의 스코프에서 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="updating-an-owner-changes-only-the-direction"></a>

#### [an-owner-changes-only-the-direction](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 생성한 세션 그룹의 방향만 변경하면, 강제 수준은 그대로인 그 세션 그룹이 옵니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 수정 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 수정 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.update: user-1 이 사용자가 생성한 세션 그룹의 방향만 퍼뜨리기로 변경합니다

Then

- 방향만 변경되고 강제 수준은 그대로인 세션 그룹 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 사용자가 만든 세션 그룹의 id 와 같다
  - domain_id: 그 도메인의 id 와 같다
  - project_id: 그 프로젝트의 id 와 같다
  - owner_user_id: 생성한 사용자의 id 와 같다
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - created_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="updating-an-owner-changes-the-direction-and-the-enforcement"></a>

#### [an-owner-changes-the-direction-and-the-enforcement](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 생성한 세션 그룹의 방향과 강제 수준을 변경하면, 두 항목이 변경된 그 세션 그룹이 옵니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 수정 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 수정 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.update: user-1 이 사용자가 생성한 세션 그룹의 방향을 퍼뜨리기로, 강제 수준을 선호로 변경합니다

Then

- 두 항목이 변경된 세션 그룹 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 사용자가 만든 세션 그룹의 id 와 같다
  - domain_id: 그 도메인의 id 와 같다
  - project_id: 그 프로젝트의 id 와 같다
  - owner_user_id: 생성한 사용자의 id 와 같다
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.PREFERRED: 'preferred'>
  - created_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="updating-a-deployments-session-group-is-refused-as-in-use"></a>

#### [a-deployments-session-group-is-refused-as-in-use](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기 배포의 replica group 이 가진 세션 그룹 정책을 변경하면, 권한이 아니라 사용 중이라는 것으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 수정 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 수정 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.update: user-1 이 배포의 replica group 이 가진 세션 그룹의 방향을 퍼뜨리기로, 강제 수준을 선호로 변경합니다

Then

- 거부됩니다
  - 거부: SessionGroupInUseForUpdate

<a id="updating-an-owner-granted-only-read-may-not-update"></a>

#### [an-owner-granted-only-read-may-not-update](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 생성한 세션 그룹의 정책을 변경하면, 권한 부족으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.update: user-1 이 사용자가 생성한 세션 그룹의 방향을 퍼뜨리기로, 강제 수준을 선호로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### bulk_get_ids

<a id="bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group"></a>

#### [a-granted-user-bulk-reads-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹을 함께 읽으면, 요청한 순서대로 그 세션 그룹과 빈 값이 옵니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.bulk_get_ids: user-3 이 사용자가 생성한 세션 그룹, 배포의 replica group 이 가진 세션 그룹 순으로 여럿 읽기로 조회합니다

Then

- 첫 항목에 사용자가 생성한 세션 그룹 전체가 오고, 배포의 replica group 이 가진 세션 그룹 항목은 빈 값입니다
  - [0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0].entity_id: 사용자가 만든 세션 그룹의 id 와 같다
  - [0].domain_id: 그 도메인의 id 와 같다
  - [0].project_id: 그 프로젝트의 id 와 같다
  - [0].owner_user_id: 생성한 사용자의 id 와 같다
  - [0].placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - [0].placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - [0].created_at: 이 실행이 쓴 시각
  - [0].deleted_at = None

<a id="bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty"></a>

#### [the-superadmin-bulk-reads-a-missing-id-as-empty](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

superadmin 이 아무 세션 그룹도 갖지 않은 id 로 여럿 읽기로 조회하면, 그 항목이 빈 값으로 옵니다. 권한 검사를 통과하는 사람이어야 읽기의 응답을 볼 수 있어 요청한 사용자가 superadmin 입니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.bulk_get_ids: user-3 이 아무 세션 그룹도 갖지 않은 id 로 여럿 읽기로 조회합니다

Then

- 요청한 항목이 빈 값입니다
  - answers = ['NoneType']

<a id="bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-bulk-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

아무 권한도 받지 않은 사용자가 사용자가 생성한 세션 그룹을 id 로 여럿 읽기로 조회하면, 그 항목이 권한 부족으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.bulk_get_ids: user-3 이 사용자가 생성한 세션 그룹의 id 로 여럿 읽기로 조회합니다

Then

- 요청한 항목이 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="reading-a-granted-user-reads-a-users-session-group"></a>

#### [a-granted-user-reads-a-users-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 생성한 세션 그룹을 id 로 조회하면, 그 세션 그룹이 옵니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.get: user-3 이 사용자가 생성한 세션 그룹을 id 로 조회합니다

Then

- 사용자가 생성한 세션 그룹 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 사용자가 만든 세션 그룹의 id 와 같다
  - domain_id: 그 도메인의 id 와 같다
  - project_id: 그 프로젝트의 id 와 같다
  - owner_user_id: 생성한 사용자의 id 와 같다
  - placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - created_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="reading-a-deployments-session-group-is-not-found-even-when-granted"></a>

#### [a-deployments-session-group-is-not-found-even-when-granted](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 배포의 replica group 이 가진 세션 그룹을 id 로 조회하면, 권한이 아니라 대상이 없다는 것으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-group-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.get: user-3 이 배포의 replica group 이 가진 세션 그룹을 id 로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="reading-a-user-granted-nothing-may-not-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

아무 권한도 받지 않은 사용자가 사용자가 생성한 세션 그룹을 id 로 조회하면, 권한 부족으로 거부됩니다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 배포의 replica group 이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킵니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다

When

- SessionGroupAdapter.get: user-3 이 사용자가 생성한 세션 그룹을 id 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

