## vfolder

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Not exercised by any scenario: batch_load_fields, bulk_purge, clone, create_download_session, create_upload_session, delete_files, deploy, get_folder_usage, list_files, mkdir, move_file, purge.

### admin_searching

#### [a-user-who-is-not-the-superadmin-may-not-search-everything](/tests/scenario/bai_scenario/manager/vfolder/test_admin_searching.py) — pass

자기 스코프에 읽기 권한을 받았더라도 슈퍼관리자가 아닌 사용자는 전체를 조회할 수 없다. 권한을 얼마나 받았는지와 무관하게 역할이 막는다

Given

- 폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.admin_search — user-1이 전체를 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-monitor-role-searches-across-every-owner-too](/tests/scenario/bai_scenario/manager/vfolder/test_admin_searching.py) — pass

모니터 역할은 슈퍼관리자가 아니지만 읽는 요청은 지나가므로, 전체 조회가 슈퍼관리자와 같은 답을 준다

Given

- 주인이 서로 다른 폴더 둘과, 아무 권한도 받지 않은 monitor 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 모니터 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 theirs-2: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.admin_search — user-3이 전체를 조회

Then

- 볼 수 있는 폴더 2개만 온다
  - items = ['theirs-1', 'theirs-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-searches-across-every-owner](/tests/scenario/bai_scenario/manager/vfolder/test_admin_searching.py) — pass

슈퍼관리자가 전체를 조회하면, 주인이 서로 다른 폴더가 모두 답으로 온다. 이 조회는 권한이 아니라 역할이 지킨다

Given

- 주인이 서로 다른 폴더 둘과, 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 theirs-2: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.admin_search — user-3이 전체를 조회

Then

- 볼 수 있는 폴더 2개만 온다
  - items = ['theirs-1', 'theirs-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-still-does-not-let-a-user-search-everything](/tests/scenario/bai_scenario/manager/vfolder/test_admin_searching.py) — pass

권한 집행을 꺼도 슈퍼관리자가 아니면 전체를 조회할 수 없다. 이 요청을 지키는 것이 권한이 아니라 역할이라 스위치와 무관하다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.admin_search — user-1이 전체를 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### batch_loading

#### [a-user-who-is-not-the-superadmin-may-not-pick-folders-by-ids](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py) — pass

슈퍼관리자가 아닌 사용자가 자기 폴더의 id를 주더라도, 이 조회는 권한이 아니라 역할이 지키므로 거부된다

Given

- 도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 가진 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.batch_load_by_ids — user-1이 자기 폴더 id로 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-empty-list-of-ids-is-answered-before-anything-is-checked](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py) — pass

아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 검사에 닿기 전에 빈 답으로 끝난다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.batch_load_by_ids — user-1이 빈 목록으로 조회

Then

- 답이 비어 있다
  - 답 = []

#### [picking-several-ids-keeps-the-order-and-leaves-a-gap](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py) — pass

슈퍼관리자가 서 있는 폴더들과 아무것도 갖지 않은 id를 섞어 주면, 준 순서 그대로 오고 없는 자리는 비어서 온다

Given

- 주인이 서로 다른 폴더 둘과, 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 theirs-2: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.batch_load_by_ids — user-3이 폴더 2개와 없는 id 하나를 함께 조회

Then

- 준 순서 그대로 오고, 없는 id 자리는 비어서 온다
  - 길이 = 3
  - 없는 id 자리 = None
  - 찾은 것 = ['theirs-1', 'theirs-2']

### bulk_retiring

#### [two-folders-of-ones-own-are-deleted-in-one-request](/tests/scenario/bai_scenario/manager/vfolder/test_bulk_retiring.py) — pass

지우기 권한을 받은 사용자가 자기 폴더 둘을 한 요청에 함께 지우면, 둘 다 지워지고 막힌 것은 하나도 없다

Given

- 도메인 스코프에 폴더 지우기 권한을 받은 사용자와, 그 사람이 가진 폴더 2개
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-2: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.bulk_delete — user-1이 폴더 2개를 함께 지움

Then

- 2개는 지워지고 0개는 막힌 것으로 담겨 온다
  - items = ['folder-1', 'folder-2']
  - deleted_count = 2
  - failed = 0
  - failed[].vfolder_id: 무시함 — 막힌 것이 없다
  - failed[].message: 무시함 — 예외 메시지를 그대로 담아 바뀌어도 되는 값이다

#### [what-the-caller-may-not-delete-comes-back-apart-from-what-they-did](/tests/scenario/bai_scenario/manager/vfolder/test_bulk_retiring.py) — pass

권한이 닿는 폴더와 닿지 않는 폴더를 한 요청에 함께 지우면, 닿는 것만 지워지고 나머지는 요청 전체를 깨뜨리지 않고 막힌 것으로 담겨 온다

Given

- 자기 도메인의 자기 폴더 하나와, 다른 도메인에 있는 남의 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다
  - 도메인 elsewhere-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.bulk_delete — user-1이 폴더 2개를 함께 지움

Then

- 1개는 지워지고 1개는 막힌 것으로 담겨 온다
  - items = ['folder-1']
  - deleted_count = 1
  - failed = 1
  - failed[].vfolder_id: 권한이 닿지 않는 폴더와 같다
  - failed[].message: 무시함 — 예외 메시지를 그대로 담아 바뀌어도 되는 값이다

### creating

#### [a-caller-who-spent-their-folder-allowance-may-not-make-another](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

자원 정책이 폴더 하나만 허락하는 사용자가 이미 하나를 가진 채 또 만들려 하면, 권한이 아니라 허락된 수를 다 썼다는 이유로 거부된다

Given

- 자기 스코프에 생성 권한을 받고 폴더를 하나 만들어 둔 사용자와 그 폴더
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 1개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.create — user-1이 one-too-many이라는 폴더를 만듦

Then

- 거부된다
  - 거부: VFolderInvalidParameter

#### [a-granted-user-makes-a-folder-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

자기 스코프에서 폴더를 만들 권한을 받은 사용자가 호스트를 골라 폴더를 만들면, 그 폴더의 주인과 만든 사람이 모두 그 사용자인 폴더 전체가 답으로 온다

Given

- 폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.create — user-1이 local:volume1에 work이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 주인은 만든 사람이다
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [a-name-a-purged-folder-left-behind-can-be-taken-again](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

저장소에서 완전히 사라진 폴더와 같은 이름으로 만들면, 그 이름은 이미 풀려 있으므로 그 이름을 쓴 새 폴더가 만들어진다

Given

- 자기 스코프에 생성 권한을 받은 사용자와, 저장소에서 완전히 사라진 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.create — user-1이 folder-1이라는 폴더를 만듦

Then

- 앞서 있던 폴더의 이름으로 새 폴더가 만들어진다
  - host = 'local:volume1'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [a-name-a-trashed-folder-still-holds-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

휴지통에 있는 폴더와 같은 이름으로 만들려 하면, 그 폴더가 아직 그 이름을 쥐고 있으므로 이름이 중복된다는 이유로 거부된다

Given

- 자기 스코프에 생성 권한을 받은 사용자와, 그 사람이 휴지통에 보낸 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 지워 휴지통에 있다

When

- VFolderAdapter.create — user-1이 folder-1이라는 폴더를 만듦

Then

- 거부된다
  - 거부: VFolderAlreadyExists

#### [a-name-the-caller-already-holds-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

권한을 받은 사용자가 자기가 이미 가진 폴더와 같은 이름으로 또 만들려 하면, 이름이 겹친다는 이유로 거부된다

Given

- 자기 스코프에 생성 권한을 받고 폴더를 하나 만들어 둔 사용자와 그 폴더
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.create — user-1이 folder-1이라는 폴더를 만듦

Then

- 거부된다
  - 거부: VFolderAlreadyExists

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

자기 스코프에 아무 권한도 받지 않은 사용자가 폴더를 만들려 하면, 그 스코프에 걸린 권한이 막아 거부된다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.create — user-1이 local:volume1에 denied이라는 폴더를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [leaving-everything-but-the-name-out-takes-the-defaults](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

권한을 받은 사용자가 이름만 주고 폴더를 만들면, 적지 않은 값은 기본값이 되고 폴더는 설정된 기본 호스트에 놓인다

Given

- 폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.create — user-1이 호스트를 대지 않고 plain이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 주인은 만든 사람이다
  - host = 'local:volume1'
  - metadata.name = 'plain'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [naming-a-project-in-the-request-makes-the-project-the-owner](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

그 프로젝트에 권한을 받은 사용자가 요청에 프로젝트를 함께 주고 폴더를 만들면, 그 프로젝트가 주인이고 개인 주인은 없는 폴더 전체가 답으로 온다

Given

- 프로젝트 하나와, 그 프로젝트에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1: 이 프로젝트의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.create — user-1이 team-1 아래 shared이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 주인은 프로젝트다
  - host = 'local:volume1'
  - metadata.name = 'shared'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'group'
  - ownership.user_id = None
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 만든 프로젝트와 같다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-user-with-no-grant-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py) — pass

권한 집행을 끄면 아무 권한도 받지 않은 사용자도 폴더를 만든다. 만들기를 지키는 것이 역할이 아니라 스코프에 걸린 권한이기 때문이다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.create — user-1이 local:volume1에 unguarded이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 주인은 만든 사람이다
  - host = 'local:volume1'
  - metadata.name = 'unguarded'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

### creating_in_project

#### [a-user-granted-nothing-on-the-project-may-not-make-a-folder-there](/tests/scenario/bai_scenario/manager/vfolder/test_creating_in_project.py) — pass

그 프로젝트에 아무 권한도 받지 않은 사용자가 프로젝트 아래 폴더를 만들려 하면, 그 프로젝트에 걸린 권한이 막아 거부된다

Given

- 프로젝트 하나와, 그 프로젝트에 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1: 이 프로젝트의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.create_in_project — user-1이 team-1 아래 denied이라는 폴더를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-on-the-project-makes-a-folder-the-project-owns](/tests/scenario/bai_scenario/manager/vfolder/test_creating_in_project.py) — pass

그 프로젝트에 권한을 받은 사용자가 프로젝트 아래 폴더를 만들면, 그 프로젝트가 주인인 폴더 전체가 답으로 온다

Given

- 프로젝트 하나와, 그 프로젝트에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1: 이 프로젝트의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.create_in_project — user-1이 team-1 아래 team이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 주인은 프로젝트다
  - host = 'local:volume1'
  - metadata.name = 'team'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'group'
  - ownership.user_id = None
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 만든 프로젝트와 같다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [naming-a-personal-project-is-stopped-by-the-storage-host-first](/tests/scenario/bai_scenario/manager/vfolder/test_creating_in_project.py) — pass

사용자를 만들 때 딸려 만들어진 개인 프로젝트를 대상으로 지목해 폴더를 만들려 하면, 그 프로젝트가 어떤 스토리지 호스트도 허용하지 않으므로 저장소 쪽이 먼저 막는다

Given

- 사용자를 만들 때 딸려 만들어진 개인 프로젝트와, 거기에 생성 권한을 받은 그 사용자
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 CREATE 허용
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.create_in_project — user-1이 자기 개인 프로젝트 아래 mine이라는 폴더를 만듦

Then

- 거부된다
  - 거부: InsufficientStoragePermission

### reading

#### [a-granted-owner-reads-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reading.py) — pass

자기 폴더를 읽을 권한을 받은 사용자가 그 폴더를 id로 읽으면, 만들어 둔 그대로의 폴더 전체가 답으로 온다

Given

- 도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 가진 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.get — user-1이 folder-1을 id로 조회

Then

- 심어둔 폴더 전체가 온다
  - host = 'local:volume1'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-may-not-read-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reading.py) — pass

남의 폴더에 아무 권한도 받지 않은 사용자가 그것을 읽으려 하면, 그 폴더에 걸린 권한이 막아 거부된다

Given

- 남이 가진 폴더 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 owner-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 owner-role-1: vfolder 전체에 CREATE 허용
  - 역할 owner-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 owner-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.get — user-2이 folder-1을 id로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-holds-is-refused-as-a-missing-permission](/tests/scenario/bai_scenario/manager/vfolder/test_reading.py) — pass

읽기 권한을 받은 사용자가 아무 폴더도 갖지 않은 id로 조회하면, 대상이 없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없다

Given

- 폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.get — user-1이 아무 폴더도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [only-the-superadmin-is-told-the-folder-is-not-there](/tests/scenario/bai_scenario/manager/vfolder/test_reading.py) — pass

슈퍼관리자가 아무 폴더도 갖지 않은 id로 조회하면, 권한 검사를 지나가므로 대상이 없다는 것으로 거부된다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.get — user-1이 아무 폴더도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: VFolderNotFound

#### [the-superadmin-reads-a-folder-they-were-granted-nothing-on](/tests/scenario/bai_scenario/manager/vfolder/test_reading.py) — pass

그 폴더에 아무 권한도 받지 않은 슈퍼관리자가 남이 만든 폴더를 읽으면, 역할이 권한 검사를 지나가 폴더 전체가 답으로 온다

Given

- 남이 가진 폴더 하나와, 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 owner-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 owner-role-1: vfolder 전체에 CREATE 허용
  - 역할 owner-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 owner-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.get — user-2이 folder-1을 id로 조회

Then

- 심어둔 폴더 전체가 온다
  - host = 'local:volume1'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 소유자와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 주인에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

### retiring

#### [a-grant-over-the-whole-domain-still-restores-only-ones-own](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

도메인 전체의 폴더에 지우기 권한을 받은 사용자라도 남이 휴지통에 보낸 폴더를 되살리려 하면, 권한이 아니라 자기 것이 아니라는 이유로 거부된다

Given

- 남이 휴지통에 보낸 폴더와, 도메인 스코프에 폴더 지우기 권한을 받은 다른 사용자
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 owner-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 owner-role-1: vfolder 전체에 CREATE 허용
  - 역할 owner-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 owner-role-1 보유
  - 폴더 folder-1: 소유자가 지워 휴지통에 있다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-2: 역할 folder-role-1 보유

When

- VFolderAdapter.restore — user-2이 folder-1을 되살림

Then

- 거부된다
  - 거부: VFolderNotFound

#### [a-granted-owner-sends-their-folder-to-the-trash](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

자기 폴더를 지울 권한을 받고 키페어 정책도 그 호스트를 허락한 사용자가 폴더를 지우면, 지운 폴더를 가리키는 답이 온다

Given

- 도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 가진 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.delete — user-1이 folder-1을 지움

Then

- 답이 그 폴더를 가리킨다
  - id: 심어둔 폴더와 같다

#### [a-keypair-policy-that-closes-the-host-stops-the-delete](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

폴더를 지울 권한은 받았지만 키페어 정책이 그 호스트에서 지우기를 막아둔 사용자가 지우려 하면, 권한이 아니라 저장소 쪽이 막아 거부된다

Given

- 도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 가진 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다, 그 호스트에서 할 수 있는 것은 create-vfolder, download-file, invite-others, modify-vfolder, mount-in-session, set-user-specific-permission, upload-file뿐이다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.delete — user-1이 folder-1을 지움

Then

- 거부된다
  - 거부: InsufficientStoragePermission

#### [a-user-granted-nothing-may-not-delete-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

남의 폴더에 아무 권한도 받지 않은 사용자가 그것을 지우려 하면, 그 폴더에 걸린 권한이 막아 거부된다

Given

- 남이 가진 폴더 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 owner-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 owner-role-1: vfolder 전체에 CREATE 허용
  - 역할 owner-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 owner-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.delete — user-2이 folder-1을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-restore-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

남이 휴지통에 보낸 폴더에 아무 권한도 받지 않은 사용자가 되살리려 하면, 그 폴더에 걸린 권한이 막아 거부된다

Given

- 남이 가진 폴더 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 owner-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 owner-role-1: vfolder 전체에 CREATE 허용
  - 역할 owner-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 owner-role-1 보유
  - 폴더 folder-1: 소유자가 지워 휴지통에 있다

When

- VFolderAdapter.restore — user-2이 folder-1을 되살림

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [whoever-sent-a-folder-to-the-trash-brings-it-back](/tests/scenario/bai_scenario/manager/vfolder/test_retiring.py) — pass

자기 폴더를 지워 휴지통에 둔 사용자가 같은 권한으로 되살리면, 되살린 폴더를 가리키는 답이 온다

Given

- 도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 지워 휴지통에 둔 폴더
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 역할 folder-role-1: vfolder 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 지워 휴지통에 있다

When

- VFolderAdapter.restore — user-1이 folder-1을 되살림

Then

- 답이 그 폴더를 가리킨다
  - id: 심어둔 폴더와 같다

### scoped_searching

#### [a-user-granted-nothing-on-the-project-may-not-search-it](/tests/scenario/bai_scenario/manager/vfolder/test_scoped_searching.py) — pass

그 프로젝트에 아무 권한도 받지 않은 사용자가 프로젝트 폴더를 조회하려 하면, 그 프로젝트에 걸린 권한이 막아 거부된다

Given

- 프로젝트 하나와, 그 프로젝트에 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1: 이 프로젝트의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.project_search — user-1이 team-1의 폴더를 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [searching-a-project-answers-only-what-that-project-owns](/tests/scenario/bai_scenario/manager/vfolder/test_scoped_searching.py) — pass

그 프로젝트에 읽기 권한을 받은 사용자가 프로젝트 폴더를 조회하면, 같은 도메인에 있는 남의 개인 폴더는 빼고 그 프로젝트 것만 온다

Given

- 프로젝트 폴더 하나와 남의 개인 폴더 하나, 그리고 그 프로젝트에 읽기 권한을 받은 사용자
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1: 이 프로젝트의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 프로젝트 폴더 project-folder-1: 프로젝트가 소유하고, 개인 소유자는 없다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.project_search — user-1이 team-1의 폴더를 조회

Then

- 볼 수 있는 폴더 1개만 온다
  - items = ['project-folder-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

### searching

#### [a-user-granted-nothing-may-not-search-even-their-own-folders](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py) — pass

자기 스코프에 아무 권한도 받지 않은 사용자가 자기 폴더를 조회하려 하면, 범위를 좁히는 것으로 끝나지 않고 그 스코프에 걸린 권한이 막아 거부된다

Given

- 폴더를 받아줄 도메인과, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.my_search — user-1이 자기 폴더를 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-who-has-made-no-folder-finds-none](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py) — pass

폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다

Given

- 폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유

When

- VFolderAdapter.my_search — user-1이 자기 폴더를 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [leaving-the-page-size-out-answers-one-default-page](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py) — pass

폴더를 열한 개 가진 사용자가 페이지 크기를 대지 않고 조회하면, 기본 크기만큼만 오고 다음 페이지가 있다고 답한다

Given

- 자기 폴더 11개와 남의 폴더 0개, 그리고 그 폴더들의 주인
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 11개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-2: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-3: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-4: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-5: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-6: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-7: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-8: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-9: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-10: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-11: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.my_search — user-1이 자기 폴더를 조회

Then

- 10건까지 오고, 다음 페이지가 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [searching-my-own-folders-answers-only-mine](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py) — pass

자기 스코프에 읽기 권한을 받은 사용자가 자기 폴더를 조회하면, 같은 도메인에 있는 남의 폴더는 빼고 자기 것만 온다

Given

- 자기 폴더 2개와 남의 폴더 1개, 그리고 그 폴더들의 주인
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 folder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 folder-role-1: vfolder 전체에 READ 허용
  - 일반 사용자 user-1: 역할 folder-role-1 보유
  - 폴더 folder-1: 소유자가 이미 만들어 둔 것이다
  - 폴더 folder-2: 소유자가 이미 만들어 둔 것이다
  - 폴더 theirs-1: 소유자가 이미 만들어 둔 것이다

When

- VFolderAdapter.my_search — user-1이 자기 폴더를 조회

Then

- 볼 수 있는 폴더 2개만 온다
  - items = ['folder-1', 'folder-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

