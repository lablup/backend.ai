## image

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/image/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/image/adapter.py)

Not exercised by any scenario: batch_load_fields.

### aliasing

#### [a-user-who-is-not-the-superadmin-may-not-dealias](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 아닌 사용자가 별칭을 떼려 하면 역할로 막힌다

Given

- 별칭이 붙은 이미지 하나, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_dealias — user-1이 별칭 seeded-alias를 뗌

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [aliasing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

아무 이미지도 갖지 않은 id에 별칭을 붙이려 하면 이미지가 없다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_alias — user-1이 아무것도 갖지 않은 id에 별칭을 붙임

Then

- 거부된다
  - 거부: ImageNotFound

#### [aliasing-an-image-answers-with-the-alias-and-the-image-it-names](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 이미지에 별칭을 붙이면 그 별칭과 가리키는 이미지가 답으로 온다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_alias — user-1이 image-1에 별칭 made-alias를 붙임

Then

- 붙인 별칭과 그 이미지의 id가 온다
  - alias = 'made-alias'
  - image_id: 심은 이미지의 id와 같다
  - alias_id: 무시함 — 데이터베이스가 만든다

#### [an-alias-another-image-already-holds-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

이미 쓰이고 있는 별칭을 붙이려 하면 별칭이 겹친다는 이유로 거부된다

Given

- 별칭이 붙은 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_alias — user-1이 이미 쓰이는 별칭 seeded-alias를 붙임

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [dealiasing-a-name-no-image-holds-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

아무 이미지도 갖지 않은 별칭을 떼려 하면 별칭이 없다는 이유로 거부된다

Given

- 별칭이 붙은 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_dealias — user-1이 아무 이미지도 갖지 않은 별칭을 뗌

Then

- 거부된다
  - 거부: ImageAliasNotFound

#### [dealiasing-answers-with-the-alias-it-removed](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 붙은 별칭을 떼면 떼어낸 별칭과 그 이미지가 답으로 온다

Given

- 별칭이 붙은 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_dealias — user-1이 별칭 seeded-alias를 뗌

Then

- 떼어낸 별칭과 그 이미지의 id가 온다
  - alias = 'seeded-alias'
  - image_id: 심은 이미지의 id와 같다
  - alias_id: 무시함 — 데이터베이스가 만든다

#### [the-maker-of-a-custom-image-still-may-not-alias-it](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

자기가 만든 커스텀 이미지라도 별칭은 붙일 수 없다. 별칭을 붙이는 문은 그 이미지의 권한이 아니라 역할이 지키기 때문이다

Given

- 부르는 사람이 만든 커스텀 이미지 하나, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 것이라 주인이 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_alias — user-1이 image-1에 별칭 made-alias를 붙임

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-who-is-not-the-superadmin-may-not-edit-an-image](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 이미지를 고치려 하면 역할로 막힌다

Given

- 레지스트리 하나와 그 안의 이미지 하나, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 태그를 moved로 고침

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 아무 값도 주지 않고 고침

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [changing-only-the-tag-leaves-every-other-field-alone](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 태그만 고치면 태그만 새 값이 되고 나머지 자리는 그대로다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 태그를 moved로 고침

Then

- 태그만 새 값이고 나머지는 그대로다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'moved'
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - is_local = False
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [clearing-the-accelerator-list-empties-it](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 가속기 목록을 비우는 수정을 하면 그 자리가 빈 채로 온다. 생략과 비우기를 따로 말할 수 있는 항목은 이것뿐이다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 가속기 목록을 비움

Then

- 가속기 자리가 비어 있다
  - name = 'image-1'
  - accelerators = None
  - tag = 'latest'
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [editing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

아무 이미지도 갖지 않은 id를 고치려 하면 이미지가 없다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 아무것도 갖지 않은 id를 고침

Then

- 거부된다
  - 거부: ImageNotFound

### forgetting

#### [a-granted-user-may-not-forget-an-image-nobody-owns](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

커스터마이즈되지 않은 이미지는 주인이 없으므로, 그 이미지에 권한을 받은 사용자라도 게이트를 지난 뒤 소유권 검사에서 막힌다

Given

- 주인 없는 이미지 하나, 그 이미지에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

#### [a-user-granted-nothing-may-not-forget-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 권한도 받지 않은 사용자가 이미지를 잊으려 하면 권한 부족으로 막힌다

Given

- 주인 없는 이미지 하나, 아무 권한도 없음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-restore-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 권한도 받지 않은 사용자가 잊힌 이미지를 되살리려 하면 권한 부족으로 막힌다

Given

- 주인 없는 이미지 하나, 아무 권한도 없음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1을 되살림

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-image-a-purge-is-working-through-cannot-be-reached](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

지우는 중인 이미지를 잊으려 하면 이미지가 없다는 이유로 거부된다. 그 상태의 이미지는 id로 집는 자리에서 보이지 않는다

Given

- 레지스트리 하나와 그 안의 이미지 하나, 상태는 PURGING, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지, 상태는 PURGING
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 거부된다
  - 거부: ImageNotFound

#### [forgetting-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 이미지도 갖지 않은 id를 잊으려 하면 이미지가 없다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 아무것도 갖지 않은 id를 잊음

Then

- 거부된다
  - 거부: ImageNotFound

#### [forgetting-an-image-marks-it-deleted-and-keeps-the-row](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

슈퍼관리자가 이미지를 잊으면, 행은 남고 지워졌다는 상태를 실은 노드가 온다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.DELETED: 'DELETED'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [restoring-a-forgotten-image-cannot-reach-it](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

잊힌 이미지를 되살리려 하면 이미지가 없다는 이유로 거부된다. 이미지를 id로 집는 자리가 살아 있는 것만 보기 때문이다

Given

- 레지스트리 하나와 그 안의 이미지 하나, 상태는 DELETED, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지, 상태는 DELETED
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1을 되살림

Then

- 거부된다
  - 거부: ImageNotFound

#### [restoring-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 이미지도 갖지 않은 id를 되살리려 하면 이미지가 없다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 아무것도 갖지 않은 id를 되살림

Then

- 거부된다
  - 거부: ImageNotFound

#### [restoring-an-image-that-was-never-forgotten-leaves-it-alive](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

살아 있는 이미지를 되살려도 살아 있는 그대로다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1을 되살림

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [the-maker-of-a-custom-image-may-forget-it](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 잊으면, 게이트와 소유권 검사를 모두 지나 지워졌다는 상태가 온다

Given

- 부르는 사람이 만든 커스텀 이미지 하나, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 것이라 주인이 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.DELETED: 'DELETED'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [turning-enforcement-off-still-does-not-let-anyone-forget-an-unowned-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

엔티티 권한 집행을 꺼서 게이트를 열어도 주인 없는 이미지는 잊을 수 없다. 소유권 검사는 그 스위치가 닿지 않는 자리에서 돌기 때문이다

Given

- 주인 없는 이미지 하나, 아무 권한도 없음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1을 잊음

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

### reading

#### [a-plain-user-loading-many-alias-ids-is-refused-as-a-whole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 아닌 사용자가 별칭 id 여럿을 한 번에 읽으려 하면 역할로 막힌다

Given

- 별칭이 붙은 이미지 하나, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_aliases_by_ids — user-1이 심은 별칭 하나와 없는 id 하나를 한 번에 읽음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-plain-user-loading-many-image-ids-is-refused-as-a-whole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 아닌 사용자가 id 여럿을 한 번에 읽으려 하면, 원소별로 갈리지 않고 요청 전체가 역할로 막힌다

Given

- 레지스트리 하나와 그 안의 이미지 2개, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_by_ids — user-1이 심은 것 둘과 없는 id 하나를 한 번에 읽음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-empty-image-id-list-answers-empty-without-calling-the-wiring](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

빈 id 목록으로 읽으면 배선을 부르지 않고 빈 답이 온다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 읽음

Then

- 빈 답이 온다
  - items = []

#### [loading-many-alias-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 심은 별칭 하나와 아무것도 갖지 않은 id 하나를 한 번에 읽으면, 준 순서 그대로 오고 없는 id 자리만 비어서 온다

Given

- 별칭이 붙은 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_aliases_by_ids — user-1이 심은 별칭 하나와 없는 id 하나를 한 번에 읽음

Then

- 준 순서 그대로 오고 없는 id 자리는 비어 있다
  - length = 2
  - aliases = ['seeded-alias', None]

#### [loading-many-image-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 심은 이미지 둘과 아무것도 갖지 않은 id 하나를 한 번에 읽으면, 준 순서 그대로 오고 없는 id 자리만 비어서 온다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_by_ids — user-1이 심은 것 둘과 없는 id 하나를 한 번에 읽음

Then

- 준 순서 그대로 오고 없는 id 자리는 비어 있다
  - length = 3
  - names = ['image-0-1', None, 'image-1-1']

### retiring

#### [a-granted-user-may-not-purge-an-image-nobody-owns](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

주인 없는 이미지는 그 이미지에 권한을 받은 사용자라도 지울 수 없다. 게이트를 지난 뒤 소유권 검사가 막는다

Given

- 주인 없는 이미지 하나, 그 이미지에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_purge — user-1이 image-1을 지움

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

#### [a-user-granted-nothing-may-not-purge-an-image](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 이미지를 지우려 하면 권한 부족으로 막힌다

Given

- 주인 없는 이미지 하나, 아무 권한도 없음인 사용자 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 image-1을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [purging-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

아무 이미지도 갖지 않은 id를 지우려 하면 이미지가 없다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: ImageNotFound

#### [purging-an-image-answers-with-the-image-it-removed](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

슈퍼관리자가 이미지를 지우면 지워진 이미지가 답으로 오고 되살릴 수 없다

Given

- 레지스트리 하나와 그 안의 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 image-1을 지움

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [purging-an-image-takes-its-aliases-with-it](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

별칭이 붙은 이미지를 지우면 이미지와 별칭이 함께 사라진다

Given

- 별칭이 붙은 이미지 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 이미지 image-1: 별칭 seeded-alias
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 별칭 seeded-alias가 붙은 이미지를 지움

Then

- 지운 이미지가 답으로 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

#### [the-maker-of-a-custom-image-may-purge-it](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 지우면, 게이트와 소유권 검사를 모두 지나 지워진 이미지가 답으로 온다

Given

- 부르는 사람이 만든 커스텀 이미지 하나, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 것이라 주인이 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_purge — user-1이 image-1을 지움

Then

- 심은 이미지 전체가 온다
  - name = 'image-1'
  - registry = 'host-1'
  - architecture = 'x86_64'
  - tag = 'latest'
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - is_local = False
  - size_bytes = 0
  - id: 무시함 — 데이터베이스가 만든다
  - last_used_at: 무시함 — 세션이 쓰는 값이라 이 실행이 말할 수 없다

### searching

#### [a-condition-given-from-outside-narrows-before-the-callers-filter](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

바깥에서 한 레지스트리로 좁혀 준 조건이 먼저 걸리므로, 그 레지스트리의 이미지만 답으로 온다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_images_gql — user-1이 한 레지스트리로 좁혀 조건 없이 검색함

Then

- 심은 이미지가 모두 세어진다
  - items = ['image-0-1', 'image-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-cursor-search-answers-the-first-page-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 커서로 앞에서부터 읽으면 정한 만큼 오고 다음 쪽이 있다고 답한다

Given

- 레지스트리 하나와 그 안의 이미지 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 이미지 image-2-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_images_gql — user-1이 커서로 앞에서부터 검색함

Then

- 정한 만큼만 오고 다음 쪽이 있다고 답한다
  - items = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

#### [a-cursor-that-cannot-be-read-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

읽을 수 없는 커서 값을 주면 커서가 틀렸다는 이유로 거부된다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_images_gql — user-1이 깨진 커서로 검색함

Then

- 거부된다
  - 거부: InvalidCursor

#### [a-user-who-is-not-the-superadmin-may-not-search-aliases](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 별칭을 검색하려 하면 역할로 막힌다

Given

- 레지스트리 하나와 그 안의 이미지 2개, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_image_aliases — user-1이 별칭을 검색함

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-search-images](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 이미지를 검색하려 하면 역할로 막힌다

Given

- 레지스트리 하나와 그 안의 이미지 2개, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search — user-1이 조건 없이 검색함

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

크기와 커서를 함께 주면 입력이 틀렸다는 이유로 거부된다. 요청 타입이 아니라 어댑터가 페이지 방식을 고르면서 낸다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_images_gql — user-1이 크기와 커서를 함께 주고 검색함

Then

- 거부된다
  - 거부: InvalidGraphQLParameters

#### [omitting-the-page-size-answers-with-fifty-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 페이지 크기를 생략하고 검색하면, 쉰 건까지만 오고 다음 쪽이 있다고 답한다

Given

- 레지스트리 하나와 그 안의 이미지 51개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 이미지 image-2-1: x86_64 이미지
  - 이미지 image-3-1: x86_64 이미지
  - 이미지 image-4-1: x86_64 이미지
  - 이미지 image-5-1: x86_64 이미지
  - 이미지 image-6-1: x86_64 이미지
  - 이미지 image-7-1: x86_64 이미지
  - 이미지 image-8-1: x86_64 이미지
  - 이미지 image-9-1: x86_64 이미지
  - 이미지 image-10-1: x86_64 이미지
  - 이미지 image-11-1: x86_64 이미지
  - 이미지 image-12-1: x86_64 이미지
  - 이미지 image-13-1: x86_64 이미지
  - 이미지 image-14-1: x86_64 이미지
  - 이미지 image-15-1: x86_64 이미지
  - 이미지 image-16-1: x86_64 이미지
  - 이미지 image-17-1: x86_64 이미지
  - 이미지 image-18-1: x86_64 이미지
  - 이미지 image-19-1: x86_64 이미지
  - 이미지 image-20-1: x86_64 이미지
  - 이미지 image-21-1: x86_64 이미지
  - 이미지 image-22-1: x86_64 이미지
  - 이미지 image-23-1: x86_64 이미지
  - 이미지 image-24-1: x86_64 이미지
  - 이미지 image-25-1: x86_64 이미지
  - 이미지 image-26-1: x86_64 이미지
  - 이미지 image-27-1: x86_64 이미지
  - 이미지 image-28-1: x86_64 이미지
  - 이미지 image-29-1: x86_64 이미지
  - 이미지 image-30-1: x86_64 이미지
  - 이미지 image-31-1: x86_64 이미지
  - 이미지 image-32-1: x86_64 이미지
  - 이미지 image-33-1: x86_64 이미지
  - 이미지 image-34-1: x86_64 이미지
  - 이미지 image-35-1: x86_64 이미지
  - 이미지 image-36-1: x86_64 이미지
  - 이미지 image-37-1: x86_64 이미지
  - 이미지 image-38-1: x86_64 이미지
  - 이미지 image-39-1: x86_64 이미지
  - 이미지 image-40-1: x86_64 이미지
  - 이미지 image-41-1: x86_64 이미지
  - 이미지 image-42-1: x86_64 이미지
  - 이미지 image-43-1: x86_64 이미지
  - 이미지 image-44-1: x86_64 이미지
  - 이미지 image-45-1: x86_64 이미지
  - 이미지 image-46-1: x86_64 이미지
  - 이미지 image-47-1: x86_64 이미지
  - 이미지 image-48-1: x86_64 이미지
  - 이미지 image-49-1: x86_64 이미지
  - 이미지 image-50-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search — user-1이 크기를 생략하고 검색함

Then

- 정한 만큼만 오고 다음 쪽이 있다고 답한다
  - items = 50
  - total_count = 51
  - has_next_page = True
  - has_previous_page = False

#### [searching-aliases-when-none-were-attached-answers-empty](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

별칭을 하나도 붙이지 않은 상태에서 슈퍼관리자가 별칭을 검색하면 답이 비어 있다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_image_aliases — user-1이 별칭을 검색함

Then

- 별칭이 하나도 없다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [searching-without-a-filter-counts-every-image](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 조건 없이 검색하면 심어둔 이미지가 모두 답으로 온다

Given

- 레지스트리 하나와 그 안의 이미지 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search — user-1이 조건 없이 검색함

Then

- 심은 이미지가 모두 세어진다
  - items = ['image-0-1', 'image-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

