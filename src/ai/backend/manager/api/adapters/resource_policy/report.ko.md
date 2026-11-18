## resource_policy

[배경](/src/ai/backend/manager/api/adapters/resource_policy/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_policy/adapter.py)

시나리오: 미완성 6 / 33

- ops 구성 (33)
  - admin_create_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_create_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_create_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_get_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_get_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_get_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_keypair_resource_policies: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_project_resource_policies: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_user_resource_policies: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_get_keypair_resource_policy_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_get_project_resource_policy_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_get_user_resource_policy_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_lookup_keypair_resource_policy_names: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_lookup_project_resource_policy_names: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_lookup_user_resource_policy_names: 대표 성공 ✓ · 대표 거부 ✓
  - get_my_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - get_my_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - get_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - lookup_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - lookup_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - lookup_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge_keypair_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_purge_project_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_purge_user_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update_keypair_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update_project_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update_user_resource_policies: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - purge_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - purge_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - update_keypair_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - update_project_resource_policy: 대표 성공 ✓ · 대표 거부 ✓
  - update_user_resource_policy: 대표 성공 ✓ · 대표 거부 ✓

**admin_create_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 한 자원의 전체 슬롯을 무제한으로 지정해 키페어 정책을 생성하면, 그 자원은 무제한으로 표시되고 수량은 비어 있습니다](#creating-an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited) | 성공 |
| [superadmin 이 생략할 수 있는 항목을 모두 생략하고 키페어 정책을 생성하면, 생략한 필드가 비어 있는 노드 전체가 반환됩니다](#creating-leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty) | 성공 |
| [superadmin 이 모든 값을 지정해 키페어 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다](#creating-the-superadmin-creates-a-keypair-policy-giving-every-value) | 성공 |
| [모니터 역할 사용자가 키페어 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다](#creating-a-monitor-may-not-create-a-keypair-policy) | 거부 |
| [이미 다른 키페어 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다](#creating-a-name-another-keypair-policy-already-holds-is-refused) | 거부 |
| [superadmin 이 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 생성하려 하면 제약 위반으로 거부됩니다](#creating-a-priority-cap-outside-the-session-range-is-refused) | 거부 |
| [superadmin 이 아닌 사용자가 키페어 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy) | 거부 |
| [권한 검사를 꺼도 키페어 정책 생성은 여전히 거부됩니다](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy) | 거부 |

**admin_create_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 모든 값을 지정해 프로젝트 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다](#creating-the-superadmin-creates-a-project-policy-giving-every-value) | 성공 |
| [모니터 역할 사용자가 프로젝트 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다](#creating-a-monitor-may-not-create-a-project-policy) | 거부 |
| [이미 다른 프로젝트 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다](#creating-a-name-another-project-policy-already-holds-is-refused) | 거부 |
| [superadmin 이 아닌 사용자가 프로젝트 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-project-policy) | 거부 |
| [권한 검사를 꺼도 프로젝트 정책 생성은 여전히 거부됩니다](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy) | 거부 |

**admin_create_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 생략할 수 있는 항목을 모두 생략하고 사용자 정책을 생성하면, 생략한 필드가 비어 있는 노드 전체가 반환됩니다](#creating-leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty) | 성공 |
| [superadmin 이 모든 값을 지정해 사용자 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다](#creating-the-superadmin-creates-a-user-policy-giving-every-value) | 성공 |
| [모니터 역할 사용자가 사용자 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다](#creating-a-monitor-may-not-create-a-user-policy) | 거부 |
| [이미 다른 사용자 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다](#creating-a-name-another-user-policy-already-holds-is-refused) | 거부 |
| [superadmin 이 아닌 사용자가 사용자 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-user-policy) | 거부 |
| [권한 검사를 꺼도 사용자 정책 생성은 여전히 거부됩니다](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy) | 거부 |

**admin_get_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [키페어 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다](#reading-the-superadmin-reads-a-keypair-policy-by-name) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 키페어 정책을 이름으로 조회할 수 있습니다](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy) | 성공 |
| [같은 키페어 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다](#reading-a-user-granted-nothing-cannot-resolve-a-keypair-policy-name) | 거부 |
| [superadmin 이 어느 키페어 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#reading-reading-a-keypair-policy-name-nothing-answers-to-is-not-found) | 거부 |

**admin_get_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다](#reading-the-superadmin-reads-a-project-policy-by-name) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 프로젝트 정책을 이름으로 조회할 수 있습니다](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy) | 성공 |
| [같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다](#reading-a-user-granted-nothing-cannot-resolve-a-project-policy-name) | 거부 |
| [superadmin 이 어느 프로젝트 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#reading-reading-a-project-policy-name-nothing-answers-to-is-not-found) | 거부 |

**admin_get_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [사용자 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다](#reading-the-superadmin-reads-a-user-policy-by-name) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 사용자 정책을 이름으로 조회할 수 있습니다](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy) | 성공 |
| [같은 사용자 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다](#reading-a-user-granted-nothing-cannot-resolve-a-user-policy-name) | 거부 |
| [superadmin 이 어느 사용자 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#reading-reading-a-user-policy-name-nothing-answers-to-is-not-found) | 거부 |

**admin_search_keypair_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [모니터 역할 사용자가 키페어 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다](#searching-a-monitor-finds-every-keypair-policy-like-the-superadmin) | 성공 |
| [키페어 정책 여럿이 있고 superadmin 이 특정 사용자의 키페어를 필터로 검색하면, 그 사용자의 키페어에 할당된 정책만 반환됩니다](#searching-filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds) | 성공 |
| [이름이 다른 키페어 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다](#searching-filtering-keypair-policy-search-by-name-leaves-that-one) | 성공 |
| [키페어 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다](#searching-the-superadmin-finds-every-keypair-policy) | 성공 |
| [superadmin 이 아닌 사용자가 키페어 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-keypair-policy) | 거부 |

**admin_search_project_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [모니터 역할 사용자가 프로젝트 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다](#searching-a-monitor-finds-every-project-policy-like-the-superadmin) | 성공 |
| [이름이 다른 프로젝트 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다](#searching-filtering-project-policy-search-by-name-leaves-that-one) | 성공 |
| [프로젝트 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다](#searching-the-superadmin-finds-every-project-policy) | 성공 |
| [superadmin 이 아닌 사용자가 프로젝트 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-project-policy) | 거부 |

**admin_search_user_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [모니터 역할 사용자가 사용자 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다](#searching-a-monitor-finds-every-user-policy-like-the-superadmin) | 성공 |
| [이름이 다른 사용자 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다](#searching-filtering-user-policy-search-by-name-leaves-that-one) | 성공 |
| [사용자 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다](#searching-the-superadmin-finds-every-user-policy) | 성공 |
| [superadmin 이 아닌 사용자가 사용자 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-user-policy) | 거부 |

**bulk_get_keypair_resource_policy_ids**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 키페어 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다](#bulk_reading-a-user-reading-policies-reads-a-keypair-policy-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다](#bulk_reading-a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item) | 거부 |

**bulk_get_project_resource_policy_ids**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 프로젝트 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다](#bulk_reading-a-user-reading-policies-reads-a-project-policy-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다](#bulk_reading-a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item) | 거부 |

**bulk_get_user_resource_policy_ids**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 사용자 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다](#bulk_reading-a-user-reading-policies-reads-a-user-policy-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다](#bulk_reading-a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item) | 거부 |

**bulk_lookup_keypair_resource_policy_names**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 키페어 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다](#looking_up-a-user-granted-nothing-looks-up-several-keypair-policy-names) | 성공 |
| [로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다](#looking_up-looking-up-several-keypair-policy-names-without-login-is-refused) | 거부 |

**bulk_lookup_project_resource_policy_names**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 프로젝트 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다](#looking_up-a-user-granted-nothing-looks-up-several-project-policy-names) | 성공 |
| [로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다](#looking_up-looking-up-several-project-policy-names-without-login-is-refused) | 거부 |

**bulk_lookup_user_resource_policy_names**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 사용자 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다](#looking_up-a-user-granted-nothing-looks-up-several-user-policy-names) | 성공 |
| [로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다](#looking_up-looking-up-several-user-policy-names-without-login-is-refused) | 거부 |

**get_my_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 키페어 정책을 읽을 권한을 받은 사용자가 자기 정책을 조회하면, 그 사용자에게 할당된 정책 전체가 반환됩니다](#reading_own-a-user-granted-read-in-their-own-scope-reads-their-keypair-policy) | 성공 |
| [기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 기본 키페어에 할당된 정책이 반환됩니다](#reading_own-among-several-keys-the-default-one-names-the-keypair-policy) | 성공 |
| [기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 그 활성 키페어에 할당된 정책이 반환됩니다](#reading_own-an-inactive-default-key-yields-to-the-active-one) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 자기 키페어 정책을 조회할 수 있습니다](#reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy) | 성공 |
| [아무 권한도 없는 사용자가 자기 키페어 정책을 조회하면 권한 부족으로 거부됩니다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사합니다](#reading_own-a-user-granted-nothing-may-not-read-their-own-keypair-policy) | 거부 |
| [활성 키페어가 없는 사용자가 자기 키페어 정책을 조회하면, 권한이 있어도 정책에 도달할 키페어가 없어 대상을 찾을 수 없다는 이유로 거부됩니다](#reading_own-a-user-with-no-active-key-finds-no-keypair-policy-of-their-own) | 거부 |

**get_my_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 사용자 정책을 읽을 권한을 받은 사용자가 자기 정책을 조회하면, 그 사용자에게 할당된 정책 전체가 반환됩니다](#reading_own-a-user-granted-read-in-their-own-scope-reads-their-user-policy) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 자기 사용자 정책을 조회할 수 있습니다](#reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy) | 성공 |
| [아무 권한도 없는 사용자가 자기 사용자 정책을 조회하면 권한 부족으로 거부됩니다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사합니다](#reading_own-a-user-granted-nothing-may-not-read-their-own-user-policy) | 거부 |

**get_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받은 사용자가 조회하면, 그 프로젝트가 따르는 정책 전체가 반환됩니다](#reading_project_policy-a-user-granted-read-in-the-project-reads-its-resource-policy) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트가 따르는 정책을 조회하면, 그 프로젝트 범위에 권한이 없으므로 거부됩니다](#reading_project_policy-a-user-granted-nothing-may-not-read-a-projects-resource-policy) | 거부 |

**lookup_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 키페어 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다](#looking_up-a-user-granted-read-looks-up-a-keypair-policy-by-name) | 성공 |
| [아무 권한도 받지 않은 사용자가 키페어 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다](#looking_up-a-user-granted-nothing-cannot-look-up-a-keypair-policy-name) | 거부 |
| [어느 키페어 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다](#looking_up-looking-up-a-keypair-policy-name-nothing-answers-to-is-refused) | 거부 |

**lookup_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 프로젝트 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다](#looking_up-a-user-granted-read-looks-up-a-project-policy-by-name) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다](#looking_up-a-user-granted-nothing-cannot-look-up-a-project-policy-name) | 거부 |
| [어느 프로젝트 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다](#looking_up-looking-up-a-project-policy-name-nothing-answers-to-is-refused) | 거부 |

**lookup_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [global 스코프에서 그 정책을 읽을 수 있는 사용자가 사용자 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다](#looking_up-a-user-granted-read-looks-up-a-user-policy-by-name) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다](#looking_up-a-user-granted-nothing-cannot-look-up-a-user-policy-name) | 거부 |
| [어느 사용자 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다](#looking_up-looking-up-a-user-policy-name-nothing-answers-to-is-refused) | 거부 |

**partial_bulk_purge_keypair_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 키페어 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-keypair-policys) | 성공 |
| [superadmin 이 아무도 사용하지 않는 키페어 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-keypair-policys-answers-for-the-missing-one) | 성공 |
| [superadmin 이 아직 할당된 키페어 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-keypair-policys-answers-for-the-one-still-held) | 성공 |

**partial_bulk_purge_project_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-project-policys) | 성공 |
| [superadmin 이 아무도 사용하지 않는 프로젝트 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-project-policys-answers-for-the-missing-one) | 성공 |
| [superadmin 이 아직 할당된 프로젝트 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-project-policys-answers-for-the-one-still-held) | 성공 |

**partial_bulk_purge_user_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 사용자 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-user-policys) | 성공 |
| [superadmin 이 아무도 사용하지 않는 사용자 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-user-policys-answers-for-the-missing-one) | 성공 |
| [superadmin 이 아직 할당된 사용자 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-user-policys-answers-for-the-one-still-held) | 성공 |

**partial_bulk_update_keypair_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 키페어 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-keypair-policys) | 성공 |
| [superadmin 이 키페어 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-keypair-policys-at-once) | 성공 |

**partial_bulk_update_project_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-project-policys) | 성공 |
| [superadmin 이 프로젝트 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-project-policys-at-once) | 성공 |

**partial_bulk_update_user_resource_policies**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 사용자 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-user-policys) | 성공 |
| [superadmin 이 사용자 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-user-policys-at-once) | 성공 |

**purge_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [아무도 사용하지 않는 키페어 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다](#retiring-the-superadmin-purges-a-keypair-policy-nobody-holds) | 성공 |
| [같은 키페어 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#retiring-a-user-granted-nothing-may-not-purge-a-keypair-policy) | 거부 |
| [superadmin 이 어느 키페어 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#retiring-purging-a-keypair-policy-name-nothing-answers-to-is-not-found) | 거부 |
| [아직 누군가에게 할당된 키페어 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다](#retiring-purging-a-keypair-policy-still-held-is-refused) | 거부 |

**purge_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [아무도 사용하지 않는 프로젝트 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다](#retiring-the-superadmin-purges-a-project-policy-nobody-holds) | 성공 |
| [같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#retiring-a-user-granted-nothing-may-not-purge-a-project-policy) | 거부 |
| [superadmin 이 어느 프로젝트 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#retiring-purging-a-project-policy-name-nothing-answers-to-is-not-found) | 거부 |
| [아직 누군가에게 할당된 프로젝트 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다](#retiring-purging-a-project-policy-still-held-is-refused) | 거부 |

**purge_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [아무도 사용하지 않는 사용자 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다](#retiring-the-superadmin-purges-a-user-policy-nobody-holds) | 성공 |
| [같은 사용자 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#retiring-a-user-granted-nothing-may-not-purge-a-user-policy) | 거부 |
| [superadmin 이 어느 사용자 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#retiring-purging-a-user-policy-name-nothing-answers-to-is-not-found) | 거부 |
| [아직 누군가에게 할당된 사용자 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다](#retiring-purging-a-user-policy-still-held-is-refused) | 거부 |

**update_keypair_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 키페어 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was) | 성공 |
| [비울 수 있는 항목에 값이 설정된 키페어 정책을 superadmin 이 그 항목을 비우도록 수정하면, 그 항목이 비어 있는 노드가 반환됩니다](#editing-clearing-a-nullable-value-of-a-keypair-policy-empties-it) | 성공 |
| [superadmin 이 키페어 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-giving-no-value-changes-nothing-of-a-keypair-policy) | 성공 |
| [키페어 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다](#editing-the-superadmin-changes-one-limit-of-a-keypair-policy) | 성공 |
| [같은 키페어 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-keypair-policy) | 거부 |
| [superadmin 이 어느 키페어 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#editing-editing-a-keypair-policy-name-nothing-answers-to-is-not-found) | 거부 |
| [superadmin 이 키페어 정책의 우선순위 상한을 세션 우선순위 범위 밖으로 수정하려 하면 제약 위반으로 거부됩니다](#editing-moving-the-priority-cap-outside-the-session-range-is-refused) | 거부 |

**update_project_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 프로젝트 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was) | 성공 |
| [superadmin 이 프로젝트 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-giving-no-value-changes-nothing-of-a-project-policy) | 성공 |
| [프로젝트 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다](#editing-the-superadmin-changes-one-limit-of-a-project-policy) | 성공 |
| [같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-project-policy) | 거부 |
| [superadmin 이 어느 프로젝트 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#editing-editing-a-project-policy-name-nothing-answers-to-is-not-found) | 거부 |

**update_user_resource_policy**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 사용자 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was) | 성공 |
| [비울 수 있는 항목에 값이 설정된 사용자 정책을 superadmin 이 그 항목을 비우도록 수정하면, 그 항목이 비어 있는 노드가 반환됩니다](#editing-clearing-a-nullable-value-of-a-user-policy-empties-it) | 성공 |
| [superadmin 이 사용자 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-giving-no-value-changes-nothing-of-a-user-policy) | 성공 |
| [사용자 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다](#editing-the-superadmin-changes-one-limit-of-a-user-policy) | 성공 |
| [같은 사용자 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-user-policy) | 거부 |
| [superadmin 이 어느 사용자 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#editing-editing-a-user-policy-name-nothing-answers-to-is-not-found) | 거부 |

### admin_create_keypair_resource_policy

<a id="creating-an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited"></a>

#### [an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 한 자원의 전체 슬롯을 무제한으로 지정해 키페어 정책을 생성하면, 그 자원은 무제한으로 표시되고 수량은 비어 있습니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 cpu 슬롯을 무제한으로 지정해 키페어 정책을 생성합니다

Then

- 생성한 키페어 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', None, True)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty"></a>

#### [leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 생략할 수 있는 항목을 모두 생략하고 키페어 정책을 생성하면, 생략한 필드가 비어 있는 노드 전체가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 대기 세션 수, 우선순위 상한, 대기 자원 슬롯을 생략하고 키페어 정책을 생성합니다

Then

- 생성한 키페어 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-the-superadmin-creates-a-keypair-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-keypair-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 모든 값을 지정해 키페어 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 모든 값을 지정해 키페어 정책을 생성합니다

Then

- 생성한 키페어 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-a-monitor-may-not-create-a-keypair-policy"></a>

#### [a-monitor-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

모니터 역할 사용자가 키페어 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 모든 값을 지정해 키페어 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-a-name-another-keypair-policy-already-holds-is-refused"></a>

#### [a-name-another-keypair-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

이미 다른 키페어 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 이미 있는 이름으로 키페어 정책을 생성합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="creating-a-priority-cap-outside-the-session-range-is-refused"></a>

#### [a-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 생성하려 하면 제약 위반으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 생성합니다

Then

- 거부됩니다
  - 거부: CheckConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 아닌 사용자가 키페어 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 모든 값을 지정해 키페어 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

권한 검사를 꺼도 키페어 정책 생성은 여전히 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1이 모든 값을 지정해 키페어 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_create_project_resource_policy

<a id="creating-the-superadmin-creates-a-project-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-project-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 모든 값을 지정해 프로젝트 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1이 모든 값을 지정해 프로젝트 정책을 생성합니다

Then

- 생성한 프로젝트 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_quota_scope_size = ('1073741824', '1g')
  - max_network_count = 5

<a id="creating-a-monitor-may-not-create-a-project-policy"></a>

#### [a-monitor-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

모니터 역할 사용자가 프로젝트 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1이 모든 값을 지정해 프로젝트 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-a-name-another-project-policy-already-holds-is-refused"></a>

#### [a-name-another-project-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

이미 다른 프로젝트 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1이 이미 있는 이름으로 프로젝트 정책을 생성합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-project-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 아닌 사용자가 프로젝트 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1이 모든 값을 지정해 프로젝트 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

권한 검사를 꺼도 프로젝트 정책 생성은 여전히 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1이 모든 값을 지정해 프로젝트 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_create_user_resource_policy

<a id="creating-leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty"></a>

#### [leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 생략할 수 있는 항목을 모두 생략하고 사용자 정책을 생성하면, 생략한 필드가 비어 있는 노드 전체가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 동시 로그인 수를 생략하고 사용자 정책을 생성합니다

Then

- 생성한 사용자 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_concurrent_logins = None
  - max_quota_scope_size = ('1073741824', '1g')
  - max_session_count_per_model_session = 4
  - max_customized_image_count = 2

<a id="creating-the-superadmin-creates-a-user-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-user-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 모든 값을 지정해 사용자 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 모든 값을 지정해 사용자 정책을 생성합니다

Then

- 생성한 사용자 정책 전체가 반환됩니다
  - id = 'fresh-policy'
  - entity_id: 건너뜀: the database generates it
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_concurrent_logins = 3
  - max_quota_scope_size = ('1073741824', '1g')
  - max_session_count_per_model_session = 4
  - max_customized_image_count = 2

<a id="creating-a-monitor-may-not-create-a-user-policy"></a>

#### [a-monitor-may-not-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

모니터 역할 사용자가 사용자 정책을 생성하려 하면 역할 부족으로 거부됩니다. superadmin 검사는 모니터에게 읽기만 허용합니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 모든 값을 지정해 사용자 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-a-name-another-user-policy-already-holds-is-refused"></a>

#### [a-name-another-user-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

이미 다른 사용자 정책이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 이미 있는 이름으로 사용자 정책을 생성합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-user-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

superadmin 이 아닌 사용자가 사용자 정책을 생성하려 하면 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 모든 값을 지정해 사용자 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

권한 검사를 꺼도 사용자 정책 생성은 여전히 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1이 모든 값을 지정해 사용자 정책을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_get_keypair_resource_policy

<a id="reading-the-superadmin-reads-a-keypair-policy-by-name"></a>

#### [the-superadmin-reads-a-keypair-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

키페어 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1이 keypair-policy-2 이름으로 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 키페어 정책을 이름으로 조회할 수 있습니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1이 keypair-policy-2 이름으로 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading-a-user-granted-nothing-cannot-resolve-a-keypair-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-keypair-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1이 keypair-policy-2 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="reading-reading-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

superadmin 이 어느 키페어 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1이 nobody 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### admin_get_project_resource_policy

<a id="reading-the-superadmin-reads-a-project-policy-by-name"></a>

#### [the-superadmin-reads-a-project-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

프로젝트 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1이 project-policy-1 이름으로 조회합니다

Then

- 미리 저장한 프로젝트 정책 전체가 반환됩니다
  - id = 'project-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 프로젝트 정책을 이름으로 조회할 수 있습니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1이 project-policy-1 이름으로 조회합니다

Then

- 미리 저장한 프로젝트 정책 전체가 반환됩니다
  - id = 'project-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading-a-user-granted-nothing-cannot-resolve-a-project-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-project-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1이 project-policy-1 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="reading-reading-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

superadmin 이 어느 프로젝트 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1이 nobody 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### admin_get_user_resource_policy

<a id="reading-the-superadmin-reads-a-user-policy-by-name"></a>

#### [the-superadmin-reads-a-user-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

사용자 정책 하나가 있고 superadmin 이 이름으로 조회하면, 그 정책 전체가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1이 user-policy-2 이름으로 조회합니다

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 사용자 정책을 이름으로 조회할 수 있습니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1이 user-policy-2 이름으로 조회합니다

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading-a-user-granted-nothing-cannot-resolve-a-user-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-user-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

같은 사용자 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1이 user-policy-2 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="reading-reading-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

superadmin 이 어느 사용자 정책에도 없는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1이 nobody 이름으로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### admin_search_keypair_resource_policies

<a id="searching-a-monitor-finds-every-keypair-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-keypair-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

모니터 역할 사용자가 키페어 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 키페어 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds"></a>

#### [filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

키페어 정책 여럿이 있고 superadmin 이 특정 사용자의 키페어를 필터로 검색하면, 그 사용자의 키페어에 할당된 정책만 반환됩니다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1이 자기 키페어 필터로 검색합니다

Then

- 호출자의 키페어에 할당된 키페어 정책 하나만 반환됩니다
  - items = ['keypair-policy-1']
  - total_count = 1

<a id="searching-filtering-keypair-policy-search-by-name-leaves-that-one"></a>

#### [filtering-keypair-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

이름이 다른 키페어 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1이 wanted-1 이름 필터로 검색합니다

Then

- 필터에 맞는 키페어 정책 하나만 반환됩니다
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-keypair-policy"></a>

#### [the-superadmin-finds-every-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

키페어 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 키페어 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-keypair-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

superadmin 이 아닌 사용자가 키페어 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_project_resource_policies

<a id="searching-a-monitor-finds-every-project-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-project-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

모니터 역할 사용자가 프로젝트 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다

Given

- 프로젝트 정책 3개와, 그중 하나가 할당된 monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 wanted-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 other-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 프로젝트 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-project-policy-search-by-name-leaves-that-one"></a>

#### [filtering-project-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

이름이 다른 프로젝트 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다

Given

- 프로젝트 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 wanted-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 other-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1이 wanted-1 이름 필터로 검색합니다

Then

- 필터에 맞는 프로젝트 정책 하나만 반환됩니다
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-project-policy"></a>

#### [the-superadmin-finds-every-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

프로젝트 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다

Given

- 프로젝트 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 wanted-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 other-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 프로젝트 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-project-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

superadmin 이 아닌 사용자가 프로젝트 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다

Given

- 프로젝트 정책 3개와, 그중 하나가 할당된 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 wanted-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 other-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_user_resource_policies

<a id="searching-a-monitor-finds-every-user-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-user-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

모니터 역할 사용자가 사용자 정책 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다

Given

- 사용자 정책 3개와, 그중 하나가 할당된 monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 wanted-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 other-1: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 사용자 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['other-1', 'user-policy-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-user-policy-search-by-name-leaves-that-one"></a>

#### [filtering-user-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

이름이 다른 사용자 정책 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환됩니다

Given

- 사용자 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 wanted-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 other-1: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1이 wanted-1 이름 필터로 검색합니다

Then

- 필터에 맞는 사용자 정책 하나만 반환됩니다
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-user-policy"></a>

#### [the-superadmin-finds-every-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

사용자 정책 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 모두, 그리고 그것만 반환됩니다

Given

- 사용자 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 wanted-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 other-1: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 미리 저장한 사용자 정책이 모두, 그리고 그것만 반환됩니다
  - items = ['other-1', 'user-policy-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-user-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

superadmin 이 아닌 사용자가 사용자 정책 전체를 검색하려 하면 역할 부족으로 거부됩니다

Given

- 사용자 정책 3개와, 그중 하나가 할당된 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 wanted-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 other-1: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1이 필터 없이 전체를 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### bulk_get_keypair_resource_policy_ids

<a id="bulk_reading-a-user-reading-policies-reads-a-keypair-policy-by-id"></a>

#### [a-user-reading-policies-reads-a-keypair-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 키페어 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - global 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.bulk_get_keypair_resource_policy_ids: user-1이 keypair-policy-2의 id 로 여럿을 읽습니다

Then

- 물은 항목에 미리 저장한 정책 전체가 응답으로 옵니다
  - len(items) = 1
  - items[0].id = 'keypair-policy-2'
  - items[0].entity_id: 미리 저장한 정책의 id 와 같다
  - items[0].name = 'keypair-policy-2'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - items[0].total_resource_slots = []
  - items[0].max_session_lifetime = 0
  - items[0].max_concurrent_sessions = 5
  - items[0].max_pending_session_count = None
  - items[0].max_priority = None
  - items[0].max_pending_session_resource_slots = None
  - items[0].max_concurrent_sftp_sessions = 1
  - items[0].max_containers_per_session = 1
  - items[0].idle_timeout = 3600
  - items[0].allowed_vfolder_hosts = []

<a id="bulk_reading-a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.bulk_get_keypair_resource_policy_ids: user-1이 keypair-policy-2의 id 로 여럿을 읽습니다

Then

- 물은 항목이 권한 부족으로 거부됩니다
  - 거부: NotEnoughPermission

### bulk_get_project_resource_policy_ids

<a id="bulk_reading-a-user-reading-policies-reads-a-project-policy-by-id"></a>

#### [a-user-reading-policies-reads-a-project-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 프로젝트 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지
  - global 스코프에서 project_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: project_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.bulk_get_project_resource_policy_ids: user-1이 project-policy-1의 id 로 여럿을 읽습니다

Then

- 물은 항목에 미리 저장한 정책 전체가 응답으로 옵니다
  - len(items) = 1
  - items[0].id = 'project-policy-1'
  - items[0].entity_id: 미리 저장한 정책의 id 와 같다
  - items[0].name = 'project-policy-1'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].max_vfolder_count = 10
  - items[0].max_quota_scope_size = ('-1', '-1')
  - items[0].max_network_count = 3

<a id="bulk_reading-a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_get_project_resource_policy_ids: user-1이 project-policy-1의 id 로 여럿을 읽습니다

Then

- 물은 항목이 권한 부족으로 거부됩니다
  - 거부: NotEnoughPermission

### bulk_get_user_resource_policy_ids

<a id="bulk_reading-a-user-reading-policies-reads-a-user-policy-by-id"></a>

#### [a-user-reading-policies-reads-a-user-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 id 로 사용자 정책 하나를 읽으면, 그 항목에 정책 전체가 응답으로 옵니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
  - global 스코프에서 user_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: user_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.bulk_get_user_resource_policy_ids: user-1이 user-policy-2의 id 로 여럿을 읽습니다

Then

- 물은 항목에 미리 저장한 정책 전체가 응답으로 옵니다
  - len(items) = 1
  - items[0].id = 'user-policy-2'
  - items[0].entity_id: 미리 저장한 정책의 id 와 같다
  - items[0].name = 'user-policy-2'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].max_vfolder_count = 10
  - items[0].max_concurrent_logins = None
  - items[0].max_quota_scope_size = ('-1', '-1')
  - items[0].max_session_count_per_model_session = 10
  - items[0].max_customized_image_count = 3

<a id="bulk_reading-a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 항목이 권한 부족으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_get_user_resource_policy_ids: user-1이 user-policy-2의 id 로 여럿을 읽습니다

Then

- 물은 항목이 권한 부족으로 거부됩니다
  - 거부: NotEnoughPermission

### bulk_lookup_keypair_resource_policy_names

<a id="looking_up-a-user-granted-nothing-looks-up-several-keypair-policy-names"></a>

#### [a-user-granted-nothing-looks-up-several-keypair-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 키페어 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.bulk_lookup_keypair_resource_policy_names: user-1이 keypair-policy-2과 nobody 의 id 를 여럿 조회합니다

Then

- 있는 이름의 항목에 그 정책의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다
  - [0]: 미리 저장한 정책의 id 와 같다
  - [1] = None

<a id="looking_up-looking-up-several-keypair-policy-names-without-login-is-refused"></a>

#### [looking-up-several-keypair-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.bulk_lookup_keypair_resource_policy_names: 로그인 문맥 없이 keypair-policy-2의 id 를 여럿 조회합니다

Then

- 거부됩니다
  - 거부: UserNotFound

### bulk_lookup_project_resource_policy_names

<a id="looking_up-a-user-granted-nothing-looks-up-several-project-policy-names"></a>

#### [a-user-granted-nothing-looks-up-several-project-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 프로젝트 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_lookup_project_resource_policy_names: user-1이 project-policy-1과 nobody 의 id 를 여럿 조회합니다

Then

- 있는 이름의 항목에 그 정책의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다
  - [0]: 미리 저장한 정책의 id 와 같다
  - [1] = None

<a id="looking_up-looking-up-several-project-policy-names-without-login-is-refused"></a>

#### [looking-up-several-project-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_lookup_project_resource_policy_names: 로그인 문맥 없이 project-policy-1의 id 를 여럿 조회합니다

Then

- 거부됩니다
  - 거부: UserNotFound

### bulk_lookup_user_resource_policy_names

<a id="looking_up-a-user-granted-nothing-looks-up-several-user-policy-names"></a>

#### [a-user-granted-nothing-looks-up-several-user-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 있는 이름과 없는 이름으로 사용자 정책 id 를 여럿 조회하면, 있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다. 이 호출은 인증만 봅니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_lookup_user_resource_policy_names: user-1이 user-policy-2과 nobody 의 id 를 여럿 조회합니다

Then

- 있는 이름의 항목에 그 정책의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다
  - [0]: 미리 저장한 정책의 id 와 같다
  - [1] = None

<a id="looking_up-looking-up-several-user-policy-names-without-login-is-refused"></a>

#### [looking-up-several-user-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.bulk_lookup_user_resource_policy_names: 로그인 문맥 없이 user-policy-2의 id 를 여럿 조회합니다

Then

- 거부됩니다
  - 거부: UserNotFound

### get_my_keypair_resource_policy

<a id="reading_own-a-user-granted-read-in-their-own-scope-reads-their-keypair-policy"></a>

#### [a-user-granted-read-in-their-own-scope-reads-their-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

자기 스코프에서 키페어 정책을 읽을 권한을 받은 사용자가 자기 정책을 조회하면, 그 사용자에게 할당된 정책 전체가 반환됩니다

Given

- 키페어 정책이 할당된 사용자 한 명, 자기 스코프에서 그 정책을 읽을 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-among-several-keys-the-default-one-names-the-keypair-policy"></a>

#### [among-several-keys-the-default-one-names-the-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 기본 키페어에 할당된 정책이 반환됩니다

Given

- 기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 other-1: 동시 세션 5개까지
  - 일반 사용자 user-1: other-1 정책이 할당된 활성 키페어 하나 더
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-an-inactive-default-key-yields-to-the-active-one"></a>

#### [an-inactive-default-key-yields-to-the-active-one](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 그 활성 키페어에 할당된 정책이 반환됩니다

Given

- 기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 other-1: 동시 세션 5개까지
  - 일반 사용자 user-1: other-1 정책이 할당된 활성 키페어 하나 더
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'other-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'other-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 자기 키페어 정책을 조회할 수 있습니다

Given

- 키페어 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-a-user-granted-nothing-may-not-read-their-own-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

아무 권한도 없는 사용자가 자기 키페어 정책을 조회하면 권한 부족으로 거부됩니다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사합니다

Given

- 키페어 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reading_own-a-user-with-no-active-key-finds-no-keypair-policy-of-their-own"></a>

#### [a-user-with-no-active-key-finds-no-keypair-policy-of-their-own](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

활성 키페어가 없는 사용자가 자기 키페어 정책을 조회하면, 권한이 있어도 정책에 도달할 키페어가 없어 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 활성 키페어가 없는 사용자, 자기 스코프에서 키페어 정책 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1이 자기 키페어 정책을 조회합니다

Then

- 거부됩니다
  - 거부: KeypairResourcePolicyNotFound

### get_my_user_resource_policy

<a id="reading_own-a-user-granted-read-in-their-own-scope-reads-their-user-policy"></a>

#### [a-user-granted-read-in-their-own-scope-reads-their-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

자기 스코프에서 사용자 정책을 읽을 권한을 받은 사용자가 자기 정책을 조회하면, 그 사용자에게 할당된 정책 전체가 반환됩니다

Given

- 사용자 정책이 할당된 사용자 한 명, 자기 스코프에서 그 정책을 읽을 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 스코프에서 user_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: user_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1이 자기 사용자 정책을 조회합니다

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 자기 사용자 정책을 조회할 수 있습니다

Given

- 사용자 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1이 자기 사용자 정책을 조회합니다

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading_own-a-user-granted-nothing-may-not-read-their-own-user-policy"></a>

#### [a-user-granted-nothing-may-not-read-their-own-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

아무 권한도 없는 사용자가 자기 사용자 정책을 조회하면 권한 부족으로 거부됩니다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사합니다

Given

- 사용자 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1이 자기 사용자 정책을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_project_resource_policy

<a id="reading_project_policy-a-user-granted-read-in-the-project-reads-its-resource-policy"></a>

#### [a-user-granted-read-in-the-project-reads-its-resource-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_project_policy.py): pass

그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받은 사용자가 조회하면, 그 프로젝트가 따르는 정책 전체가 반환됩니다

Given

- 프로젝트 하나와, 그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 policy-reader-1: project_resource_policy 전체에 READ 허용
  - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_project_resource_policy: user-1이 team-1 프로젝트의 정책을 읽습니다

Then

- 그 프로젝트가 따르는 프로젝트 정책 전체가 반환됩니다
  - id = 'default'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'default'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading_project_policy-a-user-granted-nothing-may-not-read-a-projects-resource-policy"></a>

#### [a-user-granted-nothing-may-not-read-a-projects-resource-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_project_policy.py): pass

아무 권한도 받지 않은 사용자가 프로젝트가 따르는 정책을 조회하면, 그 프로젝트 범위에 권한이 없으므로 거부됩니다

Given

- 프로젝트 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.get_project_resource_policy: user-1이 team-1 프로젝트의 정책을 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### lookup_keypair_resource_policy

<a id="looking_up-a-user-granted-read-looks-up-a-keypair-policy-by-name"></a>

#### [a-user-granted-read-looks-up-a-keypair-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 키페어 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - global 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_keypair_resource_policy: user-1이 keypair-policy-2의 id 를 찾습니다

Then

- 그 정책의 id 가 반환됩니다
  - id: 미리 저장한 정책의 id 와 같다

<a id="looking_up-a-user-granted-nothing-cannot-look-up-a-keypair-policy-name"></a>

#### [a-user-granted-nothing-cannot-look-up-a-keypair-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 키페어 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.lookup_keypair_resource_policy: user-1이 keypair-policy-2의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="looking_up-looking-up-a-keypair-policy-name-nothing-answers-to-is-refused"></a>

#### [looking-up-a-keypair-policy-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

어느 키페어 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - global 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_keypair_resource_policy: user-1이 nobody 의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### lookup_project_resource_policy

<a id="looking_up-a-user-granted-read-looks-up-a-project-policy-by-name"></a>

#### [a-user-granted-read-looks-up-a-project-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 프로젝트 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지
  - global 스코프에서 project_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: project_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_project_resource_policy: user-1이 project-policy-1의 id 를 찾습니다

Then

- 그 정책의 id 가 반환됩니다
  - id: 미리 저장한 정책의 id 와 같다

<a id="looking_up-a-user-granted-nothing-cannot-look-up-a-project-policy-name"></a>

#### [a-user-granted-nothing-cannot-look-up-a-project-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.lookup_project_resource_policy: user-1이 project-policy-1의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="looking_up-looking-up-a-project-policy-name-nothing-answers-to-is-refused"></a>

#### [looking-up-a-project-policy-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

어느 프로젝트 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지
  - global 스코프에서 project_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: project_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_project_resource_policy: user-1이 nobody 의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### lookup_user_resource_policy

<a id="looking_up-a-user-granted-read-looks-up-a-user-policy-by-name"></a>

#### [a-user-granted-read-looks-up-a-user-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

global 스코프에서 그 정책을 읽을 수 있는 사용자가 사용자 정책 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
  - global 스코프에서 user_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: user_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_user_resource_policy: user-1이 user-policy-2의 id 를 찾습니다

Then

- 그 정책의 id 가 반환됩니다
  - id: 미리 저장한 정책의 id 와 같다

<a id="looking_up-a-user-granted-nothing-cannot-look-up-a-user-policy-name"></a>

#### [a-user-granted-nothing-cannot-look-up-a-user-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 사용자 정책 이름으로 id 를 찾으면 그 정책을 읽을 권한이 없으므로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.lookup_user_resource_policy: user-1이 user-policy-2의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="looking_up-looking-up-a-user-policy-name-nothing-answers-to-is-refused"></a>

#### [looking-up-a-user-policy-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

어느 사용자 정책에도 없는 이름으로 id 를 찾으면 읽을 권한이 없을 때와 같은 거부가 오고, 그 이름이 있는지는 드러나지 않습니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, global 스코프에서 그 정책을 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
  - global 스코프에서 user_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 policy-reader-1: user_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.lookup_user_resource_policy: user-1이 nobody 의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### partial_bulk_purge_keypair_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-keypair-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-keypair-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 키페어 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 키페어 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 target-1: 동시 세션 5개까지
  - 키페어 정책 target-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1이 키페어 정책 2개를 한 번에 삭제합니다

Then

- 처리된 키페어 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-keypair-policys-answers-for-the-missing-one"></a>

#### [purging-several-keypair-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아무도 사용하지 않는 키페어 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 키페어 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 target-1: 동시 세션 5개까지
  - 키페어 정책 target-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1이 키페어 정책 2개 와 없는 id 하나를 한 번에 삭제합니다

Then

- 대상 키페어 정책이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 5
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[1].total_resource_slots = []
  - successes[1].max_session_lifetime = 0
  - successes[1].max_concurrent_sessions = 5
  - successes[1].max_pending_session_count = None
  - successes[1].max_priority = None
  - successes[1].max_pending_session_resource_slots = None
  - successes[1].max_concurrent_sftp_sessions = 1
  - successes[1].max_containers_per_session = 1
  - successes[1].idle_timeout = 3600
  - successes[1].allowed_vfolder_hosts = []
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-purging-several-keypair-policys-answers-for-the-one-still-held"></a>

#### [purging-several-keypair-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아직 할당된 키페어 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 키페어 정책 1개와, superadmin 한 명, 그 사용자에게 할당된 키페어 정책도 대상에 넣음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 target-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1이 키페어 정책 2개를 한 번에 삭제합니다

Then

- 아무도 사용하지 않는 키페어 정책은 처리된 목록에 오고, 아직 할당된 것은 참조 중이라는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 5
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - failed count = 1
  - failed[0].id: 호출자에게 할당된 정책의 id 와 같다
  - failed[0].message: 'Foreign key'를 담은 이유

### partial_bulk_purge_project_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-project-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-project-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 프로젝트 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 target-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 target-2: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1이 프로젝트 정책 2개를 한 번에 삭제합니다

Then

- 처리된 프로젝트 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-project-policys-answers-for-the-missing-one"></a>

#### [purging-several-project-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아무도 사용하지 않는 프로젝트 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 프로젝트 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 target-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 target-2: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1이 프로젝트 정책 2개 와 없는 id 하나를 한 번에 삭제합니다

Then

- 대상 프로젝트 정책이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 10
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].max_vfolder_count = 10
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_network_count = 3
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-purging-several-project-policys-answers-for-the-one-still-held"></a>

#### [purging-several-project-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아직 할당된 프로젝트 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 프로젝트 정책 1개와, superadmin 한 명, 그 사용자에게 할당된 프로젝트 정책도 대상에 넣음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 target-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1이 프로젝트 정책 2개를 한 번에 삭제합니다

Then

- 아무도 사용하지 않는 프로젝트 정책은 처리된 목록에 오고, 아직 할당된 것은 참조 중이라는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 10
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - failed count = 1
  - failed[0].id: 호출자에게 할당된 정책의 id 와 같다
  - failed[0].message: 'Foreign key'를 담은 이유

### partial_bulk_purge_user_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-user-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-user-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 사용자 정책 여럿을 한 번에 삭제하려 하면, 삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 사용자 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 target-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 target-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1이 사용자 정책 2개를 한 번에 삭제합니다

Then

- 처리된 사용자 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-user-policys-answers-for-the-missing-one"></a>

#### [purging-several-user-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아무도 사용하지 않는 사용자 정책 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 사용자 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 target-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 target-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1이 사용자 정책 2개 와 없는 id 하나를 한 번에 삭제합니다

Then

- 대상 사용자 정책이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 10
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].max_vfolder_count = 10
  - successes[1].max_concurrent_logins = None
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_session_count_per_model_session = 10
  - successes[1].max_customized_image_count = 3
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-purging-several-user-policys-answers-for-the-one-still-held"></a>

#### [purging-several-user-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

superadmin 이 아직 할당된 사용자 정책과 아무도 사용하지 않는 것을 한 번에 삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 사용자 정책 1개와, superadmin 한 명, 그 사용자에게 할당된 사용자 정책도 대상에 넣음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 target-1: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1이 사용자 정책 2개를 한 번에 삭제합니다

Then

- 아무도 사용하지 않는 사용자 정책은 처리된 목록에 오고, 아직 할당된 것은 참조 중이라는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 10
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - failed count = 1
  - failed[0].id: 호출자에게 할당된 정책의 id 와 같다
  - failed[0].message: 'Foreign key'를 담은 이유

### partial_bulk_update_keypair_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-keypair-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-keypair-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 키페어 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 키페어 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 target-1: 동시 세션 5개까지
  - 키페어 정책 target-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.partial_bulk_update_keypair_resource_policies: user-1이 키페어 정책 2개를 한 번에 수정합니다 (동시 세션 수 7 로 변경)

Then

- 처리된 키페어 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-keypair-policys-at-once"></a>

#### [the-superadmin-edits-several-keypair-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

superadmin 이 키페어 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다

Given

- 아무도 사용하지 않는 키페어 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 target-1: 동시 세션 5개까지
  - 키페어 정책 target-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.partial_bulk_update_keypair_resource_policies: user-1이 키페어 정책 2개를 한 번에 수정합니다 (동시 세션 수 7 로 변경)

Then

- 대상 키페어 정책이 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 7
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[1].total_resource_slots = []
  - successes[1].max_session_lifetime = 0
  - successes[1].max_concurrent_sessions = 7
  - successes[1].max_pending_session_count = None
  - successes[1].max_priority = None
  - successes[1].max_pending_session_resource_slots = None
  - successes[1].max_concurrent_sftp_sessions = 1
  - successes[1].max_containers_per_session = 1
  - successes[1].idle_timeout = 3600
  - successes[1].allowed_vfolder_hosts = []
  - failed = []

### partial_bulk_update_project_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-project-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-project-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 프로젝트 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 target-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 target-2: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_update_project_resource_policies: user-1이 프로젝트 정책 2개를 한 번에 수정합니다 (vfolder 수 20으로 변경)

Then

- 처리된 프로젝트 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-project-policys-at-once"></a>

#### [the-superadmin-edits-several-project-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

superadmin 이 프로젝트 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다

Given

- 아무도 사용하지 않는 프로젝트 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 target-1: 프로젝트 하나당 vfolder 10개까지
  - 프로젝트 자원 정책 target-2: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_update_project_resource_policies: user-1이 프로젝트 정책 2개를 한 번에 수정합니다 (vfolder 수 20으로 변경)

Then

- 대상 프로젝트 정책이 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 20
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].max_vfolder_count = 20
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_network_count = 3
  - failed = []

### partial_bulk_update_user_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-user-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-user-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 사용자 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아무도 사용하지 않는 사용자 정책 2개와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 target-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 target-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_update_user_resource_policies: user-1이 사용자 정책 2개를 한 번에 수정합니다 (vfolder 수 20으로 변경)

Then

- 처리된 사용자 정책 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 정책의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 정책의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-user-policys-at-once"></a>

#### [the-superadmin-edits-several-user-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

superadmin 이 사용자 정책 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 오고 실패한 것은 없습니다

Given

- 아무도 사용하지 않는 사용자 정책 2개와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 target-1: 사용자 한 명당 vfolder 10개까지
  - 사용자 자원 정책 target-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.partial_bulk_update_user_resource_policies: user-1이 사용자 정책 2개를 한 번에 수정합니다 (vfolder 수 20으로 변경)

Then

- 대상 사용자 정책이 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[0].name = 'target-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].max_vfolder_count = 20
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - successes[1].id = 'target-2'
  - successes[1].entity_id: 미리 저장한 정책의 id 와 같다
  - successes[1].name = 'target-2'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].max_vfolder_count = 20
  - successes[1].max_concurrent_logins = None
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_session_count_per_model_session = 10
  - successes[1].max_customized_image_count = 3
  - failed = []

### purge_keypair_resource_policy

<a id="retiring-the-superadmin-purges-a-keypair-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-keypair-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아무도 사용하지 않는 키페어 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1이 keypair-policy-2을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 삭제한 이름이 반환되고 다시 검색하면 없습니다
  - name = 'keypair-policy-2'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1이 keypair-policy-2을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="retiring-purging-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

superadmin 이 어느 키페어 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1이 nobody 을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="retiring-purging-a-keypair-policy-still-held-is-refused"></a>

#### [purging-a-keypair-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아직 누군가에게 할당된 키페어 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다

Given

- superadmin 한 명과, 그 사용자에게 아직 할당된 키페어 정책
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1이 keypair-policy-1을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: ForeignKeyViolationError

### purge_project_resource_policy

<a id="retiring-the-superadmin-purges-a-project-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-project-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아무도 사용하지 않는 프로젝트 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1이 project-policy-1을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 삭제한 이름이 반환되고 다시 검색하면 없습니다
  - name = 'project-policy-1'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-project-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1이 project-policy-1을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="retiring-purging-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

superadmin 이 어느 프로젝트 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1이 nobody 을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="retiring-purging-a-project-policy-still-held-is-refused"></a>

#### [purging-a-project-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아직 누군가에게 할당된 프로젝트 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다

Given

- superadmin 한 명과, 그 사용자에게 아직 할당된 프로젝트 정책
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1이 default 을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: ForeignKeyViolationError

### purge_user_resource_policy

<a id="retiring-the-superadmin-purges-a-user-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-user-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아무도 사용하지 않는 사용자 정책을 superadmin 이 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없습니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1이 user-policy-2을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 삭제한 이름이 반환되고 다시 검색하면 없습니다
  - name = 'user-policy-2'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-user-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

같은 사용자 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1이 user-policy-2을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="retiring-purging-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

superadmin 이 어느 사용자 정책에도 없는 이름을 삭제하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1이 nobody 을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="retiring-purging-a-user-policy-still-held-is-refused"></a>

#### [purging-a-user-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

아직 누군가에게 할당된 사용자 정책을 superadmin 이 삭제하려 하면, 아직 참조 중이라는 이유로 거부됩니다. 막는 것은 삭제 spec 이 아니라 외래 키입니다

Given

- superadmin 한 명과, 그 사용자에게 아직 할당된 사용자 정책
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1이 user-policy-1을 삭제한 뒤 같은 이름으로 다시 검색합니다

Then

- 거부됩니다
  - 거부: ForeignKeyViolationError

### update_keypair_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 키페어 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (동시 세션 수 비우기)

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-clearing-a-nullable-value-of-a-keypair-policy-empties-it"></a>

#### [clearing-a-nullable-value-of-a-keypair-policy-empties-it](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

비울 수 있는 항목에 값이 설정된 키페어 정책을 superadmin 이 그 항목을 비우도록 수정하면, 그 항목이 비어 있는 노드가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 그중 대기 2개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (대기 세션 수 비우기)

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-giving-no-value-changes-nothing-of-a-keypair-policy"></a>

#### [giving-no-value-changes-nothing-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 키페어 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (빈 요청)

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-the-superadmin-changes-one-limit-of-a-keypair-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

키페어 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (동시 세션 수 7 로 변경)

Then

- 미리 저장한 키페어 정책 전체가 반환됩니다
  - id = 'keypair-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 7
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-a-user-granted-nothing-may-not-edit-a-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (동시 세션 수 7 로 변경)

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="editing-editing-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 어느 키페어 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 nobody 을 수정합니다 (동시 세션 수 7 로 변경)

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="editing-moving-the-priority-cap-outside-the-session-range-is-refused"></a>

#### [moving-the-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 키페어 정책의 우선순위 상한을 세션 우선순위 범위 밖으로 수정하려 하면 제약 위반으로 거부됩니다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1이 keypair-policy-2을 수정합니다 (우선순위 상한을 세션 우선순위 범위 밖으로 변경)

Then

- 거부됩니다
  - 거부: CheckConstraintViolationError

### update_project_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 프로젝트 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1이 project-policy-1을 수정합니다 (vfolder 수 비우기)

Then

- 미리 저장한 프로젝트 정책 전체가 반환됩니다
  - id = 'project-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-giving-no-value-changes-nothing-of-a-project-policy"></a>

#### [giving-no-value-changes-nothing-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 프로젝트 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1이 project-policy-1을 수정합니다 (빈 요청)

Then

- 미리 저장한 프로젝트 정책 전체가 반환됩니다
  - id = 'project-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-the-superadmin-changes-one-limit-of-a-project-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

프로젝트 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1이 project-policy-1을 수정합니다 (vfolder 수 20으로 변경)

Then

- 미리 저장한 프로젝트 정책 전체가 반환됩니다
  - id = 'project-policy-1'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-a-user-granted-nothing-may-not-edit-a-project-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

같은 프로젝트 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1이 project-policy-1을 수정합니다 (vfolder 수 20으로 변경)

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="editing-editing-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 어느 프로젝트 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 자원 정책 project-policy-1: 프로젝트 하나당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1이 nobody 을 수정합니다 (vfolder 수 20으로 변경)

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### update_user_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 사용자 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 user-policy-2을 수정합니다 (vfolder 수 비우기)

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-clearing-a-nullable-value-of-a-user-policy-empties-it"></a>

#### [clearing-a-nullable-value-of-a-user-policy-empties-it](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

비울 수 있는 항목에 값이 설정된 사용자 정책을 superadmin 이 그 항목을 비우도록 수정하면, 그 항목이 비어 있는 노드가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지, 동시 로그인 3개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 user-policy-2을 수정합니다 (동시 로그인 수 비우기)

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-giving-no-value-changes-nothing-of-a-user-policy"></a>

#### [giving-no-value-changes-nothing-of-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 사용자 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 user-policy-2을 수정합니다 (빈 요청)

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-the-superadmin-changes-one-limit-of-a-user-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

사용자 정책 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 user-policy-2을 수정합니다 (vfolder 수 20으로 변경)

Then

- 미리 저장한 사용자 정책 전체가 반환됩니다
  - id = 'user-policy-2'
  - entity_id: 미리 저장한 정책의 id 와 같다
  - name = 'user-policy-2'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-a-user-granted-nothing-may-not-edit-a-user-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

같은 사용자 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 user-policy-2을 수정합니다 (vfolder 수 20으로 변경)

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="editing-editing-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

superadmin 이 어느 사용자 정책에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 아무도 사용하지 않는 사용자 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1이 nobody 을 수정합니다 (vfolder 수 20으로 변경)

Then

- 거부됩니다
  - 거부: EntityNotFoundError

