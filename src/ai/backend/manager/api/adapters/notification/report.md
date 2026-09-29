## notification

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/notification/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/notification/adapter.py)

시나리오: 미완 2 / 14

- ops 로 구성 (12)
  - batch_load_channels_by_ids — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_rules_by_ids — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - create_channel — 대표 성공 ✓ · 대표 실패 ✓
  - create_rule — 대표 성공 ✓ · 대표 실패 ✓
  - delete_channel — 대표 성공 ✓ · 대표 실패 ✓
  - delete_rule — 대표 성공 ✓ · 대표 실패 ✓
  - get_channel — 대표 성공 ✓ · 대표 실패 ✓
  - get_rule — 대표 성공 ✓ · 대표 실패 ✓
  - search_channels — 대표 성공 ✓ · 대표 실패 ✓
  - search_rules — 대표 성공 ✓ · 대표 실패 ✓
  - update_channel — 대표 성공 ✓ · 대표 실패 ✓
  - update_rule — 대표 성공 ✓ · 대표 실패 ✓
- 직접 구현 (2)
  - validate_channel — 성공 있음 1 · 실패 있음 2 (single_entity)
  - validate_rule — 성공 있음 1 · 실패 있음 3 (single_entity)

**batch_load_channels_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다](#reading_channels-a-batch-load-of-no-channel-ids-answers-an-empty-list) | 성공 |
| [아무 권한도 없는 사용자가 채널 둘을 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다](#reading_channels-a-user-granted-nothing-batch-loading-channels-is-refused-per-item) | 성공 |
| [슈퍼관리자가 미리 만들어 둔 채널 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다](#reading_channels-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |

**batch_load_rules_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다](#reading_rules-a-batch-load-of-no-rule-ids-answers-an-empty-list) | 성공 |
| [아무 권한도 없는 사용자가 규칙 둘을 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다](#reading_rules-a-user-granted-nothing-batch-loading-rules-is-refused-per-item) | 성공 |
| [슈퍼관리자가 미리 만들어 둔 규칙 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다](#reading_rules-the-superadmin-batch-load-leaves-a-missing-rule-id-empty) | 성공 |

**create_channel**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 비활성으로 지정해 채널을 만들면 비활성인 채널이 반환된다](#creating_channels-a-channel-made-disabled-answers-disabled) | 성공 |
| [슈퍼관리자가 이름과 주소만 주고 webhook 채널을 만들면, 활성 상태이고 설명이 비어 있는 채널 전체가 반환된다](#creating_channels-the-superadmin-makes-a-webhook-channel) | 성공 |
| [슈퍼관리자가 SMTP 접속과 보내는 사람, 받는 사람, 인증 계정을 주고 email 채널을 만들면, 인증 계정의 이름은 있고 비밀번호는 없는 채널 전체가 반환된다](#creating_channels-the-superadmin-makes-an-email-channel) | 성공 |
| [email 종류라고 하면서 webhook 명세를 주고 만들려 하면, 쓴 행을 읽어 돌려주는 자리에서 명세가 종류에 맞지 않아 거부되고 쓴 것은 되돌려진다](#creating_channels-a-channel-type-and-a-spec-that-disagree-are-refused) | 거부 |
| [webhook도 email도 주지 않은 명세로 만들려 하면 잘못된 입력으로 거부된다](#creating_channels-a-spec-naming-neither-webhook-nor-email-is-refused) | 거부 |
| [슈퍼관리자가 아닌 사용자가 채널을 만들려 하면 역할 부족으로 거부된다](#creating_channels-a-user-who-is-not-the-superadmin-may-not-make-a-channel) | 거부 |
| [모니터가 채널을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다](#creating_channels-the-monitor-may-not-make-a-channel) | 거부 |

**create_rule**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 비활성으로 지정해 규칙을 만들면 비활성인 규칙이 반환된다](#creating_rules-a-rule-made-disabled-answers-disabled) | 성공 |
| [어느 행에도 없는 채널 id를 가리켜 규칙을 만들면 막히지 않고 그대로 만들어진다. 두 테이블 사이에 외래 키가 없다](#creating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same) | 성공 |
| [슈퍼관리자가 종류와 채널과 템플릿을 주고 규칙을 만들면, 활성 상태이고 설명이 비어 있는 규칙 전체가 반환된다](#creating_rules-the-superadmin-makes-a-rule-through-a-channel) | 성공 |
| [슈퍼관리자가 아닌 사용자가 규칙을 만들려 하면 역할 부족으로 거부된다](#creating_rules-a-user-who-is-not-the-superadmin-may-not-make-a-rule) | 거부 |
| [모니터가 규칙을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다](#creating_rules-the-monitor-may-not-make-a-rule) | 거부 |

**delete_channel**

| 시나리오 | 판정 |
|---|---|
| [규칙이 가리키는 채널을 슈퍼관리자가 삭제하면 막히지 않고 삭제한 채널의 id가 반환된다. 두 테이블 사이에 외래 키가 없어 규칙은 남는다](#retiring_channels-a-channel-a-rule-points-at-is-deleted-all-the-same) | 성공 |
| [채널 하나가 있고 슈퍼관리자가 삭제하면 삭제한 채널의 id가 반환된다](#retiring_channels-the-superadmin-deletes-a-channel) | 성공 |
| [아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다](#retiring_channels-a-user-granted-nothing-may-not-delete-a-channel) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다](#retiring_channels-the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found) | 거부 |

**delete_rule**

| 시나리오 | 판정 |
|---|---|
| [규칙 하나가 있고 슈퍼관리자가 삭제하면 삭제한 규칙의 id가 반환된다](#retiring_rules-the-superadmin-deletes-a-rule) | 성공 |
| [아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다](#retiring_rules-a-user-granted-nothing-may-not-delete-a-rule) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다](#retiring_rules-the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found) | 거부 |

**get_channel**

| 시나리오 | 판정 |
|---|---|
| [채널 하나가 있고 슈퍼관리자가 id로 조회하면, 그 채널 전체가 반환된다](#reading_channels-the-superadmin-reads-a-channel-by-id) | 성공 |
| [아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다. 만든 사람으로 기록되어 있어도 같다](#reading_channels-a-user-granted-nothing-may-not-read-a-channel) | 거부 |
| [아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다](#reading_channels-a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission) | 거부 |
| [모니터가 id로 조회하면 권한 부족으로 거부된다. 검색은 통과하지만 id 조회는 권한 검사이고 모니터에게도 부여된 권한이 없다](#reading_channels-the-monitor-may-not-read-a-channel-by-id) | 거부 |
| [슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다](#reading_channels-the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found) | 거부 |

**get_rule**

| 시나리오 | 판정 |
|---|---|
| [규칙 하나가 있고 슈퍼관리자가 id로 조회하면, 그 규칙 전체가 반환된다](#reading_rules-the-superadmin-reads-a-rule-by-id) | 성공 |
| [아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다](#reading_rules-a-user-granted-nothing-may-not-read-a-rule) | 거부 |
| [슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다](#reading_rules-the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found) | 거부 |

**search_channels**

| 시나리오 | 판정 |
|---|---|
| [webhook 채널과 email 채널이 있을 때 email 종류를 필터로 조회하면 email 채널 하나만 반환된다](#searching_channels-a-channel-type-filter-narrows-the-answer-to-that-kind) | 성공 |
| [채널 둘 중 한쪽 이름을 필터로 조회하면 그 채널 하나만 반환된다](#searching_channels-a-name-filter-narrows-the-answer-to-that-channel) | 성공 |
| [활성 채널과 비활성 채널이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다](#searching_channels-an-enabled-filter-leaves-only-the-enabled-channels) | 성공 |
| [채널 둘이 있을 때 앞에서 한 건만 요청하면 한 건이 반환되고 다음 페이지가 있다고 응답한다](#searching_channels-asking-for-the-first-channel-only-says-there-is-a-next-page) | 성공 |
| [모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다](#searching_channels-the-monitor-searches-channels-like-the-superadmin) | 성공 |
| [채널 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다](#searching_channels-the-superadmin-counts-every-channel-laid) | 성공 |
| [슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다](#searching_channels-a-user-who-is-not-the-superadmin-may-not-search-channels) | 거부 |

**search_rules**

| 시나리오 | 판정 |
|---|---|
| [규칙 둘 중 한쪽 이름을 필터로 조회하면 그 규칙 하나만 반환된다](#searching_rules-a-name-filter-narrows-the-answer-to-that-rule) | 성공 |
| [종류가 다른 규칙 둘 중 한쪽 종류를 필터로 조회하면 그 규칙 하나만 반환된다](#searching_rules-a-rule-type-filter-narrows-the-answer-to-that-kind) | 성공 |
| [활성 규칙과 비활성 규칙이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다](#searching_rules-an-enabled-filter-leaves-only-the-enabled-rules) | 성공 |
| [모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다](#searching_rules-the-monitor-searches-rules-like-the-superadmin) | 성공 |
| [규칙 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다](#searching_rules-the-superadmin-counts-every-rule-laid) | 성공 |
| [슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다](#searching_rules-a-user-who-is-not-the-superadmin-may-not-search-rules) | 거부 |

**update_channel**

| 시나리오 | 판정 |
|---|---|
| [아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 채널이 반환된다](#editing_channels-an-edit-naming-no-field-changes-nothing) | 성공 |
| [webhook 채널의 명세를 다른 주소로 바꾸면 주소가 새 값인 채널이 반환된다](#editing_channels-changing-a-webhook-spec-moves-the-channel-to-the-new-url) | 성공 |
| [설명이 있는 채널의 설명을 비우면 설명이 비어 있는 채널이 반환된다](#editing_channels-clearing-a-channel-description-leaves-it-empty) | 성공 |
| [활성 채널을 비활성으로 바꾸면 비활성인 채널이 반환된다](#editing_channels-disabling-a-channel-answers-it-disabled) | 성공 |
| [슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 채널 전체가 반환된다](#editing_channels-the-superadmin-renaming-a-channel-leaves-the-rest) | 성공 |
| [아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다](#editing_channels-a-user-granted-nothing-may-not-edit-a-channel) | 거부 |
| [webhook도 email도 주지 않은 명세로 수정하려 하면 잘못된 입력으로 거부된다](#editing_channels-an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다](#editing_channels-the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found) | 거부 |

**update_rule**

| 시나리오 | 판정 |
|---|---|
| [아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 규칙이 반환된다](#editing_rules-a-rule-edit-naming-no-field-changes-nothing) | 성공 |
| [규칙의 템플릿을 바꾸면 템플릿이 새 값인 규칙이 반환된다](#editing_rules-changing-a-rule-template-answers-the-new-template) | 성공 |
| [설명이 있는 규칙의 설명을 비우면 설명이 비어 있는 규칙이 반환된다](#editing_rules-clearing-a-rule-description-leaves-it-empty) | 성공 |
| [활성 규칙을 비활성으로 바꾸면 비활성인 규칙이 반환된다](#editing_rules-disabling-a-rule-answers-it-disabled) | 성공 |
| [슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 규칙 전체가 반환된다](#editing_rules-the-superadmin-renaming-a-rule-leaves-the-rest) | 성공 |
| [아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다](#editing_rules-a-user-granted-nothing-may-not-edit-a-rule) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다](#editing_rules-the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found) | 거부 |

**validate_channel**

| 시나리오 | 판정 |
|---|---|
| [webhook 채널 하나가 있고 슈퍼관리자가 시험 메시지로 검증하면 검증한 채널의 id가 반환된다](#validating_channels-the-superadmin-validates-a-webhook-channel) | 성공 |
| [아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다](#validating_channels-a-user-granted-nothing-may-not-validate-a-channel) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다](#validating_channels-the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found) | 거부 |

**validate_rule**

| 시나리오 | 판정 |
|---|---|
| [세션 시작 규칙 하나가 있고 슈퍼관리자가 그 종류에 맞는 시험 데이터로 검증하면, 템플릿에 데이터를 넣어 만든 문자열이 반환된다](#validating_rules-the-superadmin-validates-a-rule-with-test-data) | 성공 |
| [없는 채널 id를 가리키는 규칙을 검증하면 채널을 찾을 수 없다는 이유로 거부된다](#validating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused) | 거부 |
| [아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다](#validating_rules-a-user-granted-nothing-may-not-validate-a-rule) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다](#validating_rules-the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found) | 거부 |

### batch_load_channels_by_ids

<a id="reading_channels-a-batch-load-of-no-channel-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-channel-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다

Given

- webhook 채널 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.batch_load_channels_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

<a id="reading_channels-a-user-granted-nothing-batch-loading-channels-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-channels-is-refused-per-item](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

아무 권한도 없는 사용자가 채널 둘을 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다

Given

- webhook 채널 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.batch_load_channels_by_ids — user-1이 미리 만들어 둔 2개를 한 번에 조회

Then

- 항목마다 권한 부족 거부가 담긴다
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

<a id="reading_channels-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

슈퍼관리자가 미리 만들어 둔 채널 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다

Given

- webhook 채널 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.batch_load_channels_by_ids — user-1이 미리 만들어 둔 2개와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로 반환되고, 없는 id에 해당하는 항목은 비어 있다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].name = 'wanted-1'
  - items[0].description = None
  - items[0].channel_type = 'webhook'
  - items[0].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - items[0].spec.url = 'https://hooks.example.test/notify'
  - items[0].enabled = True
  - items[0].created_by: 만든 사람와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].name = 'other-1'
  - items[1].description = None
  - items[1].channel_type = 'webhook'
  - items[1].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - items[1].spec.url = 'https://hooks.example.test/notify'
  - items[1].enabled = True
  - items[1].created_by: 만든 사람와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[2] = None

### batch_load_rules_by_ids

<a id="reading_rules-a-batch-load-of-no-rule-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-rule-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.batch_load_rules_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

<a id="reading_rules-a-user-granted-nothing-batch-loading-rules-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-rules-is-refused-per-item](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

아무 권한도 없는 사용자가 규칙 둘을 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.batch_load_rules_by_ids — user-1이 미리 만들어 둔 2개를 한 번에 조회

Then

- 항목마다 권한 부족 거부가 담긴다
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

<a id="reading_rules-the-superadmin-batch-load-leaves-a-missing-rule-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-rule-id-empty](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

슈퍼관리자가 미리 만들어 둔 규칙 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.batch_load_rules_by_ids — user-1이 미리 만들어 둔 2개와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로 반환되고, 없는 id에 해당하는 항목은 비어 있다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].name = 'wanted-1'
  - items[0].description = None
  - items[0].rule_type = 'session.started'
  - items[0].channel_id: 가리키는 채널와 같다
  - items[0].message_template = 'Session {{ session_name }} is {{ status }}'
  - items[0].enabled = True
  - items[0].created_by: 만든 사람와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].name = 'other-1'
  - items[1].description = None
  - items[1].rule_type = 'session.started'
  - items[1].channel_id: 가리키는 채널와 같다
  - items[1].message_template = 'Session {{ session_name }} is {{ status }}'
  - items[1].enabled = True
  - items[1].created_by: 만든 사람와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[2] = None

### create_channel

<a id="creating_channels-a-channel-made-disabled-answers-disabled"></a>

#### [a-channel-made-disabled-answers-disabled](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

슈퍼관리자가 비활성으로 지정해 채널을 만들면 비활성인 채널이 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 webhook 채널 muted을 생성

Then

- 생성한 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'muted'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = False
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_channels-the-superadmin-makes-a-webhook-channel"></a>

#### [the-superadmin-makes-a-webhook-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

슈퍼관리자가 이름과 주소만 주고 webhook 채널을 만들면, 활성 상태이고 설명이 비어 있는 채널 전체가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 webhook 채널 alerts을 생성

Then

- 생성한 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'alerts'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_channels-the-superadmin-makes-an-email-channel"></a>

#### [the-superadmin-makes-an-email-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

슈퍼관리자가 SMTP 접속과 보내는 사람, 받는 사람, 인증 계정을 주고 email 채널을 만들면, 인증 계정의 이름은 있고 비밀번호는 없는 채널 전체가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 email 채널 mail을 생성

Then

- 생성한 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'mail'
  - description = None
  - channel_type = 'email'
  - spec.channel_type = <NotificationChannelTypeDTO.EMAIL: 'email'>
  - spec.smtp.host = 'smtp.example.test'
  - spec.smtp.port = 587
  - spec.smtp.use_tls = True
  - spec.smtp.timeout = 30
  - spec.message.from_email = 'noreply@example.test'
  - spec.message.to_emails = ['ops@example.test']
  - spec.message.subject_template = None
  - spec.auth.username = 'mailer'
  - spec.auth.password: 무시함 — 응답 타입에 그 자리가 없다
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_channels-a-channel-type-and-a-spec-that-disagree-are-refused"></a>

#### [a-channel-type-and-a-spec-that-disagree-are-refused](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

email 종류라고 하면서 webhook 명세를 주고 만들려 하면, 쓴 행을 읽어 돌려주는 자리에서 명세가 종류에 맞지 않아 거부되고 쓴 것은 되돌려진다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 email 채널 mismatched을 생성

Then

- 거부된다
  - 거부: BackendAISchemaValidationFailed

<a id="creating_channels-a-spec-naming-neither-webhook-nor-email-is-refused"></a>

#### [a-spec-naming-neither-webhook-nor-email-is-refused](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

webhook도 email도 주지 않은 명세로 만들려 하면 잘못된 입력으로 거부된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 webhook 채널 empty을 생성

Then

- 거부된다
  - 거부: InvalidNotificationSpec

<a id="creating_channels-a-user-who-is-not-the-superadmin-may-not-make-a-channel"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

슈퍼관리자가 아닌 사용자가 채널을 만들려 하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 webhook 채널 by-a-user을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

<a id="creating_channels-the-monitor-may-not-make-a-channel"></a>

#### [the-monitor-may-not-make-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py) — pass

모니터가 채널을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- NotificationAdapter.create_channel — user-1이 webhook 채널 by-the-monitor을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### create_rule

<a id="creating_rules-a-rule-made-disabled-answers-disabled"></a>

#### [a-rule-made-disabled-answers-disabled](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py) — pass

슈퍼관리자가 비활성으로 지정해 규칙을 만들면 비활성인 규칙이 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.create_rule — user-1이 채널 channel-1를 가리키는 규칙 muted을 생성

Then

- 생성한 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'muted'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = False
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same"></a>

#### [a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py) — pass

어느 행에도 없는 채널 id를 가리켜 규칙을 만들면 막히지 않고 그대로 만들어진다. 두 테이블 사이에 외래 키가 없다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.create_rule — user-1이 없는 채널 id를 가리키는 규칙 orphan을 생성

Then

- 생성한 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'orphan'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_rules-the-superadmin-makes-a-rule-through-a-channel"></a>

#### [the-superadmin-makes-a-rule-through-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py) — pass

슈퍼관리자가 종류와 채널과 템플릿을 주고 규칙을 만들면, 활성 상태이고 설명이 비어 있는 규칙 전체가 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.create_rule — user-1이 채널 channel-1를 가리키는 규칙 on-start을 생성

Then

- 생성한 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'on-start'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating_rules-a-user-who-is-not-the-superadmin-may-not-make-a-rule"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-a-rule](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py) — pass

슈퍼관리자가 아닌 사용자가 규칙을 만들려 하면 역할 부족으로 거부된다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.create_rule — user-1이 채널 channel-1를 가리키는 규칙 by-a-user을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

<a id="creating_rules-the-monitor-may-not-make-a-rule"></a>

#### [the-monitor-may-not-make-a-rule](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py) — pass

모니터가 규칙을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다

Given

- webhook 채널 하나와, 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.create_rule — user-1이 채널 channel-1를 가리키는 규칙 by-the-monitor을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### delete_channel

<a id="retiring_channels-a-channel-a-rule-points-at-is-deleted-all-the-same"></a>

#### [a-channel-a-rule-points-at-is-deleted-all-the-same](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py) — pass

규칙이 가리키는 채널을 슈퍼관리자가 삭제하면 막히지 않고 삭제한 채널의 id가 반환된다. 두 테이블 사이에 외래 키가 없어 규칙은 남는다

Given

- 채널 하나와 그것을 가리키는 규칙 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.delete_channel — user-1이 채널 channel-1 삭제

Then

- 삭제한 채널의 id가 반환된다
  - id: 미리 만들어 둔 채널와 같다

<a id="retiring_channels-the-superadmin-deletes-a-channel"></a>

#### [the-superadmin-deletes-a-channel](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py) — pass

채널 하나가 있고 슈퍼관리자가 삭제하면 삭제한 채널의 id가 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.delete_channel — user-1이 채널 channel-1 삭제

Then

- 삭제한 채널의 id가 반환된다
  - id: 미리 만들어 둔 채널와 같다

<a id="retiring_channels-a-user-granted-nothing-may-not-delete-a-channel"></a>

#### [a-user-granted-nothing-may-not-delete-a-channel](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py) — pass

아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.delete_channel — user-1이 채널 channel-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="retiring_channels-the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.delete_channel — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

### delete_rule

<a id="retiring_rules-the-superadmin-deletes-a-rule"></a>

#### [the-superadmin-deletes-a-rule](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py) — pass

규칙 하나가 있고 슈퍼관리자가 삭제하면 삭제한 규칙의 id가 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.delete_rule — user-1이 규칙 rule-1 삭제

Then

- 삭제한 규칙의 id가 반환된다
  - id: 미리 만들어 둔 규칙와 같다

<a id="retiring_rules-a-user-granted-nothing-may-not-delete-a-rule"></a>

#### [a-user-granted-nothing-may-not-delete-a-rule](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py) — pass

아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.delete_rule — user-1이 규칙 rule-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="retiring_rules-the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.delete_rule — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

### get_channel

<a id="reading_channels-the-superadmin-reads-a-channel-by-id"></a>

#### [the-superadmin-reads-a-channel-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

채널 하나가 있고 슈퍼관리자가 id로 조회하면, 그 채널 전체가 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.get_channel — user-1이 채널 channel-1 조회

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading_channels-a-user-granted-nothing-may-not-read-a-channel"></a>

#### [a-user-granted-nothing-may-not-read-a-channel](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다. 만든 사람으로 기록되어 있어도 같다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.get_channel — user-1이 채널 channel-1 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reading_channels-a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.get_channel — user-1이 존재하지 않는 id 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reading_channels-the-monitor-may-not-read-a-channel-by-id"></a>

#### [the-monitor-may-not-read-a-channel-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

모니터가 id로 조회하면 권한 부족으로 거부된다. 검색은 통과하지만 id 조회는 권한 검사이고 모니터에게도 부여된 권한이 없다

Given

- webhook 채널 하나와, 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.get_channel — user-1이 채널 channel-1 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reading_channels-the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py) — pass

슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.get_channel — user-1이 존재하지 않는 id 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### get_rule

<a id="reading_rules-the-superadmin-reads-a-rule-by-id"></a>

#### [the-superadmin-reads-a-rule-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

규칙 하나가 있고 슈퍼관리자가 id로 조회하면, 그 규칙 전체가 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.get_rule — user-1이 규칙 rule-1 조회

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading_rules-a-user-granted-nothing-may-not-read-a-rule"></a>

#### [a-user-granted-nothing-may-not-read-a-rule](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.get_rule — user-1이 규칙 rule-1 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reading_rules-the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py) — pass

슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.get_rule — user-1이 존재하지 않는 id 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### search_channels

<a id="searching_channels-a-channel-type-filter-narrows-the-answer-to-that-kind"></a>

#### [a-channel-type-filter-narrows-the-answer-to-that-kind](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

webhook 채널과 email 채널이 있을 때 email 종류를 필터로 조회하면 email 채널 하나만 반환된다

Given

- webhook 채널 하나와 email 채널 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - email 채널 mail-channel-1: smtp.example.test를 거쳐 ops@example.test에게 보낸다

When

- NotificationAdapter.search_channels — user-1이 email 종류 필터로 조회

Then

- 필터에 맞는 채널 하나만 반환된다
  - items = ['mail-channel-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-a-name-filter-narrows-the-answer-to-that-channel"></a>

#### [a-name-filter-narrows-the-answer-to-that-channel](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

채널 둘 중 한쪽 이름을 필터로 조회하면 그 채널 하나만 반환된다

Given

- webhook 채널 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.search_channels — user-1이 이름 wanted-1 필터로 조회

Then

- 필터에 맞는 채널 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-an-enabled-filter-leaves-only-the-enabled-channels"></a>

#### [an-enabled-filter-leaves-only-the-enabled-channels](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

활성 채널과 비활성 채널이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다

Given

- 활성 webhook 채널 하나와 비활성 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 channel-2: https://hooks.example.test/notify로 보낸다, 비활성

When

- NotificationAdapter.search_channels — user-1이 활성 필터로 조회

Then

- 응답에 나와야 하는 채널만 반환된다
  - items = ['channel-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-asking-for-the-first-channel-only-says-there-is-a-next-page"></a>

#### [asking-for-the-first-channel-only-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

채널 둘이 있을 때 앞에서 한 건만 요청하면 한 건이 반환되고 다음 페이지가 있다고 응답한다

Given

- webhook 채널 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.search_channels — user-1이 앞에서 한 건만 조회

Then

- 한 건짜리 첫 페이지가 반환된다
  - len(items) = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching_channels-the-monitor-searches-channels-like-the-superadmin"></a>

#### [the-monitor-searches-channels-like-the-superadmin](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다

Given

- webhook 채널 둘과, 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.search_channels — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 채널만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-the-superadmin-counts-every-channel-laid"></a>

#### [the-superadmin-counts-every-channel-laid](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

채널 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다

Given

- webhook 채널 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.search_channels — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 채널만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-a-user-who-is-not-the-superadmin-may-not-search-channels"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-channels](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py) — pass

슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다

Given

- webhook 채널 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 wanted-1: https://hooks.example.test/notify로 보낸다
  - webhook 채널 other-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.search_channels — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### search_rules

<a id="searching_rules-a-name-filter-narrows-the-answer-to-that-rule"></a>

#### [a-name-filter-narrows-the-answer-to-that-rule](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

규칙 둘 중 한쪽 이름을 필터로 조회하면 그 규칙 하나만 반환된다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.search_rules — user-1이 이름 wanted-1 필터로 조회

Then

- 필터에 맞는 규칙 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-a-rule-type-filter-narrows-the-answer-to-that-kind"></a>

#### [a-rule-type-filter-narrows-the-answer-to-that-kind](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

종류가 다른 규칙 둘 중 한쪽 종류를 필터로 조회하면 그 규칙 하나만 반환된다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.terminated 이벤트를 알린다

When

- NotificationAdapter.search_rules — user-1이 종류 session.started 필터로 조회

Then

- 필터에 맞는 규칙 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-an-enabled-filter-leaves-only-the-enabled-rules"></a>

#### [an-enabled-filter-leaves-only-the-enabled-rules](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

활성 규칙과 비활성 규칙이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다

Given

- 활성 규칙 하나와 비활성 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다
  - 규칙 rule-2: session.started 이벤트를 알린다, 비활성

When

- NotificationAdapter.search_rules — user-1이 활성 필터로 조회

Then

- 응답에 나와야 하는 규칙만 반환된다
  - items = ['rule-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-the-monitor-searches-rules-like-the-superadmin"></a>

#### [the-monitor-searches-rules-like-the-superadmin](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.search_rules — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 규칙만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-the-superadmin-counts-every-rule-laid"></a>

#### [the-superadmin-counts-every-rule-laid](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

규칙 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.search_rules — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 규칙만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-a-user-who-is-not-the-superadmin-may-not-search-rules"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-rules](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py) — pass

슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다

Given

- 같은 webhook 채널을 가리키는 규칙 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 wanted-1: session.started 이벤트를 알린다
  - 규칙 other-1: session.started 이벤트를 알린다

When

- NotificationAdapter.search_rules — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### update_channel

<a id="editing_channels-an-edit-naming-no-field-changes-nothing"></a>

#### [an-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 채널이 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 아무것도 지정하지 않고 수정

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_channels-changing-a-webhook-spec-moves-the-channel-to-the-new-url"></a>

#### [changing-a-webhook-spec-moves-the-channel-to-the-new-url](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

webhook 채널의 명세를 다른 주소로 바꾸면 주소가 새 값인 채널이 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 주소를 https://hooks.example.test/elsewhere로 수정

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/elsewhere'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_channels-clearing-a-channel-description-leaves-it-empty"></a>

#### [clearing-a-channel-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

설명이 있는 채널의 설명을 비우면 설명이 비어 있는 채널이 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 설명을 비움 수정

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_channels-disabling-a-channel-answers-it-disabled"></a>

#### [disabling-a-channel-answers-it-disabled](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

활성 채널을 비활성으로 바꾸면 비활성인 채널이 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 활성을 False로 수정

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = False
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_channels-the-superadmin-renaming-a-channel-leaves-the-rest"></a>

#### [the-superadmin-renaming-a-channel-leaves-the-rest](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 채널 전체가 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 이름을 renamed으로 수정

Then

- 미리 만들어 둔 채널 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_channels-a-user-granted-nothing-may-not-edit-a-channel"></a>

#### [a-user-granted-nothing-may-not-edit-a-channel](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 이름을 by-a-user으로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing_channels-an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused"></a>

#### [an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

webhook도 email도 주지 않은 명세로 수정하려 하면 잘못된 입력으로 거부된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 채널 channel-1을 빈 명세로 수정

Then

- 거부된다
  - 거부: InvalidNotificationSpec

<a id="editing_channels-the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py) — pass

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.update_channel — user-1이 존재하지 않는 id을 이름을 nowhere으로 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

### update_rule

<a id="editing_rules-a-rule-edit-naming-no-field-changes-nothing"></a>

#### [a-rule-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 규칙이 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 아무것도 지정하지 않고 수정

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_rules-changing-a-rule-template-answers-the-new-template"></a>

#### [changing-a-rule-template-answers-the-new-template](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

규칙의 템플릿을 바꾸면 템플릿이 새 값인 규칙이 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 템플릿을 새것으로 수정

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = '{{ session_id }} started'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_rules-clearing-a-rule-description-leaves-it-empty"></a>

#### [clearing-a-rule-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

설명이 있는 규칙의 설명을 비우면 설명이 비어 있는 규칙이 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 설명을 비움 수정

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_rules-disabling-a-rule-answers-it-disabled"></a>

#### [disabling-a-rule-answers-it-disabled](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

활성 규칙을 비활성으로 바꾸면 비활성인 규칙이 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 활성을 False로 수정

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = False
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_rules-the-superadmin-renaming-a-rule-leaves-the-rest"></a>

#### [the-superadmin-renaming-a-rule-leaves-the-rest](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 규칙 전체가 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 이름을 renamed으로 수정

Then

- 미리 만들어 둔 규칙 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = None
  - rule_type = 'session.started'
  - channel_id: 가리키는 채널와 같다
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: 만든 사람와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing_rules-a-user-granted-nothing-may-not-edit-a-rule"></a>

#### [a-user-granted-nothing-may-not-edit-a-rule](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 규칙 rule-1을 이름을 by-a-user으로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing_rules-the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py) — pass

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.update_rule — user-1이 존재하지 않는 id을 이름을 nowhere으로 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

### validate_channel

<a id="validating_channels-the-superadmin-validates-a-webhook-channel"></a>

#### [the-superadmin-validates-a-webhook-channel](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py) — pass

webhook 채널 하나가 있고 슈퍼관리자가 시험 메시지로 검증하면 검증한 채널의 id가 반환된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.validate_channel — user-1이 채널 channel-1을 시험 메시지로 검증

Then

- 검증한 채널의 id가 반환된다
  - id: 미리 만들어 둔 채널와 같다

<a id="validating_channels-a-user-granted-nothing-may-not-validate-a-channel"></a>

#### [a-user-granted-nothing-may-not-validate-a-channel](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py) — pass

아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다

Given

- webhook 채널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.validate_channel — user-1이 채널 channel-1을 시험 메시지로 검증

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="validating_channels-the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py) — pass

슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- webhook 채널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다

When

- NotificationAdapter.validate_channel — user-1이 존재하지 않는 id을 시험 메시지로 검증

Then

- 거부된다
  - 거부: NotificationChannelNotFound

### validate_rule

<a id="validating_rules-the-superadmin-validates-a-rule-with-test-data"></a>

#### [the-superadmin-validates-a-rule-with-test-data](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py) — pass

세션 시작 규칙 하나가 있고 슈퍼관리자가 그 종류에 맞는 시험 데이터로 검증하면, 템플릿에 데이터를 넣어 만든 문자열이 반환된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.validate_rule — user-1이 규칙 rule-1을 시험 데이터로 검증

Then

- 템플릿에 데이터를 넣어 만든 문자열이 반환된다
  - message = 'Session train is running'

<a id="validating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused"></a>

#### [a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py) — pass

없는 채널 id를 가리키는 규칙을 검증하면 채널을 찾을 수 없다는 이유로 거부된다

Given

- 없는 채널 id를 가리키는 규칙 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 orphan-rule-1: 없는 채널 id를 가리킨다

When

- NotificationAdapter.validate_rule — user-1이 규칙 orphan-rule-1을 시험 데이터로 검증

Then

- 거부된다
  - 거부: NotificationChannelNotFound

<a id="validating_rules-a-user-granted-nothing-may-not-validate-a-rule"></a>

#### [a-user-granted-nothing-may-not-validate-a-rule](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py) — pass

아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.validate_rule — user-1이 규칙 rule-1을 시험 데이터로 검증

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="validating_rules-the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py) — pass

슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 규칙 하나와 그것이 가리키는 webhook 채널, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - webhook 채널 channel-1: https://hooks.example.test/notify로 보낸다
  - 규칙 rule-1: session.started 이벤트를 알린다

When

- NotificationAdapter.validate_rule — user-1이 존재하지 않는 id을 시험 데이터로 검증

Then

- 거부된다
  - 거부: NotificationRuleNotFound

