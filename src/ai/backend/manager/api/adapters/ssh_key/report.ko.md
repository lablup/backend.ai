## ssh_key

[어댑터](/src/ai/backend/manager/api/adapters/ssh_key/adapter.py)

시나리오: 완성

- 직접 구현 (2)
  - my_upload: 성공 있음 2 · 거부 있음 2 (single_entity)
  - switch_default: 성공 있음 1 · 거부 있음 1 (single_field)

**my_upload**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 UPDATE 권한을 받고 SSH 키가 없는 사용자가 키를 업로드하면, 그 키가 default 로 지정되어 응답으로 옵니다](#uploading-a-user-granted-update-uploads-their-first-key-as-the-default) | 성공 |
| [자기 사용자에 UPDATE 권한을 받고 default SSH 키를 이미 가진 사용자가 키를 업로드하면, 그 키는 default 가 아닌 키로 응답이 옵니다](#uploading-a-user-holding-a-default-uploads-a-key-that-is-not-the-default) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 SSH 키를 업로드하려 하면 권한 부족으로 거부됩니다](#uploading-a-user-granted-read-may-not-upload-a-key) | 거부 |
| [자기 사용자에 UPDATE 권한을 받은 사용자라도 공개키 형식이 아닌 값을 업로드하면 거부됩니다](#uploading-a-value-that-is-not-a-public-key-is-rejected) | 거부 |

**switch_default**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 SSH 키를 default 로 지정하면, default 가 된 그 키가 응답으로 옵니다](#switching_default-a-user-granted-update-switches-their-default-key) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 자기 SSH 키를 default 로 지정하려 하면 권한 부족으로 거부됩니다](#switching_default-a-user-granted-read-may-not-switch-their-default-key) | 거부 |

### my_upload

<a id="uploading-a-user-granted-update-uploads-their-first-key-as-the-default"></a>

#### [a-user-granted-update-uploads-their-first-key-as-the-default](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

자기 사용자에 UPDATE 권한을 받고 SSH 키가 없는 사용자가 키를 업로드하면, 그 키가 default 로 지정되어 응답으로 옵니다

Given

- 도메인 하나와 SSH 키가 없는 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.my_upload: user-1이 자기 SSH 키를 업로드합니다

Then

- SSH 키 전체가 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 만듭니다
  - user_id: 호출한 사용자와 같다
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - is_default = True

<a id="uploading-a-user-holding-a-default-uploads-a-key-that-is-not-the-default"></a>

#### [a-user-holding-a-default-uploads-a-key-that-is-not-the-default](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

자기 사용자에 UPDATE 권한을 받고 default SSH 키를 이미 가진 사용자가 키를 업로드하면, 그 키는 default 가 아닌 키로 응답이 옵니다

Given

- 도메인 하나와 default SSH 키 하나와 default 아닌 SSH 키 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: default SSH 키 하나를 갖습니다
  - 일반 사용자 user-1: default 가 아닌 SSH 키 하나를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.my_upload: user-1이 자기 SSH 키를 업로드합니다

Then

- SSH 키 전체가 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 만듭니다
  - user_id: 호출한 사용자와 같다
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICuqqTj6Ee2CFRyYHeq1INgqKdEoYvyazZPR69RTWOJI'
  - is_default = False

<a id="uploading-a-user-granted-read-may-not-upload-a-key"></a>

#### [a-user-granted-read-may-not-upload-a-key](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

자기 사용자에 READ 권한만 받은 사용자가 SSH 키를 업로드하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 SSH 키가 없는 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.my_upload: user-1이 자기 SSH 키를 업로드합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="uploading-a-value-that-is-not-a-public-key-is-rejected"></a>

#### [a-value-that-is-not-a-public-key-is-rejected](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

자기 사용자에 UPDATE 권한을 받은 사용자라도 공개키 형식이 아닌 값을 업로드하면 거부됩니다

Given

- 도메인 하나와 SSH 키가 없는 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.my_upload: user-1이 공개키 형식이 아닌 값을 자기 SSH 키로 업로드합니다

Then

- 거부됩니다
  - 거부: InvalidSSHPublicKey

### switch_default

<a id="switching_default-a-user-granted-update-switches-their-default-key"></a>

#### [a-user-granted-update-switches-their-default-key](/tests/scenario/bai_scenario/manager/ssh_key/test_switching_default.py): pass

자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 SSH 키를 default 로 지정하면, default 가 된 그 키가 응답으로 옵니다

Given

- 도메인 하나와 default SSH 키 하나와 default 아닌 SSH 키 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: default SSH 키 하나를 갖습니다
  - 일반 사용자 user-1: default 가 아닌 SSH 키 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.switch_default: user-1이 default 가 아닌 자기 SSH 키를 default 로 지정합니다

Then

- SSH 키 전체가 응답으로 옵니다
  - id: 심어 둔 그 SSH 키와 같다
  - user_id: 호출한 사용자와 같다
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFYD/Yrss1np0I+R9f51bEJ0Jjs+d0s4JUussQhs0WBG'
  - is_default = True

<a id="switching_default-a-user-granted-read-may-not-switch-their-default-key"></a>

#### [a-user-granted-read-may-not-switch-their-default-key](/tests/scenario/bai_scenario/manager/ssh_key/test_switching_default.py): pass

자기 사용자에 READ 권한만 받은 사용자가 자기 SSH 키를 default 로 지정하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default SSH 키 하나와 default 아닌 SSH 키 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: default SSH 키 하나를 갖습니다
  - 일반 사용자 user-1: default 가 아닌 SSH 키 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- SSHKeyAdapter.switch_default: user-1이 default 가 아닌 자기 SSH 키를 default 로 지정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

