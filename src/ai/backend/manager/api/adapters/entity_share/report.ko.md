## entity_share

[어댑터](/src/ai/backend/manager/api/adapters/entity_share/adapter.py)

시나리오: 완성

- ops 구성 (4)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - my_search: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (6)
  - accept: 성공 있음 1 · 거부 있음 1 (scope)
  - cancel: 성공 있음 1 · 거부 있음 1 (single_entity)
  - create: 성공 있음 1 · 거부 있음 1 (scope)
  - leave: 성공 있음 1 · 거부 있음 1 (scope)
  - reject: 성공 있음 1 · 거부 있음 1 (scope)
  - revoke: 성공 있음 1 · 거부 있음 1 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 공유 읽기 권한을 받은 사용자가 id 로 조회하면 그 공유가 노드로 옵니다](#reading-a-user-granted-on-the-project-loads-the-share) | 성공 |
| [id 로 읽으면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다](#reading-an-unknown-share-id-answers-a-denial) | 성공 |
| [아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다](#reading-a-user-granted-nothing-gets-a-denial-for-the-share) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 공유 읽기 권한을 받은 사용자가 공유를 조회하면 그 공유가 통째로 옵니다](#reading-a-user-granted-on-the-project-reads-the-share) | 성공 |
| [아무 권한도 없는 사용자가 공유를 조회하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-the-share) | 거부 |

**my_search**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 공유를 읽을 수 있는 사용자가 자기에게 온 공유를 훑으면 자기가 보낸 제안과 자기와 무관한 제안은 빠지고 그 공유만 한 페이지로 옵니다](#searching-the-recipient-pages-through-the-shares-addressed-to-them) | 성공 |
| [아무 권한도 없는 사용자가 자기에게 온 공유를 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-their-shares) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 공유를 읽을 수 있는 사용자가 폴더를 범위로 받는 사람을 걸러 훑으면 다른 폴더의 제안과 다른 사람에게 간 제안은 빠지고 그 공유만 한 페이지로 옵니다](#searching-the-sharer-pages-through-the-shares-of-a-folder) | 성공 |
| [아무 권한도 없는 사용자가 폴더를 범위로 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-a-folders-shares) | 거부 |

**accept**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 받아들이면 받아들인 공유가 통째로 옵니다](#answering-the-recipient-accepts-the-offer) | 성공 |
| [아무 권한도 없는 사용자가 제안을 받아들이면 권한 부족으로 거부됩니다](#answering-a-user-granted-nothing-may-not-accept-the-offer) | 거부 |

**cancel**

| 시나리오 | 판정 |
|---|---|
| [빌려준 사람이 응답하지 않은 제안을 취소하면 취소된 공유가 통째로 옵니다](#withdrawing-the-sharer-cancels-the-unanswered-offer) | 성공 |
| [아무 권한도 없는 사용자가 제안을 취소하면 권한 부족으로 거부됩니다](#withdrawing-a-user-granted-nothing-may-not-cancel-the-offer) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 공유 생성 권한을 받은 사용자가 폴더를 다른 사람에게 제안하면 아직 응답하지 않은 공유가 통째로 옵니다](#creating-a-user-granted-on-the-project-offers-the-folder) | 성공 |
| [아무 권한도 없는 사용자가 폴더를 제안하면 권한 부족으로 거부됩니다](#creating-a-user-granted-nothing-cannot-offer-the-folder) | 거부 |

**leave**

| 시나리오 | 판정 |
|---|---|
| [빌린 사람이 자기 스코프에서 공유에서 탈퇴하면 회수된 공유가 통째로 옵니다](#withdrawing-the-recipient-leaves-the-share) | 성공 |
| [아무 권한도 없는 사용자가 공유에서 탈퇴해도 권한 부족으로 거부됩니다](#withdrawing-a-user-granted-nothing-may-not-leave-the-share) | 거부 |

**reject**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 거절하면 거절된 공유가 통째로 옵니다](#answering-the-recipient-rejects-the-offer) | 성공 |
| [아무 권한도 없는 사용자가 제안을 거절해도 권한 부족으로 거부됩니다](#answering-a-user-granted-nothing-may-not-reject-the-offer) | 거부 |

**revoke**

| 시나리오 | 판정 |
|---|---|
| [빌려준 사람이 빌려준 공유를 회수하면 회수된 공유가 통째로 옵니다](#withdrawing-the-sharer-takes-back-the-share) | 성공 |
| [아무 권한도 없는 사용자가 공유를 회수하면 권한 부족으로 거부됩니다](#withdrawing-a-user-granted-nothing-may-not-take-the-share-back) | 거부 |

### batch_load_by_ids

<a id="reading-a-user-granted-on-the-project-loads-the-share"></a>

#### [a-user-granted-on-the-project-loads-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

프로젝트에서 공유 읽기 권한을 받은 사용자가 id 로 조회하면 그 공유가 노드로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.batch_load_by_ids: user-1이 공유 하나를 한 번에 조회합니다

Then

- 미리 만든 공유가 노드로 옵니다
  - length = 1
  - [0].sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - [0].recipient_entity_type = 'user'
  - [0].recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - [0].recipient_email = None
  - [0].target_entity_type = 'vfolder'
  - [0].target_entity_id: 미리 만든 폴더의 id 와 같다
  - [0].permissions = []
  - [0].status = 'pending'
  - [0].expires_at = None
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [0].id: 미리 만든 공유의 id 와 같다
  - [0].entity_id: 미리 만든 공유의 id 와 같다

<a id="reading-an-unknown-share-id-answers-a-denial"></a>

#### [an-unknown-share-id-answers-a-denial](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

id 로 읽으면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.batch_load_by_ids: user-1이 공유 하나와 없는 id 하나를 한 번에 조회합니다

Then

- 미리 만든 공유는 노드로, 없는 id 자리는 권한 부족으로 옵니다
  - length = 2
  - [0].sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - [0].recipient_entity_type = 'user'
  - [0].recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - [0].recipient_email = None
  - [0].target_entity_type = 'vfolder'
  - [0].target_entity_id: 미리 만든 폴더의 id 와 같다
  - [0].permissions = []
  - [0].status = 'pending'
  - [0].expires_at = None
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [0].id: 미리 만든 공유의 id 와 같다
  - [0].entity_id: 미리 만든 공유의 id 와 같다
  - [1] denied = 'NotEnoughPermission'

<a id="reading-a-user-granted-nothing-gets-a-denial-for-the-share"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.batch_load_by_ids: user-3이 공유 하나를 한 번에 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### get

<a id="reading-a-user-granted-on-the-project-reads-the-share"></a>

#### [a-user-granted-on-the-project-reads-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

프로젝트에서 공유 읽기 권한을 받은 사용자가 공유를 조회하면 그 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.get: user-1이 폴더 folder-1에 걸린 공유를 조회합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'pending'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="reading-a-user-granted-nothing-may-not-read-the-share"></a>

#### [a-user-granted-nothing-may-not-read-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

아무 권한도 없는 사용자가 공유를 조회하면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.get: user-3이 폴더 folder-1에 걸린 공유를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_search

<a id="searching-the-recipient-pages-through-the-shares-addressed-to-them"></a>

#### [the-recipient-pages-through-the-shares-addressed-to-them](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

자기 스코프에서 공유를 읽을 수 있는 사용자가 자기에게 온 공유를 훑으면 자기가 보낸 제안과 자기와 무관한 제안은 빠지고 그 공유만 한 페이지로 옵니다

Given

- 범위 밖의 폴더 하나와 받는 사람이 내는 제안 하나, 같은 폴더를 세 번째 사람에게 빌려주는 제안 하나, 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌린 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - 프로젝트 vfolder other-folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 other-share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 bystander-share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.my_search: user-2이 자기가 선 쪽의 공유를 훑습니다

Then

- 미리 만든 공유가 통째로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - items[0].recipient_entity_type = 'user'
  - items[0].recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - items[0].recipient_email = None
  - items[0].target_entity_type = 'vfolder'
  - items[0].target_entity_id: 미리 만든 폴더의 id 와 같다
  - items[0].permissions = []
  - items[0].status = 'pending'
  - items[0].expires_at = None
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 만든 공유의 id 와 같다
  - items[0].entity_id: 미리 만든 공유의 id 와 같다

<a id="searching-a-user-granted-nothing-may-not-page-through-their-shares"></a>

#### [a-user-granted-nothing-may-not-page-through-their-shares](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

아무 권한도 없는 사용자가 자기에게 온 공유를 훑으면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.my_search: user-3이 자기가 선 쪽의 공유를 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-the-sharer-pages-through-the-shares-of-a-folder"></a>

#### [the-sharer-pages-through-the-shares-of-a-folder](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

프로젝트에서 공유를 읽을 수 있는 사용자가 폴더를 범위로 받는 사람을 걸러 훑으면 다른 폴더의 제안과 다른 사람에게 간 제안은 빠지고 그 공유만 한 페이지로 옵니다

Given

- 범위 밖의 폴더 하나와 받는 사람이 내는 제안 하나, 같은 폴더를 세 번째 사람에게 빌려주는 제안 하나, 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - 프로젝트 vfolder other-folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 other-share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 bystander-share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.scoped_search: user-1이 폴더 folder-1에 걸린 공유 가운데 user-2에게 간 것을 훑습니다

Then

- 미리 만든 공유가 통째로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - items[0].recipient_entity_type = 'user'
  - items[0].recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - items[0].recipient_email = None
  - items[0].target_entity_type = 'vfolder'
  - items[0].target_entity_id: 미리 만든 폴더의 id 와 같다
  - items[0].permissions = []
  - items[0].status = 'pending'
  - items[0].expires_at = None
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 만든 공유의 id 와 같다
  - items[0].entity_id: 미리 만든 공유의 id 와 같다

<a id="searching-a-user-granted-nothing-may-not-page-through-a-folders-shares"></a>

#### [a-user-granted-nothing-may-not-page-through-a-folders-shares](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

아무 권한도 없는 사용자가 폴더를 범위로 훑으면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.scoped_search: user-3이 폴더 folder-1에 걸린 공유 가운데 user-2에게 간 것을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### accept

<a id="answering-the-recipient-accepts-the-offer"></a>

#### [the-recipient-accepts-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 받아들이면 받아들인 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌린 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.accept: user-2이 폴더 folder-1의 공유 제안을 받아들입니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'accepted'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="answering-a-user-granted-nothing-may-not-accept-the-offer"></a>

#### [a-user-granted-nothing-may-not-accept-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

아무 권한도 없는 사용자가 제안을 받아들이면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.accept: user-3이 폴더 folder-1의 공유 제안을 받아들입니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### cancel

<a id="withdrawing-the-sharer-cancels-the-unanswered-offer"></a>

#### [the-sharer-cancels-the-unanswered-offer](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

빌려준 사람이 응답하지 않은 제안을 취소하면 취소된 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.cancel: user-1이 폴더 folder-1의 공유를 응답하지 않은 제안을 취소합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'canceled'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="withdrawing-a-user-granted-nothing-may-not-cancel-the-offer"></a>

#### [a-user-granted-nothing-may-not-cancel-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

아무 권한도 없는 사용자가 제안을 취소하면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.cancel: user-3이 폴더 folder-1의 공유를 응답하지 않은 제안을 취소합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create

<a id="creating-a-user-granted-on-the-project-offers-the-folder"></a>

#### [a-user-granted-on-the-project-offers-the-folder](/tests/scenario/bai_scenario/manager/entity_share/test_creating.py): pass

프로젝트에서 공유 생성 권한을 받은 사용자가 폴더를 다른 사람에게 제안하면 아직 응답하지 않은 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와 두 사람, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityShareAdapter.create: user-1이 폴더 folder-1를 user-2에게 빌려주는 제안을 합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'pending'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 같은 응답이 담은 공유의 id 와 같다

<a id="creating-a-user-granted-nothing-cannot-offer-the-folder"></a>

#### [a-user-granted-nothing-cannot-offer-the-folder](/tests/scenario/bai_scenario/manager/entity_share/test_creating.py): pass

아무 권한도 없는 사용자가 폴더를 제안하면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와 두 사람, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityShareAdapter.create: user-3이 폴더 folder-1를 user-2에게 빌려주는 제안을 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### leave

<a id="withdrawing-the-recipient-leaves-the-share"></a>

#### [the-recipient-leaves-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

빌린 사람이 자기 스코프에서 공유에서 탈퇴하면 회수된 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 빌려준 공유, 그리고 폴더를 빌린 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임

When

- EntityShareAdapter.leave: user-2이 폴더 folder-1의 공유를 빌린 공유에서 탈퇴합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'revoked'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="withdrawing-a-user-granted-nothing-may-not-leave-the-share"></a>

#### [a-user-granted-nothing-may-not-leave-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

아무 권한도 없는 사용자가 공유에서 탈퇴해도 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.leave: user-3이 폴더 folder-1의 공유를 빌린 공유에서 탈퇴합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### reject

<a id="answering-the-recipient-rejects-the-offer"></a>

#### [the-recipient-rejects-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 거절하면 거절된 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 폴더를 빌린 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.reject: user-2이 폴더 folder-1의 공유 제안을 거절합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'rejected'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="answering-a-user-granted-nothing-may-not-reject-the-offer"></a>

#### [a-user-granted-nothing-may-not-reject-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

아무 권한도 없는 사용자가 제안을 거절해도 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다

When

- EntityShareAdapter.reject: user-3이 폴더 folder-1의 공유 제안을 거절합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### revoke

<a id="withdrawing-the-sharer-takes-back-the-share"></a>

#### [the-sharer-takes-back-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

빌려준 사람이 빌려준 공유를 회수하면 회수된 공유가 통째로 옵니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 빌려준 공유, 그리고 폴더를 빌려주는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임

When

- EntityShareAdapter.revoke: user-1이 폴더 folder-1의 공유를 빌려준 공유를 회수합니다

Then

- 그 공유 전체가 응답으로 옵니다
  - sharer_user_id: 미리 만든 빌려준 사람의 id 와 같다
  - recipient_entity_type = 'user'
  - recipient_entity_id: 미리 만든 빌린 사람의 id 와 같다
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: 미리 만든 폴더의 id 와 같다
  - permissions = []
  - status = 'revoked'
  - expires_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 만든 공유의 id 와 같다
  - entity_id: 미리 만든 공유의 id 와 같다

<a id="withdrawing-a-user-granted-nothing-may-not-take-the-share-back"></a>

#### [a-user-granted-nothing-may-not-take-the-share-back](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

아무 권한도 없는 사용자가 공유를 회수하면 권한 부족으로 거부됩니다

Given

- 프로젝트 폴더 하나와, 다른 사람에게 빌려준 공유, 그리고 아무 관련 없는 사람
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 범위의 공유 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 share-lender-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-lender-1: entity_share 전체에 CREATE 허용
    - 역할 share-lender-1: entity_share 전체에 READ 허용
    - 역할 share-lender-1: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 share-lender-1 보유
  - 자기 스코프의 공유 권한을 받은 사용자 준비
    - 역할 share-recipient-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-1: entity_share 전체에 READ 허용
    - 일반 사용자 user-1: 역할 share-recipient-1 보유
    - 역할 share-recipient-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 share-recipient-2: entity_share 전체에 READ 허용
    - 역할 share-recipient-2: entity_share 전체에 UPDATE 허용
    - 역할 share-recipient-2: entity_share 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 share-recipient-2 보유
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - vfolder 공유 제안 share-1: 권한 상한 없이 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임

When

- EntityShareAdapter.revoke: user-3이 폴더 folder-1의 공유를 빌려준 공유를 회수합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

