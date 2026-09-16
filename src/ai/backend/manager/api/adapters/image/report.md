## image

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/image/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/image/adapter.py)

Not exercised by any scenario: batch_load_fields, scoped_search.

### aliasing

#### [a-user-who-is-not-the-superadmin-may-not-dealias](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 아닌 사용자가 별칭을 해제하려 하면 슈퍼관리자 권한 부족으로 거부된다

Given

- 별칭이 등록된 이미지 1개, user 1명
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

- ImageAdapter.admin_dealias — user-1이 별칭 seeded-alias 해제

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [aliasing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

어느 이미지도 가리키지 않는 ID에 별칭을 등록하려 하면 대상을 찾을 수 없어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_alias — user-1이 어느 이미지도 가리키지 않는 ID에 별칭 등록

Then

- 거부된다
  - 거부: ImageNotFound

#### [aliasing-an-image-answers-with-the-alias-and-the-image-it-names](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 이미지에 별칭을 등록하면 그 별칭과 가리키는 이미지가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_alias — user-1이 image-1에 별칭 made-alias 등록

Then

- 등록한 별칭과 그 이미지의 ID가 반환된다
  - alias = 'made-alias'
  - image_id: 미리 만들어 둔 이미지의 ID와 같다
  - alias_id: 무시함 — 데이터베이스가 생성한다

#### [an-alias-that-is-already-in-use-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

이미 사용 중인 별칭을 등록하려 하면 유니크 제약 위반으로 거부된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.admin_alias — user-1이 이미 사용 중인 별칭 seeded-alias 등록

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [dealiasing-a-name-no-image-holds-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

어느 이미지도 가리키지 않는 별칭을 해제하려 하면 대상을 찾을 수 없어 거부된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.admin_dealias — user-1이 어느 이미지도 가리키지 않는 별칭 해제

Then

- 거부된다
  - 거부: ImageAliasNotFound

#### [dealiasing-answers-with-the-alias-it-removed](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

슈퍼관리자가 등록된 별칭을 해제하면 해제된 별칭과 그 이미지가 반환된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.admin_dealias — user-1이 별칭 seeded-alias 해제

Then

- 해제한 별칭과 그 이미지의 ID가 반환된다
  - alias = 'seeded-alias'
  - image_id: 미리 만들어 둔 이미지의 ID와 같다
  - alias_id: 무시함 — 데이터베이스가 생성한다

#### [the-maker-of-a-custom-image-still-may-not-alias-it](/tests/scenario/bai_scenario/manager/image/test_aliasing.py) — pass

자기가 만든 커스텀 이미지라도 별칭은 등록할 수 없다. 별칭 등록은 해당 이미지의 권한이 아니라 슈퍼관리자 검사로 보호되기 때문이다

Given

- 호출자가 만든 커스텀 이미지 1개, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 이미지라 소유자가 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_alias — user-1이 image-1에 별칭 made-alias 등록

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-who-is-not-the-superadmin-may-not-edit-an-image](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 이미지를 수정하려 하면 슈퍼관리자 권한 부족으로 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, user 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 태그를 moved로 수정

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 값을 하나도 지정하지 않고 수정

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [changing-labels-and-resource-limits-returns-the-new-values](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 레이블과 CPU 하한·상한을 수정하면 지정한 값이 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 여러 필드를 함께 수정

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = [ImageLabelInfo(key='purpose', value='scenario')]
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='2', max='4'), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = [ImageLabelInfo(key='purpose', value='scenario')]
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='2', max='4'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [changing-only-the-tag-leaves-every-other-field-alone](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 태그만 수정하면 태그만 새 값이 되고 나머지 필드는 그대로다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 태그를 moved로 수정

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'moved'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [changing-the-remaining-scalar-fields-returns-the-new-values](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 이름과 레지스트리 등의 기본 필드를 함께 수정하면 지정한 값이 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 여러 필드를 함께 수정

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'updated-image'
  - image = 'team/updated-image'
  - registry = 'updated.example.com'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'aarch64'
  - size_bytes = 2048
  - type = <ImageType.SERVICE: 'service'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
  - is_local = True
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'updated-image'
  - identity.namespace = 'team/updated-image'
  - identity.architecture = 'aarch64'
  - metadata.digest = 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
  - metadata.size_bytes = 2048
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [clearing-the-accelerator-list-empties-it](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 가속기 목록을 비우는 수정을 하면 그 필드가 빈 채로 반환된다. 생략과 비우기를 구분할 수 있는 필드는 이것뿐이다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지, 가속기는 cuda
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 가속기 목록을 비움

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [editing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

어느 이미지도 가리키지 않는 ID를 수정하려 하면 대상을 찾을 수 없어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 어느 이미지도 가리키지 않는 ID 수정

Then

- 거부된다
  - 거부: ImageNotFound

#### [writing-an-accelerator-onto-an-image-that-had-none](/tests/scenario/bai_scenario/manager/image/test_editing.py) — pass

슈퍼관리자가 가속기 이름을 지정하면 그 이름이 담긴 노드가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_update — user-1이 image-1의 가속기 목록을 cuda로 지정

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = 'cuda'
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['cuda']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

### forgetting

#### [a-granted-user-may-not-forget-an-image-they-did-not-customize](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

커스텀 이미지가 아닌 이미지는 권한을 받은 사용자라도 소프트 삭제할 수 없다. 이미지 권한 검사를 통과한 뒤 커스텀 이미지 작성자 검사에서 거부된다

Given

- 커스텀 이미지가 아닌 이미지 1개, 그 이미지에 권한 있음인 사용자 1명
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

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

#### [a-user-granted-nothing-may-not-forget-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 권한도 받지 않은 사용자가 이미지를 소프트 삭제하려 하면 권한 부족으로 거부된다

Given

- 커스텀 이미지가 아닌 이미지 1개, 아무 권한도 없음인 사용자 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-restore-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

아무 권한도 받지 않은 사용자가 이미지를 복원하려 하면 권한 부족으로 거부된다

Given

- 커스텀 이미지가 아닌 이미지 1개, 아무 권한도 없음인 사용자 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1 복원

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-image-a-purge-is-working-through-cannot-be-reached](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

완전 삭제 중인 이미지를 소프트 삭제하려 하면 대상을 찾을 수 없어 거부된다. 그 상태의 이미지는 ID로 조회하는 지점에서 보이지 않는다

Given

- 레지스트리 1개와 그 안의 이미지 1개, 상태는 PURGING, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지, 상태는 PURGING
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 거부된다
  - 거부: ImageNotFound

#### [forgetting-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

어느 이미지도 가리키지 않는 ID를 소프트 삭제하려 하면 대상을 찾을 수 없어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 어느 이미지도 가리키지 않는 ID 소프트 삭제

Then

- 거부된다
  - 거부: ImageNotFound

#### [forgetting-an-image-marks-it-deleted-and-keeps-the-row](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

슈퍼관리자가 이미지를 소프트 삭제하면, 행은 남고 삭제됨 상태가 담긴 노드가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [restoring-a-forgotten-image-brings-it-back-alive](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

슈퍼관리자가 삭제된 이미지를 복원하면 살아 있는 상태가 담긴 노드가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, 상태는 DELETED, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지, 상태는 DELETED
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1 복원

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [restoring-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

어느 이미지도 가리키지 않는 ID를 복원하려 하면 대상을 찾을 수 없어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 어느 이미지도 가리키지 않는 ID 복원

Then

- 거부된다
  - 거부: ImageNotFound

#### [restoring-an-image-that-was-never-forgotten-leaves-it-alive](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

살아 있는 이미지를 복원해도 살아 있는 상태 그대로다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_restore — user-1이 image-1 복원

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [the-maker-of-a-custom-image-may-forget-it](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 소프트 삭제하면, 이미지 권한과 커스텀 이미지 작성자 검사를 모두 통과해 삭제됨 상태가 반환된다

Given

- 호출자가 만든 커스텀 이미지 1개, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 이미지라 소유자가 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [turning-enforcement-off-does-not-skip-the-custom-image-creator-check](/tests/scenario/bai_scenario/manager/image/test_forgetting.py) — pass

RBAC 권한 검사를 비활성화해도 커스텀 이미지가 아닌 이미지는 소프트 삭제할 수 없다. 커스텀 이미지 작성자 검사는 그 설정의 영향을 받지 않는다

Given

- 커스텀 이미지가 아닌 이미지 1개, 아무 권한도 없음인 사용자 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_forget — user-1이 image-1 소프트 삭제

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

### reading

#### [a-plain-user-loading-many-alias-ids-is-refused-per-element](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 별칭 ID 여러 개를 한 번에 조회하면, 있는 별칭 자리에는 권한 부족 거부가 오고 없는 ID 자리는 비어 있다

Given

- 별칭이 등록된 이미지 1개, user 1명
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

- ImageAdapter.batch_load_aliases_by_ids — user-1이 미리 만들어 둔 별칭 1개와 없는 ID 1개를 한 번에 조회

Then

- 있는 별칭 자리에는 권한 부족 거부가, 없는 ID 자리에는 빈 값이 온다
  - length = 2
  - 거부: NotEnoughPermission
  - [1] = None

#### [a-plain-user-loading-many-image-ids-is-refused-per-element](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 ID 여러 개를 한 번에 조회하면, 요청 전체가 아니라 원소마다 권한 부족 거부가 입력 순서대로 온다

Given

- 레지스트리 1개와 그 안의 이미지 2개, user 1명
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

- ImageAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 이미지 2개와 없는 ID 1개를 한 번에 조회

Then

- 원소마다 권한 부족 거부가 입력 순서대로 온다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-alias-id-list-answers-with-an-empty-list](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

빈 별칭 ID 목록으로 조회하면 빈 목록이 반환된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.batch_load_aliases_by_ids — user-1이 빈 별칭 ID 목록으로 조회

Then

- 빈 목록이 반환된다
  - items = []

#### [an-empty-image-id-list-answers-with-an-empty-list](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

빈 ID 목록으로 조회하면 빈 목록이 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

- ImageAdapter.batch_load_by_ids — user-1이 빈 ID 목록으로 조회

Then

- 빈 목록이 반환된다
  - items = []

#### [duplicate-image-ids-keep-both-input-positions](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

같은 이미지 ID를 두 번 조회하면 같은 이미지가 두 위치에 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.batch_load_by_ids — user-1이 같은 이미지 ID를 두 번 조회

Then

- 같은 이미지가 두 위치에 반환된다
  - length = 2
  - names = ['image-0-1', 'image-0-1']

#### [loading-many-alias-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 미리 만들어 둔 별칭 1개와 어느 별칭도 가리키지 않는 ID 1개를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 ID 위치만 비어 있다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.batch_load_aliases_by_ids — user-1이 미리 만들어 둔 별칭 1개와 없는 ID 1개를 한 번에 조회

Then

- 요청한 순서대로 반환되고 없는 ID 위치는 비어 있다
  - length = 2
  - aliases = ['seeded-alias', None]

#### [loading-many-image-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py) — pass

슈퍼관리자가 미리 만들어 둔 이미지 2개와 어느 이미지도 가리키지 않는 ID 1개를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 ID 위치만 비어 있다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

- ImageAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 이미지 2개와 없는 ID 1개를 한 번에 조회

Then

- 요청한 순서대로 반환되고 없는 ID 위치는 비어 있다
  - length = 3
  - [0].name = 'image-0-1'
  - [1] = None
  - [2].name = 'image-1-1'

### retiring

#### [a-granted-user-may-not-purge-an-image-they-did-not-customize](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

커스텀 이미지가 아닌 이미지는 권한을 받은 사용자라도 완전 삭제할 수 없다. 이미지 권한 검사를 통과한 뒤 커스텀 이미지 작성자 검사에서 거부된다

Given

- 커스텀 이미지가 아닌 이미지 1개, 그 이미지에 권한 있음인 사용자 1명
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

- ImageAdapter.admin_purge — user-1이 image-1 완전 삭제

Then

- 거부된다
  - 거부: ImageAccessForbiddenError

#### [a-user-granted-nothing-may-not-purge-an-image](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 이미지를 완전 삭제하려 하면 권한 부족으로 거부된다

Given

- 커스텀 이미지가 아닌 이미지 1개, 아무 권한도 없음인 사용자 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 image-1 완전 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [purging-an-aliased-image-answers-with-the-image-it-removed](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

별칭이 등록된 이미지를 완전 삭제하면 삭제된 이미지가 반환된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.admin_purge — user-1이 별칭 seeded-alias가 등록된 이미지를 완전 삭제

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [purging-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

어느 이미지도 가리키지 않는 ID를 완전 삭제하려 하면 대상을 찾을 수 없어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 어느 이미지도 가리키지 않는 ID 완전 삭제

Then

- 거부된다
  - 거부: ImageNotFound

#### [purging-an-image-answers-with-the-image-it-removed](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

슈퍼관리자가 이미지를 완전 삭제하면 삭제된 이미지가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_purge — user-1이 image-1 완전 삭제

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

#### [the-maker-of-a-custom-image-may-purge-it](/tests/scenario/bai_scenario/manager/image/test_retiring.py) — pass

자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 완전 삭제하면, 이미지 권한과 커스텀 이미지 작성자 검사를 모두 통과해 삭제된 이미지가 반환된다

Given

- 호출자가 만든 커스텀 이미지 1개, 그 이미지에 권한 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 이미지 image-1: x86_64 이미지, 커스터마이즈된 이미지라 소유자가 있다
  - 이미지를 다룰 권한을 받은 사용자 준비
    - 역할 image-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 image-keeper-1: image 전체에 READ 허용
    - 역할 image-keeper-1: image 전체에 SOFT_DELETE 허용
    - 역할 image-keeper-1: image 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 image-keeper-1 보유

When

- ImageAdapter.admin_purge — user-1이 image-1 완전 삭제

Then

- 이미지 노드의 모든 필드가 예상값과 일치한다
  - id: 미리 만들어 둔 이미지의 ID와 같다
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: 미리 만들어 둔 레지스트리의 ID와 같다
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - created_at: 이 실행이 쓴 시각
  - last_used_at: 무시함 — 세션이 기록하는 값이라 이 실행에서는 알 수 없다
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.last_used_at: 노드의 last_used_at 필드와 같다
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

### searching

#### [a-condition-given-from-outside-narrows-before-the-callers-filter](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

이미지가 레지스트리 2개에 나뉘어 있을 때 호출 측이 한쪽으로 좁혀 주면, 그 레지스트리의 이미지만 반환되고 다른 쪽은 집계되지 않는다

Given

- 레지스트리 2개, 한쪽에 이미지 2개와 다른 쪽에 2개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 이미지 here-0-1: x86_64 이미지
  - 이미지 here-1-1: x86_64 이미지
  - 이미지 there-0-1: x86_64 이미지
  - 이미지 there-1-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_images_gql — user-1이 한 레지스트리로 좁혀 한 페이지에 50개씩 검색함

Then

- 미리 만들어 둔 이미지가 모두 집계된다
  - items = ['here-0-1', 'here-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-cursor-alone-answers-the-first-page-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py) — FAIL

슈퍼관리자가 크기와 오프셋 없이 커서만 지정해 검색하면 지정한 개수만 반환되고 다음 페이지가 있다고 알린다

Given

- 레지스트리 1개와 그 안의 이미지 3개, superadmin 1명
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

- ImageAdapter.admin_search — user-1이 커서로 앞에서부터 검색함

Then

- 지정한 개수만 반환되고 다음 페이지가 있다고 알린다
  - length = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

#### [a-cursor-search-answers-the-first-page-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 커서로 앞에서부터 조회하면 지정한 개수만 반환되고 다음 페이지가 있다고 알린다

Given

- 레지스트리 1개와 그 안의 이미지 3개, superadmin 1명
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

- 지정한 개수만 반환되고 다음 페이지가 있다고 알린다
  - length = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

#### [a-cursor-that-cannot-be-read-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

해석할 수 없는 커서 값을 지정하면 커서가 잘못되어 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

- ImageAdapter.admin_search_images_gql — user-1이 잘못된 커서로 검색함

Then

- 거부된다
  - 거부: InvalidCursor

#### [a-size-beside-a-cursor-pages-by-offset](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

크기와 커서를 함께 지정하면 커서는 무시되고 크기대로 오프셋 페이지가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 3개, superadmin 1명
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

- ImageAdapter.admin_search — user-1이 크기와 커서를 함께 지정하고 검색함

Then

- 지정한 개수만 반환되고 다음 페이지가 있다고 알린다
  - length = 1
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-aliases](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 별칭을 검색하려 하면 슈퍼관리자 권한 부족으로 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 2개, user 1명
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

슈퍼관리자가 아닌 사용자가 이미지를 검색하려 하면 슈퍼관리자 권한 부족으로 거부된다

Given

- 레지스트리 1개와 그 안의 이미지 2개, user 1명
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

- ImageAdapter.admin_search — user-1이 한 페이지에 50개씩 검색함

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-aliases-by-image-and-ordering-by-name](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 한 이미지의 별칭만 이름 내림차순으로 검색하면 해당 별칭만 정렬되어 반환된다

Given

- 이미지 2개, 한쪽에 별칭 2개와 다른 쪽에 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 wanted-1: x86_64 이미지
  - 이미지 other-1: x86_64 이미지
  - 이미지 wanted-1: 별칭 alpha
  - 이미지 wanted-1: 별칭 zeta
  - 이미지 other-1: 별칭 middle
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search_image_aliases — user-1이 한 이미지의 별칭을 이름 내림차순으로 검색함

Then

- 해당 이미지의 별칭만 이름 내림차순으로 반환된다
  - items = ['zeta', 'alpha']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-images-by-name-returns-only-the-match](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 한 이미지의 이름으로 검색하면 그 이미지만 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 3개, superadmin 1명
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

- ImageAdapter.admin_search — user-1이 image-0-1 이름으로 한 페이지에 50개씩 검색함

Then

- 이름이 일치하는 이미지만 반환된다
  - items = ['image-0-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-images-by-status-returns-only-alive-images](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

살아 있는 이미지와 삭제된 이미지 중 살아 있는 상태로 검색하면 해당 이미지만 반환된다

Given

- 살아 있는 이미지 1개와 삭제된 이미지 1개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 alive-1: x86_64 이미지
  - 이미지 deleted-1: x86_64 이미지, 상태는 DELETED
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search — user-1이 ALIVE 상태로 한 페이지에 50개씩 검색함

Then

- 살아 있는 이미지만 반환된다
  - items = ['alive-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

크기와 커서를 함께 지정하면 입력이 잘못되어 거부된다. 요청 타입이 아니라 어댑터가 페이지 방식을 고르는 과정에서 발생한다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

- ImageAdapter.admin_search_images_gql — user-1이 크기와 커서를 함께 지정하고 검색함

Then

- 거부된다
  - 거부: InvalidGraphQLParameters

#### [omitting-the-page-size-answers-with-fifty-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

슈퍼관리자가 페이지 크기를 생략하고 검색하면, 50개까지만 반환되고 다음 페이지가 있다고 알린다

Given

- 레지스트리 1개와 그 안의 이미지 51개, superadmin 1명
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

- ImageAdapter.admin_search — user-1이 페이지 크기를 생략하고 검색함

Then

- 지정한 개수만 반환되고 다음 페이지가 있다고 알린다
  - length = 50
  - total_count = 51
  - has_next_page = True
  - has_previous_page = False

#### [ordering-by-name-and-offsetting-returns-the-middle-page](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

이름 내림차순으로 정렬하고 첫 항목을 제외하면 두 번째와 세 번째 이미지가 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 4개, superadmin 1명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-0-1: x86_64 이미지
  - 이미지 image-1-1: x86_64 이미지
  - 이미지 image-2-1: x86_64 이미지
  - 이미지 image-3-1: x86_64 이미지
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ImageAdapter.admin_search — user-1이 이름 내림차순으로 정렬해 앞의 1개를 건너뛰고 한 페이지에 2개씩 검색함

Then

- 정렬된 결과의 가운데 2개와 앞뒤 페이지 표시가 반환된다
  - items = ['image-2-1', 'image-1-1']
  - total_count = 4
  - has_next_page = True
  - has_previous_page = True

#### [searching-aliases-answers-with-the-one-that-was-attached](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

별칭이 등록되어 있을 때 슈퍼관리자가 별칭을 검색하면 그 별칭이 반환된다

Given

- 별칭이 등록된 이미지 1개, superadmin 1명
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

- ImageAdapter.admin_search_image_aliases — user-1이 별칭을 검색함

Then

- 등록해 둔 별칭이 반환된다
  - items = ['seeded-alias']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [searching-aliases-when-none-were-attached-answers-empty](/tests/scenario/bai_scenario/manager/image/test_searching.py) — pass

별칭을 하나도 등록하지 않은 상태에서 슈퍼관리자가 별칭을 검색하면 응답이 비어 있다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

슈퍼관리자가 조건 없이 검색하면 미리 만들어 둔 이미지가 모두 반환된다

Given

- 레지스트리 1개와 그 안의 이미지 2개, superadmin 1명
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

- ImageAdapter.admin_search — user-1이 한 페이지에 50개씩 검색함

Then

- 미리 만들어 둔 이미지가 모두 집계된다
  - items = ['image-0-1', 'image-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

