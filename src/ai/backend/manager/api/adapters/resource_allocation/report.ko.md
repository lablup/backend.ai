## resource_allocation

[어댑터](/src/ai/backend/manager/api/adapters/resource_allocation/adapter.py)

시나리오: 미완성 2 / 12

- 직접 구현 (12)
  - admin_domain_usage: 성공 있음 1 · 거부 있음 1 (single_entity)
  - admin_effective_allocation: 성공 없음 · 거부 없음 (scope): SCENARIO-GAP
  - admin_effective_allocation_resolved: 성공 없음 · 거부 없음 (scope, single_entity): SCENARIO-GAP
  - check_preset_availability: 성공 있음 1 · 거부 있음 1 (scope)
  - check_preset_availability_for_current_user: 성공 있음 1 · 거부 있음 1 (scope, single_entity)
  - effective_allocation: 성공 있음 3 · 거부 있음 1 (scope)
  - effective_allocation_for_current_user: 성공 있음 1 · 거부 있음 1 (scope, single_entity)
  - my_concurrency: 성공 있음 1 · 거부 있음 1 (single_entity)
  - my_keypair_usage: 성공 있음 1 · 거부 있음 1 (single_entity)
  - my_user_usage: 성공 있음 1 · 거부 있음 1 (single_entity)
  - project_usage: 성공 있음 1 · 거부 있음 1 (single_entity)
  - resource_group_usage: 성공 있음 1 · 거부 있음 1 (global_scope)

**admin_domain_usage**

