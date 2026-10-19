## session_group

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session_group/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session_group/adapter.py)

시나리오: 완성

- ops 로 구성 (3)
  - global_search — 대표 성공 ✓ · 대표 실패 ✓
  - purge — 대표 성공 ✓ · 대표 실패 ✓
  - scoped_search — 대표 성공 ✓ · 대표 실패 ✓
- 직접 구현 (2)
  - bulk_get_ids — 성공 있음 2 · 실패 있음 1 (partial_bulk)
  - get — 성공 있음 1 · 실패 있음 2 (single_entity)

**global_search**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 슈퍼관리자가 한 프로젝트로 걸러 전체 검색하면, 그 프로젝트의 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹이 모두 온다. 이 문은 역할이라 행위자가 슈퍼관리자다](#searching-the-superadmin-finds-a-users-group-and-a-deployments-group) | 성공 |
| [그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 슈퍼관리자가 아닌 사용자가 전체 검색하면, 역할로 거부된다](#searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 자기가 만든 세션 그룹을 지우면, 그 세션 그룹의 id가 오고 멤버 세션은 세션 그룹이 비워진 채 남는다](#purging-the-owner-purges-a-users-session-group-keeping-its-members) | 성공 |
| [자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 replica group이 가진 세션 그룹을 지우면, 권한이 아니라 대상이 없다는 것으로 거부되고 세션 그룹은 남는다](#purging-a-deployments-session-group-is-not-found-for-a-purge) | 거부 |
| [아무 권한도 받지 않은 사용자가 자기가 만든 세션 그룹을 지우면, 권한 부족으로 거부되고 세션 그룹은 남는다](#purging-a-user-granted-nothing-may-not-purge-a-session-group) | 거부 |
| [자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 만든 세션 그룹을 지우면, 권한 부족으로 거부되고 세션 그룹은 남는다](#purging-a-user-granted-only-read-may-not-purge-a-session-group) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그 프로젝트 범위로 검색하면, replica group이 가진 세션 그룹과 다른 프로젝트의 세션 그룹은 빠지고 그 프로젝트의 사용자가 만든 세션 그룹만 온다](#scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project) | 성공 |
| [자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 두 스코프를 함께 넘겨 검색하면, 자기가 만든 세션 그룹과 그 프로젝트에서 다른 사용자가 만든 세션 그룹이 합쳐져 오고 replica group이 가진 세션 그룹은 빠진다](#scoped_searching-a-user-scope-and-a-project-scope-are-joined) | 성공 |
| [자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자가 자기 스코프로 검색하면, 두 프로젝트에 자기가 만든 세션 그룹이 오고 replica group이 가진 세션 그룹과 다른 사용자가 만든 세션 그룹은 빠진다](#scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope) | 성공 |
| [다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들이 있는 프로젝트 범위로 검색하면, 권한 부족으로 거부된다](#scoped_searching-searching-a-project-not-granted-is-refused) | 거부 |
| [세션 그룹들이 있는 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들을 만든 사용자의 스코프로 검색하면, 권한 부족으로 거부된다](#scoped_searching-searching-another-users-scope-is-refused) | 거부 |

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹을 함께 읽으면, 요청한 순서대로 그 세션 그룹과 빈 값이 온다](#bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group) | 성공 |
| [슈퍼관리자가 아무 세션 그룹도 갖지 않은 id로 여럿 읽으면, 그 자리가 빈 값으로 온다. 권한 검사를 통과하는 사람이어야 읽기의 답을 볼 수 있어 행위자가 슈퍼관리자다](#bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자가 만든 세션 그룹을 id로 여럿 읽으면, 그 자리가 권한 부족으로 거부된다](#bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 세션 그룹을 id로 조회하면, 그 세션 그룹이 온다](#reading-a-granted-user-reads-a-users-session-group) | 성공 |
| [그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 replica group이 가진 세션 그룹을 id로 조회하면, 권한이 아니라 대상이 없다는 것으로 거부된다](#reading-a-deployments-session-group-is-not-found-even-when-granted) | 거부 |
| [아무 권한도 받지 않은 사용자가 사용자가 만든 세션 그룹을 id로 조회하면, 권한 부족으로 거부된다](#reading-a-user-granted-nothing-may-not-read-a-session-group) | 거부 |

### global_search

<a id="searching-the-superadmin-finds-a-users-group-and-a-deployments-group"></a>

#### [the-superadmin-finds-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py) — pass

아무 권한도 받지 않은 슈퍼관리자가 한 프로젝트로 걸러 전체 검색하면, 그 프로젝트의 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹이 모두 온다. 이 문은 역할이라 행위자가 슈퍼관리자다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.global_search — user-3이 team-1 프로젝트로 걸러 전체 검색

Then

- 그 프로젝트의 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹이 모두 온다
  - items: 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group"></a>

#### [a-user-who-is-not-a-superadmin-may-not-search-every-session-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py) — pass

그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 슈퍼관리자가 아닌 사용자가 전체 검색하면, 역할로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.global_search — user-3이 team-1 프로젝트로 걸러 전체 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

### purge

<a id="purging-the-owner-purges-a-users-session-group-keeping-its-members"></a>

#### [the-owner-purges-a-users-session-group-keeping-its-members](/tests/scenario/bai_scenario/manager/session_group/test_purging.py) — pass

자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 자기가 만든 세션 그룹을 지우면, 그 세션 그룹의 id가 오고 멤버 세션은 세션 그룹이 비워진 채 남는다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프에서 세션 그룹 권한 하나를 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-owner-1: session_group 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.purge — user-1이 사용자가 만든 세션 그룹을 영구 삭제

Then

- 지운 사용자가 만든 세션 그룹의 id가 온다
  - id: 사용자가 만든 세션 그룹의 id와 같다

<a id="purging-a-deployments-session-group-is-not-found-for-a-purge"></a>

#### [a-deployments-session-group-is-not-found-for-a-purge](/tests/scenario/bai_scenario/manager/session_group/test_purging.py) — pass

자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 replica group이 가진 세션 그룹을 지우면, 권한이 아니라 대상이 없다는 것으로 거부되고 세션 그룹은 남는다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프에서 세션 그룹 권한 하나를 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-owner-1: session_group 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.purge — user-1이 replica group이 가진 세션 그룹을 영구 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

<a id="purging-a-user-granted-nothing-may-not-purge-a-session-group"></a>

#### [a-user-granted-nothing-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 자기가 만든 세션 그룹을 지우면, 권한 부족으로 거부되고 세션 그룹은 남는다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 그리고 아무 권한도 받지 않은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.purge — user-1이 사용자가 만든 세션 그룹을 영구 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="purging-a-user-granted-only-read-may-not-purge-a-session-group"></a>

#### [a-user-granted-only-read-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py) — pass

자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 만든 세션 그룹을 지우면, 권한 부족으로 거부되고 세션 그룹은 남는다

Given

- 한 프로젝트에 멤버 세션 둘을 가진 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 그리고 자기 스코프에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프에서 세션 그룹 권한 하나를 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 세션 session-1: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 세션 session-2: 세션 그룹의 멤버로 스케줄링을 기다리고 있다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.purge — user-1이 사용자가 만든 세션 그룹을 영구 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project"></a>

#### [a-granted-user-finds-only-the-users-group-of-the-project](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py) — pass

그 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그 프로젝트 범위로 검색하면, replica group이 가진 세션 그룹과 다른 프로젝트의 세션 그룹은 빠지고 그 프로젝트의 사용자가 만든 세션 그룹만 온다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search — user-3이 team-1 프로젝트 범위에서 조회

Then

- 그 프로젝트의 사용자가 만든 세션 그룹만 남는다
  - items: 그 프로젝트의 사용자가 만든 세션 그룹
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-scope-and-a-project-scope-are-joined"></a>

#### [a-user-scope-and-a-project-scope-are-joined](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py) — pass

자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 두 스코프를 함께 넘겨 검색하면, 자기가 만든 세션 그룹과 그 프로젝트에서 다른 사용자가 만든 세션 그룹이 합쳐져 오고 replica group이 가진 세션 그룹은 빠진다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프와 한 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-reader-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.scoped_search — user-1이 자기 스코프와 other-1 프로젝트 범위를 함께 조회

Then

- 그 사용자가 만든 세션 그룹과 다른 프로젝트의 세션 그룹이 합쳐져 남는다
  - items: 그 사용자가 만든 세션 그룹과 다른 프로젝트의 세션 그룹
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope"></a>

#### [an-owner-finds-the-groups-they-made-in-their-own-scope](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py) — pass

자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자가 자기 스코프로 검색하면, 두 프로젝트에 자기가 만든 세션 그룹이 오고 replica group이 가진 세션 그룹과 다른 사용자가 만든 세션 그룹은 빠진다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 자기 스코프에서 세션 그룹 읽기 권한을 받은 세션 그룹들을 만든 사용자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-owner-1: session_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 session-group-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.scoped_search — user-1이 자기 스코프에서 조회

Then

- 그 사용자가 두 프로젝트에 만든 세션 그룹만 남는다
  - items: 그 사용자가 두 프로젝트에 만든 세션 그룹
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-searching-a-project-not-granted-is-refused"></a>

#### [searching-a-project-not-granted-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py) — pass

다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들이 있는 프로젝트 범위로 검색하면, 권한 부족으로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search — user-3이 team-1 프로젝트 범위에서 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="scoped_searching-searching-another-users-scope-is-refused"></a>

#### [searching-another-users-scope-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py) — pass

세션 그룹들이 있는 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 세션 그룹들을 만든 사용자의 스코프로 검색하면, 권한 부족으로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.scoped_search — user-3이 user-1의 스코프에서 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

### bulk_get_ids

<a id="bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group"></a>

#### [a-granted-user-bulk-reads-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py) — pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹을 함께 읽으면, 요청한 순서대로 그 세션 그룹과 빈 값이 온다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.bulk_get_ids — user-3이 사용자가 만든 세션 그룹, replica group이 가진 세션 그룹 순으로 여럿 읽기

Then

- 첫 자리에 사용자가 만든 세션 그룹 전체가 오고, replica group이 가진 세션 그룹 자리는 빈 값이다
  - [0].id: 무시함 — 데이터베이스가 만든다
  - [0].entity_id: 사용자가 만든 세션 그룹의 id와 같다
  - [0].domain_id: 그 도메인의 id와 같다
  - [0].project_id: 그 프로젝트의 id와 같다
  - [0].owner_user_id: 만든 사람의 id와 같다
  - [0].placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - [0].placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - [0].created_at: 이 실행이 쓴 시각
  - [0].deleted_at = None

<a id="bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty"></a>

#### [the-superadmin-bulk-reads-a-missing-id-as-empty](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py) — pass

슈퍼관리자가 아무 세션 그룹도 갖지 않은 id로 여럿 읽으면, 그 자리가 빈 값으로 온다. 권한 검사를 통과하는 사람이어야 읽기의 답을 볼 수 있어 행위자가 슈퍼관리자다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.bulk_get_ids — user-3이 아무 세션 그룹도 갖지 않은 id로 여럿 읽기

Then

- 물은 자리가 빈 값이다
  - answers = ['NoneType']

<a id="bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-bulk-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py) — pass

아무 권한도 받지 않은 사용자가 사용자가 만든 세션 그룹을 id로 여럿 읽으면, 그 자리가 권한 부족으로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.bulk_get_ids — user-3이 사용자가 만든 세션 그룹의 id로 여럿 읽기

Then

- 물은 자리가 거부된다
  - 거부: NotEnoughPermission

### get

<a id="reading-a-granted-user-reads-a-users-session-group"></a>

#### [a-granted-user-reads-a-users-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py) — pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 세션 그룹을 id로 조회하면, 그 세션 그룹이 온다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.get — user-3이 사용자가 만든 세션 그룹을 id로 조회

Then

- 사용자가 만든 세션 그룹 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - entity_id: 사용자가 만든 세션 그룹의 id와 같다
  - domain_id: 그 도메인의 id와 같다
  - project_id: 그 프로젝트의 id와 같다
  - owner_user_id: 만든 사람의 id와 같다
  - placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - created_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="reading-a-deployments-session-group-is-not-found-even-when-granted"></a>

#### [a-deployments-session-group-is-not-found-even-when-granted](/tests/scenario/bai_scenario/manager/session_group/test_reading.py) — pass

그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 replica group이 가진 세션 그룹을 id로 조회하면, 권한이 아니라 대상이 없다는 것으로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 세션 그룹들이 있는 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다
  - 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-group-reader-1: session_group 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-group-reader-1 보유

When

- SessionGroupAdapter.get — user-3이 replica group이 가진 세션 그룹을 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

<a id="reading-a-user-granted-nothing-may-not-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 사용자가 만든 세션 그룹을 id로 조회하면, 권한 부족으로 거부된다

Given

- 한 프로젝트에 사용자가 만든 세션 그룹과 replica group이 가진 세션 그룹, 다른 프로젝트에 같은 사용자가 만든 세션 그룹과 다른 사용자가 만든 세션 그룹, 그리고 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자가 만든 세션 그룹 session-group-1: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-2: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 사용자가 만든 세션 그룹 session-group-3: 멤버를 한 에이전트에 모으고, 반드시 지킨다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 replica group과 함께 만드는 세션 그룹이다
  - 배포 deployment-1: 세션 그룹을 가진 replica group 하나를 갖는다

When

- SessionGroupAdapter.get — user-3이 사용자가 만든 세션 그룹을 id로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

