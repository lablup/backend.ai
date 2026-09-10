## vfolder

Not exercised by any scenario: admin_search, batch_load_by_ids, batch_load_fields, bulk_delete, bulk_purge, clone, create_download_session, create_in_project, create_upload_session, delete, delete_files, deploy, get, get_folder_usage, list_files, mkdir, move_file, project_search, purge, restore.

### vfolder

#### a-user-granted-folder-create-makes-one-of-their-own — pass

자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다

Given

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

- 일반 사용자 user-1의 create 호출
  - CreateVFolderInput(name='work')

Then

- vfolder.access_control.ownership_type = 'user'

#### a-user-granted-nothing-may-not-make-a-folder — pass

아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- 일반 사용자 user-1의 create 호출
  - CreateVFolderInput(name='denied')

Then

- 거부: NotEnoughPermission

#### a-user-who-has-made-no-folder-lists-none — pass

폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다

Given

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

- 일반 사용자 user-1의 my_search 호출
  - SearchVFoldersInput()

Then

- 답 전체 일치

