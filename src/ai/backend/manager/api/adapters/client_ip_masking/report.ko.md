## client_ip_masking

[배경](/src/ai/backend/manager/api/adapters/client_ip_masking/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/client_ip_masking/adapter.py)

시나리오: 미완성 2 / 5

- ops 구성 (5)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - upsert: 대표 성공 ✓ · 대표 거부 ✓

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [모니터 역할이 필터 없이 조회하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사는 모니터의 읽기를 허용합니다](#searching-the-monitor-searches-masking-policies-like-the-superadmin) | 성공 |
| [대상이 다른 정책 둘이 있을 때 superadmin 이 필터 없이 조회하면 둘 다 집계됩니다](#searching-the-superadmin-counts-every-masking-policy-laid) | 성공 |
| [superadmin 이 아닌 사용자가 전체를 조회하도록 요청하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-masking-policies) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 정책 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-masking-policies) | 성공 |
| [superadmin 이 정책 둘과 없는 id 하나를 한 번에 purge 하면 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-masking-policies-answers-for-the-missing-one) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 정책을 id 로 삭제하면 삭제한 정책 전체를 담은 응답이 반환됩니다](#retiring-the-superadmin-purges-a-masking-policy) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 삭제할 수 있습니다](#retiring-turning-enforcement-off-lets-a-user-purge-a-masking-policy) | 성공 |
| [아무 권한도 없는 사용자가 정책을 삭제하면 권한 부족으로 거부됩니다. 등록이 역할 부족으로 거부되는 것과는 다른 검사입니다](#retiring-a-user-granted-nothing-may-not-purge-a-masking-policy) | 거부 |
| [아무 권한도 없는 사용자가 존재하지 않는 id 를 삭제하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 row 에는 부여된 권한도 없기 때문입니다](#retiring-a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission) | 거부 |
| [superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다](#retiring-purging-a-masking-policy-id-nothing-answers-to-is-not-found) | 거부 |

**upsert**

| 시나리오 | 판정 |
|---|---|
| [대상과 모드만 지정해 등록하면 두 접두 길이가 비어 있는 노드가 반환됩니다](#upserting-a-masking-policy-put-without-prefixes-carries-empty-prefixes) | 성공 |
| [접두 길이가 있는 정책의 대상에 대상과 모드만 지정해 다시 등록하면 접두 길이가 비워집니다. 등록은 기존 값과 병합하지 않고 row 전체를 변경합니다](#upserting-putting-a-policy-again-without-prefixes-clears-the-stored-prefixes) | 성공 |
| [이미 정책이 있는 대상에 다른 모드로 등록하면 새 row 가 아니라 같은 id 의 row 가 새 모드로 변경된 노드가 반환됩니다](#upserting-putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row) | 성공 |
| [정책이 없을 때 superadmin 이 대상, 모드, 두 접두 길이를 지정해 등록하면 지정한 값이 그대로 담긴 노드가 반환됩니다](#upserting-the-superadmin-puts-a-masking-policy-on-a-target) | 성공 |
| [superadmin 이 아닌 사용자가 정책을 등록하면 역할 부족으로 거부됩니다](#upserting-a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy) | 거부 |
| [모니터 역할이 정책을 등록하면 역할 부족으로 거부됩니다. 모니터는 superadmin 검사에서 읽기만 통과합니다](#upserting-the-monitor-may-not-put-a-masking-policy) | 거부 |
| [권한 검사를 꺼도 superadmin 이 아니면 정책을 등록하지 못합니다](#upserting-turning-enforcement-off-does-not-let-a-user-put-a-masking-policy) | 거부 |

### admin_search

<a id="searching-the-monitor-searches-masking-policies-like-the-superadmin"></a>

#### [the-monitor-searches-masking-policies-like-the-superadmin](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

모니터 역할이 필터 없이 조회하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사는 모니터의 읽기를 허용합니다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 모니터 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 응답에 나와야 하는 정책만 반환됩니다
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-counts-every-masking-policy-laid"></a>

#### [the-superadmin-counts-every-masking-policy-laid](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

대상이 다른 정책 둘이 있을 때 superadmin 이 필터 없이 조회하면 둘 다 집계됩니다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 응답에 나와야 하는 정책만 반환됩니다
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-masking-policies"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-masking-policies](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

superadmin 이 아닌 사용자가 전체를 조회하도록 요청하면 역할 부족으로 거부됩니다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-masking-policies"></a>

#### [a-user-granted-nothing-purges-none-of-several-masking-policies](/tests/scenario/bai_scenario/manager/client_ip_masking/test_partial_bulk_purging.py): pass

아무 권한도 없는 사용자가 정책 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.partial_bulk_purge: user-1 이 클라이언트 IP 마스킹 정책 2개를 한 번에 purge 합니다

Then

- 처리된 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-masking-policies-answers-for-the-missing-one"></a>

#### [purging-several-masking-policies-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/client_ip_masking/test_partial_bulk_purging.py): pass

superadmin 이 정책 둘과 없는 id 하나를 한 번에 purge 하면 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.partial_bulk_purge: user-1 이 클라이언트 IP 마스킹 정책 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 정책이 모두 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - id: 미리 저장한 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - id: 미리 저장한 정책와 같다
  - target_type = 'login_history'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### purge

<a id="retiring-the-superadmin-purges-a-masking-policy"></a>

#### [the-superadmin-purges-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

superadmin 이 정책을 id 로 삭제하면 삭제한 정책 전체를 담은 응답이 반환됩니다

Given

- 클라이언트 IP 마스킹 정책 하나와, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.purge: user-1 이 default 대상 정책를 삭제합니다

Then

- 삭제한 정책 전체가 반환됩니다
  - id: 미리 저장한 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="retiring-turning-enforcement-off-lets-a-user-purge-a-masking-policy"></a>

#### [turning-enforcement-off-lets-a-user-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 삭제할 수 있습니다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.purge: user-1 이 default 대상 정책를 삭제합니다

Then

- 삭제한 정책 전체가 반환됩니다
  - id: 미리 저장한 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="retiring-a-user-granted-nothing-may-not-purge-a-masking-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

아무 권한도 없는 사용자가 정책을 삭제하면 권한 부족으로 거부됩니다. 등록이 역할 부족으로 거부되는 것과는 다른 검사입니다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.purge: user-1 이 default 대상 정책를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

아무 권한도 없는 사용자가 존재하지 않는 id 를 삭제하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 row 에는 부여된 권한도 없기 때문입니다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.purge: user-1 이 존재하지 않는 id 를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-purging-a-masking-policy-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-masking-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 클라이언트 IP 마스킹 정책 하나와, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.purge: user-1 이 존재하지 않는 id 를 삭제합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### upsert

<a id="upserting-a-masking-policy-put-without-prefixes-carries-empty-prefixes"></a>

#### [a-masking-policy-put-without-prefixes-carries-empty-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

대상과 모드만 지정해 등록하면 두 접두 길이가 비어 있는 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 등록합니다

Then

- 등록한 정책 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-putting-a-policy-again-without-prefixes-clears-the-stored-prefixes"></a>

#### [putting-a-policy-again-without-prefixes-clears-the-stored-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

접두 길이가 있는 정책의 대상에 대상과 모드만 지정해 다시 등록하면 접두 길이가 비워집니다. 등록은 기존 값과 병합하지 않고 row 전체를 변경합니다

Given

- 클라이언트 IP 마스킹 정책 하나와, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 다시 등록합니다

Then

- 같은 id 의 행이 지정한 값으로 변경되어 반환됩니다
  - id: 미리 저장한 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row"></a>

#### [putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

이미 정책이 있는 대상에 다른 모드로 등록하면 새 row 가 아니라 같은 id 의 row 가 새 모드로 변경된 노드가 반환됩니다

Given

- 클라이언트 IP 마스킹 정책 하나와, superadmin 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 drop 모드 정책을 접두 길이와 함께 다시 등록합니다

Then

- 같은 id 의 행이 지정한 값으로 변경되어 반환됩니다
  - id: 미리 저장한 정책와 같다
  - target_type = 'default'
  - mode = 'drop'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-the-superadmin-puts-a-masking-policy-on-a-target"></a>

#### [the-superadmin-puts-a-masking-policy-on-a-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

정책이 없을 때 superadmin 이 대상, 모드, 두 접두 길이를 지정해 등록하면 지정한 값이 그대로 담긴 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 접두 길이와 함께 등록합니다

Then

- 등록한 정책 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

superadmin 이 아닌 사용자가 정책을 등록하면 역할 부족으로 거부됩니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 접두 길이와 함께 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="upserting-the-monitor-may-not-put-a-masking-policy"></a>

#### [the-monitor-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

모니터 역할이 정책을 등록하면 역할 부족으로 거부됩니다. 모니터는 superadmin 검사에서 읽기만 통과합니다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 접두 길이와 함께 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="upserting-turning-enforcement-off-does-not-let-a-user-put-a-masking-policy"></a>

#### [turning-enforcement-off-does-not-let-a-user-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

권한 검사를 꺼도 superadmin 이 아니면 정책을 등록하지 못합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ClientIPMaskingAdapter.upsert: user-1 이 default 대상에 truncate 모드 정책을 접두 길이와 함께 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