| 시나리오 | 판정 |
|---|---|
| [도메인 범위에서 도메인을 읽을 수 있는 사용자가 그 도메인의 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다](#usage-a-user-reading-the-domain-reads-its-usage) | 성공 |
| [없는 이름으로 도메인 사용량을 읽으면 대상이 없다는 것으로 거부됩니다](#usage-reading-the-usage-of-a-domain-nothing-answers-to-is-not-found) | 거부 |

**check_preset_availability**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 범위에서 리소스 프리셋을 읽을 수 있는 사용자가 주어진 접근 키와 정책으로 프리셋 가용성을 확인하면, 미리 저장한 프리셋이 모두 쓸 수 있는 것으로 반환됩니다](#checking_presets-a-user-reading-presets-checks-available-presets-with-a-given-key) | 성공 |
| [아무 권한도 받지 않은 사용자가 주어진 키로 프리셋 가용성을 확인하려 하면 권한 부족으로 거부됩니다](#checking_presets-a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key) | 거부 |

**check_preset_availability_for_current_user**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 범위에서 리소스 프리셋을 읽고 자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 키페어로 프리셋 가용성을 확인하면, 미리 저장한 프리셋이 모두 쓸 수 있는 것으로 반환됩니다](#checking_presets-a-user-reading-presets-checks-available-presets-for-themselves) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋 가용성을 확인하려 하면 권한 부족으로 거부됩니다](#checking_presets-a-user-granted-nothing-may-not-check-preset-availability) | 거부 |

**effective_allocation**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 범위에서 세션을 읽을 수 있는 사용자가 유효 할당을 읽으면, 기본 설정에서는 프로젝트 범위가 담기지 않고 자원 그룹 범위가 담깁니다](#effective_allocation-a-user-reading-sessions-reads-the-effective-allocation) | 성공 |
| [에이전트를 숨기면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에서 자원 그룹 범위가 빠집니다](#effective_allocation-hiding-agents-drops-the-resource-group-scope) | 성공 |
| [자원 그룹 가시성을 켜면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에 프로젝트 범위가 담깁니다](#effective_allocation-turning-group-resource-visibility-on-shows-the-project-scope) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트의 유효 할당을 읽으려 하면 권한 부족으로 거부됩니다](#effective_allocation-a-user-granted-nothing-may-not-read-the-effective-allocation) | 거부 |

**effective_allocation_for_current_user**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 범위에서 세션을 읽고 자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 유효 할당을 읽으면, 기본 설정에서는 자원 그룹 범위만 담겨 반환됩니다](#effective_allocation-a-user-reading-sessions-reads-their-own-effective-allocation) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 유효 할당을 읽으려 하면 권한 부족으로 거부됩니다](#effective_allocation-a-user-granted-nothing-may-not-read-their-own-effective-allocation) | 거부 |

**my_concurrency**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 동시 세션 수를 읽으면, 세션이 없으므로 모두 0 이 반환됩니다](#usage-a-user-reading-their-own-user-reads-their-concurrency) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 동시 세션 수를 읽으려 하면 권한 부족으로 거부됩니다](#usage-a-user-granted-nothing-may-not-read-their-own-concurrency) | 거부 |

**my_keypair_usage**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 기본 키페어 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다](#usage-a-user-reading-their-own-user-reads-their-keypair-usage) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 키페어 사용량을 읽으려 하면 권한 부족으로 거부됩니다](#usage-a-user-granted-nothing-may-not-read-their-own-keypair-usage) | 거부 |

**my_user_usage**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다](#usage-a-user-reading-their-own-user-reads-their-user-usage) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 사용량을 읽으려 하면 권한 부족으로 거부됩니다](#usage-a-user-granted-nothing-may-not-read-their-own-user-usage) | 거부 |

**project_usage**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 범위에서 프로젝트를 읽을 수 있는 사용자가 그 프로젝트의 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다](#usage-a-user-reading-the-project-reads-its-usage) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 사용량을 읽으려 하면 권한 부족으로 거부됩니다](#usage-a-user-granted-nothing-may-not-read-a-projects-usage) | 거부 |

**resource_group_usage**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 자원 그룹의 사용량을 읽으면, 에이전트가 없으므로 용량·사용량·여유가 모두 비어 있습니다](#usage-the-superadmin-reads-a-resource-groups-usage) | 성공 |
| [superadmin 이 아닌 사용자가 자원 그룹 사용량을 읽으려 하면 역할이 없다는 것으로 거부됩니다](#usage-a-user-may-not-read-a-resource-groups-usage) | 거부 |

### admin_domain_usage

<a id="usage-a-user-reading-the-domain-reads-its-usage"></a>

#### [a-user-reading-the-domain-reads-its-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

도메인 범위에서 도메인을 읽을 수 있는 사용자가 그 도메인의 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 도메인 범위에서 도메인을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 도메인 범위의 도메인 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.admin_domain_usage: user-1이 도메인 home-1의 사용량을 조회합니다

Then

- 도메인 범위의 한도는 무한대이고 사용량은 0 입니다
  - domain.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - domain.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - domain.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-reading-the-usage-of-a-domain-nothing-answers-to-is-not-found"></a>

#### [reading-the-usage-of-a-domain-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

없는 이름으로 도메인 사용량을 읽으면 대상이 없다는 것으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.admin_domain_usage: user-1이 도메인 no-such-target 의 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### check_preset_availability

<a id="checking_presets-a-user-reading-presets-checks-available-presets-with-a-given-key"></a>

#### [a-user-reading-presets-checks-available-presets-with-a-given-key](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

프로젝트 범위에서 리소스 프리셋을 읽을 수 있는 사용자가 주어진 접근 키와 정책으로 프리셋 가용성을 확인하면, 미리 저장한 프리셋이 모두 쓸 수 있는 것으로 반환됩니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 리소스 프리셋을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다. 프리셋 2개가 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 리소스 프리셋 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: resource_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유
  - 자원 프리셋 preset-1: 자원 그룹에 묶이지 않아 public 에 속합니다
  - 자원 프리셋 preset-2: 자원 그룹에 묶이지 않아 public 에 속합니다

When

- ResourceAllocationAdapter.check_preset_availability: user-1이 프로젝트 team-1에서 쓸 수 있는 프리셋을 확인합니다

Then

- 미리 저장한 프리셋이 모두 쓰일 수 있는 것으로 응답으로 옵니다
  - len(presets) = 2
  - presets[0].id: 미리 저장한 프리셋의 id 와 같다
  - presets[0].name = 'preset-1'
  - presets[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[0].shared_memory = None
  - presets[0].resource_group_name = None
  - presets[0].available = True
  - presets[1].id: 미리 저장한 프리셋의 id 와 같다
  - presets[1].name = 'preset-2'
  - presets[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[1].shared_memory = None
  - presets[1].resource_group_name = None
  - presets[1].available = True

<a id="checking_presets-a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key"></a>

#### [a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

아무 권한도 받지 않은 사용자가 주어진 키로 프리셋 가용성을 확인하려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다. 프리셋 1개가 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자원 프리셋 preset-1: 자원 그룹에 묶이지 않아 public 에 속합니다

When

- ResourceAllocationAdapter.check_preset_availability: user-1이 프로젝트 team-1에서 쓸 수 있는 프리셋을 확인합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### check_preset_availability_for_current_user

<a id="checking_presets-a-user-reading-presets-checks-available-presets-for-themselves"></a>

#### [a-user-reading-presets-checks-available-presets-for-themselves](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

프로젝트 범위에서 리소스 프리셋을 읽고 자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 키페어로 프리셋 가용성을 확인하면, 미리 저장한 프리셋이 모두 쓸 수 있는 것으로 반환됩니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다. 그 사용자는 프로젝트 범위에서 리소스 프리셋을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다. 프리셋 2개가 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자기 사용자 범위의 사용자 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유
  - 프로젝트 범위의 리소스 프리셋 조회 권한을 받은 사용자
    - 역할 reader-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-2: resource_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-2 보유
  - 자원 프리셋 preset-1: 자원 그룹에 묶이지 않아 public 에 속합니다
  - 자원 프리셋 preset-2: 자원 그룹에 묶이지 않아 public 에 속합니다

When

- ResourceAllocationAdapter.check_preset_availability_for_current_user: user-1이 프로젝트 team-1에서 쓸 수 있는 프리셋을 확인합니다

Then

- 미리 저장한 프리셋이 모두 쓰일 수 있는 것으로 응답으로 옵니다
  - len(presets) = 2
  - presets[0].id: 미리 저장한 프리셋의 id 와 같다
  - presets[0].name = 'preset-1'
  - presets[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[0].shared_memory = None
  - presets[0].resource_group_name = None
  - presets[0].available = True
  - presets[1].id: 미리 저장한 프리셋의 id 와 같다
  - presets[1].name = 'preset-2'
  - presets[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[1].shared_memory = None
  - presets[1].resource_group_name = None
  - presets[1].available = True

<a id="checking_presets-a-user-granted-nothing-may-not-check-preset-availability"></a>

#### [a-user-granted-nothing-may-not-check-preset-availability](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

아무 권한도 받지 않은 사용자가 프리셋 가용성을 확인하려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다. 프리셋 1개가 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자원 프리셋 preset-1: 자원 그룹에 묶이지 않아 public 에 속합니다

When

- ResourceAllocationAdapter.check_preset_availability_for_current_user: user-1이 프로젝트 team-1에서 쓸 수 있는 프리셋을 확인합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### effective_allocation

<a id="effective_allocation-a-user-reading-sessions-reads-the-effective-allocation"></a>

#### [a-user-reading-sessions-reads-the-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

프로젝트 범위에서 세션을 읽을 수 있는 사용자가 유효 할당을 읽으면, 기본 설정에서는 프로젝트 범위가 담기지 않고 자원 그룹 범위가 담깁니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 세션을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: session 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.effective_allocation: user-1이 프로젝트 team-1의 유효 할당을 조회합니다

Then

- 유효 할당 전체가 응답으로 옵니다. 프로젝트 범위는 담기지 않습니다. 자원 그룹 범위가 담깁니다
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project = None
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-hiding-agents-drops-the-resource-group-scope"></a>

#### [hiding-agents-drops-the-resource-group-scope](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

에이전트를 숨기면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에서 자원 그룹 범위가 빠집니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 세션을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: session 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.effective_allocation: user-1이 프로젝트 team-1의 유효 할당을 조회합니다

Then

- 유효 할당 전체가 응답으로 옵니다. 프로젝트 범위는 담기지 않습니다. 자원 그룹 범위는 담기지 않습니다
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project = None
  - breakdown.resource_group = None

<a id="effective_allocation-turning-group-resource-visibility-on-shows-the-project-scope"></a>

#### [turning-group-resource-visibility-on-shows-the-project-scope](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

자원 그룹 가시성을 켜면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에 프로젝트 범위가 담깁니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 세션을 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: session 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.effective_allocation: user-1이 프로젝트 team-1의 유효 할당을 조회합니다

Then

- 유효 할당 전체가 응답으로 옵니다. 프로젝트 범위가 담깁니다. 자원 그룹 범위가 담깁니다
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.project.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-a-user-granted-nothing-may-not-read-the-effective-allocation"></a>

#### [a-user-granted-nothing-may-not-read-the-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 유효 할당을 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.effective_allocation: user-1이 프로젝트 team-1의 유효 할당을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### effective_allocation_for_current_user

<a id="effective_allocation-a-user-reading-sessions-reads-their-own-effective-allocation"></a>

#### [a-user-reading-sessions-reads-their-own-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

프로젝트 범위에서 세션을 읽고 자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 유효 할당을 읽으면, 기본 설정에서는 자원 그룹 범위만 담겨 반환됩니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 세션을 읽을 수 있습니다. 그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: session 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유
  - 자기 사용자 범위의 사용자 조회 권한을 받은 사용자
    - 역할 reader-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-2: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-2 보유

When

- ResourceAllocationAdapter.effective_allocation_for_current_user: user-1이 자기 유효 할당을 조회합니다

Then

- 유효 할당 전체가 응답으로 옵니다. 프로젝트 범위는 담기지 않습니다. 자원 그룹 범위가 담깁니다
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project = None
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-a-user-granted-nothing-may-not-read-their-own-effective-allocation"></a>

#### [a-user-granted-nothing-may-not-read-their-own-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

아무 권한도 받지 않은 사용자가 자기 유효 할당을 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.effective_allocation_for_current_user: user-1이 자기 유효 할당을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_concurrency

<a id="usage-a-user-reading-their-own-user-reads-their-concurrency"></a>

#### [a-user-reading-their-own-user-reads-their-concurrency](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 동시 세션 수를 읽으면, 세션이 없으므로 모두 0 이 반환됩니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자기 사용자 범위의 사용자 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.my_concurrency: user-1이 자기 동시 세션 수를 조회합니다

Then

- 그 사용자의 세션 수가 오고, 아무 세션도 없으므로 모두 0 입니다
  - user_id: 호출한 사용자의 id 와 같다
  - session_count = 0
  - private_session_count = 0

<a id="usage-a-user-granted-nothing-may-not-read-their-own-concurrency"></a>

#### [a-user-granted-nothing-may-not-read-their-own-concurrency](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

아무 권한도 받지 않은 사용자가 자기 동시 세션 수를 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.my_concurrency: user-1이 자기 동시 세션 수를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_keypair_usage

<a id="usage-a-user-reading-their-own-user-reads-their-keypair-usage"></a>

#### [a-user-reading-their-own-user-reads-their-keypair-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 기본 키페어 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자기 사용자 범위의 사용자 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.my_keypair_usage: user-1이 자기 기본 키페어 사용량을 조회합니다

Then

- 키페어 범위의 한도는 무한대이고 사용량은 0 입니다
  - keypair.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - keypair.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - keypair.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-their-own-keypair-usage"></a>

#### [a-user-granted-nothing-may-not-read-their-own-keypair-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

아무 권한도 받지 않은 사용자가 자기 키페어 사용량을 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.my_keypair_usage: user-1이 자기 기본 키페어 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_user_usage

<a id="usage-a-user-reading-their-own-user-reads-their-user-usage"></a>

#### [a-user-reading-their-own-user-reads-their-user-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 자기 사용자 범위의 사용자 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.my_user_usage: user-1이 자기 사용량을 조회합니다

Then

- 사용자 범위의 한도는 무한대이고 사용량은 0 입니다
  - user.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - user.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - user.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-their-own-user-usage"></a>

#### [a-user-granted-nothing-may-not-read-their-own-user-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

아무 권한도 받지 않은 사용자가 자기 사용량을 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.my_user_usage: user-1이 자기 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### project_usage

<a id="usage-a-user-reading-the-project-reads-its-usage"></a>

#### [a-user-reading-the-project-reads-its-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

프로젝트 범위에서 프로젝트를 읽을 수 있는 사용자가 그 프로젝트의 사용량을 읽으면, 등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다

Given

- 자리 하나와 일반 사용자 한 명. 그 사용자는 프로젝트 범위에서 프로젝트를 읽을 수 있습니다. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 프로젝트 범위의 프로젝트 조회 권한을 받은 사용자
    - 역할 reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 reader-1: project 전체에 READ 허용
    - 일반 사용자 user-1: 역할 reader-1 보유

When

- ResourceAllocationAdapter.project_usage: user-1이 프로젝트 team-1의 사용량을 조회합니다

Then

- 프로젝트 범위의 한도는 무한대이고 사용량은 0 입니다
  - project.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - project.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - project.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-a-projects-usage"></a>

#### [a-user-granted-nothing-may-not-read-a-projects-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 사용량을 읽으려 하면 권한 부족으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명. 슬롯 종류 하나가 등록되어 있습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.project_usage: user-1이 프로젝트 team-1의 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### resource_group_usage

<a id="usage-the-superadmin-reads-a-resource-groups-usage"></a>

#### [the-superadmin-reads-a-resource-groups-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

superadmin 이 자원 그룹의 사용량을 읽으면, 에이전트가 없으므로 용량·사용량·여유가 모두 비어 있습니다

Given

- 자리 하나와 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - superadmin user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.resource_group_usage: user-1이 자원 그룹 group-1의 사용량을 조회합니다

Then

- 자원 그룹의 용량, 사용량, 여유가 모두 비어 있습니다
  - resource_group.capacity = []
  - resource_group.used = []
  - resource_group.free = []
  - resource_group.max_per_node = []

<a id="usage-a-user-may-not-read-a-resource-groups-usage"></a>

#### [a-user-may-not-read-a-resource-groups-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

superadmin 이 아닌 사용자가 자원 그룹 사용량을 읽으려 하면 역할이 없다는 것으로 거부됩니다

Given

- 자리 하나와 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- ResourceAllocationAdapter.resource_group_usage: user-1이 자원 그룹 group-1의 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

