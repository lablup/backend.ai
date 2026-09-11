## vfolder

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Not exercised by any scenario: admin_search, batch_load_by_ids, batch_load_fields, bulk_delete, bulk_purge, clone, create_download_session, create_upload_session, delete, delete_files, deploy, get, get_folder_usage, list_files, mkdir, move_file, my_search, project_search, purge, restore.

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

