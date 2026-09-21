## model_card

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

Not exercised by any scenario: admin_bulk_delete, batch_load_fields, create, delete, deploy, get, min_resources, project_search, scan_project, scoped_search, update.

### available_presets

#### [a-user-granted-nothing-may-not-ask-which-presets-fit-the-card](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py) — pass

아무 권한도 받지 않은 사용자가 카드에 쓸 수 있는 프리셋을 물으면, 권한 부족으로 거부된다

Given

- 요구 자원이 있는 카드 하나와, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그리고 아무 모델 카드 권한도 받지 않은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 store-1
  - 모델 카드 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - cpu와 메모리 슬롯 타입 준비
    - 자원 슬롯 타입 cpu: 리비전이 채우지 않아도 된다
    - 자원 슬롯 타입 mem: 리비전이 채우지 않아도 된다
  - 모델 카드 card-1: 접근 수준은 internal, 요구 자원은 따로 심는다
  - 모델 카드 card-1: cpu 최소 4 필요
  - 모델 카드 card-1: mem 최소 2048 필요
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 fitting-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 fitting-1: cpu 8 할당
  - 배포 리비전 프리셋 fitting-1: mem 4096 할당
  - 배포 리비전 프리셋 lacking-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 lacking-1: cpu 1 할당
  - 배포 리비전 프리셋 lacking-1: mem 1024 할당

When

- ModelCardAdapter.available_presets — user-1이 card-1에 쓸 수 있는 프리셋 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-the-card-sees-the-presets-that-fit-it](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py) — pass

카드 읽기 권한을 받은 사용자가 그 카드에 쓸 수 있는 프리셋을 물으면, 카드의 요구 자원을 모두 채우는 프리셋만 반환된다

Given

- 요구 자원이 있는 카드 하나와, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그리고 모델 카드에 READ 권한을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 store-1
  - 모델 카드에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 card-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-user-1: model_card 전체에 READ 허용
    - 일반 사용자 user-1: 역할 card-user-1 보유
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - cpu와 메모리 슬롯 타입 준비
    - 자원 슬롯 타입 cpu: 리비전이 채우지 않아도 된다
    - 자원 슬롯 타입 mem: 리비전이 채우지 않아도 된다
  - 모델 카드 card-1: 접근 수준은 internal, 요구 자원은 따로 심는다
  - 모델 카드 card-1: cpu 최소 4 필요
  - 모델 카드 card-1: mem 최소 2048 필요
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 fitting-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 fitting-1: cpu 8 할당
  - 배포 리비전 프리셋 fitting-1: mem 4096 할당
  - 배포 리비전 프리셋 lacking-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 lacking-1: cpu 1 할당
  - 배포 리비전 프리셋 lacking-1: mem 1024 할당

When

- ModelCardAdapter.available_presets — user-1이 card-1에 쓸 수 있는 프리셋 조회

Then

- 카드의 요구를 모두 채우는 프리셋만 온다
  - items = ['fitting-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py) — pass

슈퍼관리자가 존재하지 않는 id로 물으면, 대상을 찾을 수 없다는 이유로 거부된다. 권한 검사를 통과하는 사용자만 이 응답을 본다

Given

- 요구 자원이 있는 카드 하나와, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그리고 아무 모델 카드 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 store-1
  - 모델 카드 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - cpu와 메모리 슬롯 타입 준비
    - 자원 슬롯 타입 cpu: 리비전이 채우지 않아도 된다
    - 자원 슬롯 타입 mem: 리비전이 채우지 않아도 된다
  - 모델 카드 card-1: 접근 수준은 internal, 요구 자원은 따로 심는다
  - 모델 카드 card-1: cpu 최소 4 필요
  - 모델 카드 card-1: mem 최소 2048 필요
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 fitting-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 fitting-1: cpu 8 할당
  - 배포 리비전 프리셋 fitting-1: mem 4096 할당
  - 배포 리비전 프리셋 lacking-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 lacking-1: cpu 1 할당
  - 배포 리비전 프리셋 lacking-1: mem 1024 할당

When

- ModelCardAdapter.available_presets — user-1이 존재하지 않는 id에 쓸 수 있는 프리셋 조회

Then

- 거부된다
  - 거부: ModelCardNotFound

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py) — pass

카드 읽기 권한을 받은 사용자가 존재하지 않는 id로 물으면, 대상 없음이 아니라 권한 부족으로 거부된다. 없는 행에는 부여된 권한도 없기 때문이다

Given

- 요구 자원이 있는 카드 하나와, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그리고 모델 카드에 READ 권한을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 store-1
  - 모델 카드에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 card-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-user-1: model_card 전체에 READ 허용
    - 일반 사용자 user-1: 역할 card-user-1 보유
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - cpu와 메모리 슬롯 타입 준비
    - 자원 슬롯 타입 cpu: 리비전이 채우지 않아도 된다
    - 자원 슬롯 타입 mem: 리비전이 채우지 않아도 된다
  - 모델 카드 card-1: 접근 수준은 internal, 요구 자원은 따로 심는다
  - 모델 카드 card-1: cpu 최소 4 필요
  - 모델 카드 card-1: mem 최소 2048 필요
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
  - 배포 리비전 프리셋 fitting-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 fitting-1: cpu 8 할당
  - 배포 리비전 프리셋 fitting-1: mem 4096 할당
  - 배포 리비전 프리셋 lacking-1: 공개 스코프에 놓이고, 할당 슬롯은 따로 심는다
  - 배포 리비전 프리셋 lacking-1: cpu 1 할당
  - 배포 리비전 프리셋 lacking-1: mem 1024 할당

When

- ModelCardAdapter.available_presets — user-1이 존재하지 않는 id에 쓸 수 있는 프리셋 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

### model_card

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

