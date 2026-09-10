## vfolder

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Not exercised by any scenario: admin_search, batch_load_by_ids, batch_load_fields, bulk_delete, bulk_purge, clone, create_download_session, create_in_project, create_upload_session, delete, delete_files, deploy, get, get_folder_usage, list_files, mkdir, move_file, project_search, purge, restore.

### vfolder

#### [a-user-granted-folder-create-makes-one-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py) — pass

자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다

Given

- 폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 폴더를 만들 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 folder-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.create — user-1이 work이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 소유는 만든 사람에게 있다
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id = UserID('01a08a89-ca48-730a-9666-6eeb79b4a661')
  - ownership.project_id: 무시함 — 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - ownership.creator_id = UserID('01a08a89-ca48-730a-9666-6eeb79b4a661')
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함 — 데이터베이스가 만든다
  - status: 무시함 — 폴더가 만들어지는 동안 오가는 값이다
  - metadata.usage_mode: 무시함 — 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함 — 저장소가 정한다
  - access_control.permission: 무시함 — 만든 사람에게는 물어볼 것이 없다
  - quota: 무시함 — 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py) — pass

아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다

Given

- 폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.create — user-1이 denied이라는 폴더를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-who-has-made-no-folder-lists-none](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py) — pass

폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다

Given

- 폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 폴더를 만들 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 folder-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.my_search — user-1이 자기 폴더를 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

