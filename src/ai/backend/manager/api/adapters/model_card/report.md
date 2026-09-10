## model_card

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

Not exercised by any scenario: admin_bulk_delete, available_presets, batch_load_fields, create, delete, deploy, get, min_resources, project_search, scan_project, scoped_search, search_by_vfolder, update.

### model_card

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — 슈퍼관리자 user-1
  - SearchModelCardsInput()

Then

- 답 전체 일치

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — 일반 사용자 user-1
  - SearchModelCardsInput()

Then

- 거부: InsufficientPrivilege

