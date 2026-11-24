## bootstrap_script

[어댑터](/src/ai/backend/manager/api/adapters/bootstrap_script/adapter.py)

시나리오: 완성

- ops 구성 (4)
  - bulk_get_ids: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (4)
  - add_revision: 성공 있음 1 · 거부 있음 1 (runtime_single_field)
  - bulk_get_current_revisions: 성공 있음 1 · 거부 있음 1 (partial_bulk_field)
  - create: 성공 있음 1 · 거부 있음 1 (single_entity)
  - switch_default: 성공 있음 1 · 거부 있음 1 (single_entity)

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 일괄 조회하면, 그 script 가 응답으로 옵니다](#batch_loading-a-user-granted-read-loads-their-bootstrap-script-by-id) | 성공 |
| [자기 사용자에 READ 권한을 받은 사용자가 자기 script 와 다른 사용자의 script 를 id 로 일괄 조회하면, 호출은 성공하되 다른 사용자의 script 자리는 권한 부족으로 거부됩니다](#batch_loading-a-strangers-bootstrap-script-is-rejected-in-the-batch) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 읽으면, 그 script 가 응답으로 옵니다](#reading-a-user-granted-read-reads-their-bootstrap-script) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 id 로 읽으려 하면, script 가 있는지 알려 주지 않는 답으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-their-bootstrap-script) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 지우면, 지운 script 의 id 가 응답으로 옵니다](#purging-a-user-granted-update-purges-their-bootstrap-script) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 지우려 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-read-may-not-purge-their-bootstrap-script) | 거부 |
| [자기 사용자에 READ, UPDATE 권한을 받은 사용자라도 자기 default bootstrap script 를 지우려 하면, default 를 먼저 바꾸라며 거부됩니다](#purging-the-default-bootstrap-script-is-not-purged) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 중 default 가 아닌 것을 검색하면, 그 script 만 오고 default script 와 다른 사용자의 script 는 오지 않습니다](#searching-a-user-granted-read-searches-their-bootstrap-scripts) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 검색하려 하면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-their-bootstrap-scripts) | 거부 |

**add_revision**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ, UPDATE 권한을 받은 사용자가 자기 bootstrap script 의 내용을 바꾸면, revision 2 가 응답으로 옵니다](#revising-a-user-granted-update-adds-a-revision) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 의 내용을 바꾸려 하면 권한 부족으로 거부됩니다](#revising-a-user-granted-read-may-not-add-a-revision) | 거부 |

**bulk_get_current_revisions**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 의 가장 마지막 revision 을 일괄 조회하면, 그 script 의 가장 마지막 revision 이 응답으로 옵니다](#batch_loading_revisions-a-user-granted-read-loads-their-bootstrap-script-current-revision) | 성공 |
| [자기 사용자에 READ 권한을 받은 사용자가 자기 script 와 다른 사용자의 script 의 가장 마지막 revision 을 일괄 조회하면, 호출은 성공하되 다른 사용자의 script 자리는 권한 부족으로 거부됩니다](#batch_loading_revisions-a-strangers-bootstrap-script-revision-is-rejected-in-the-batch) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 UPDATE 권한을 받은 사용자가 bootstrap script 를 추가하면, 새 script 의 revision 1 이 응답으로 옵니다](#creating-a-user-granted-update-adds-a-bootstrap-script) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 bootstrap script 를 추가하려 하면 권한 부족으로 거부됩니다](#creating-a-user-granted-read-may-not-add-a-bootstrap-script) | 거부 |

**switch_default**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 default 로 지정하면, 그 script 가 응답으로 옵니다](#switching_default-a-user-granted-update-switches-their-default-script) | 성공 |
| [자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 default 로 지정하려 하면 권한 부족으로 거부됩니다](#switching_default-a-user-granted-read-may-not-switch-their-default-script) | 거부 |

### bulk_get_ids

<a id="batch_loading-a-user-granted-read-loads-their-bootstrap-script-by-id"></a>

#### [a-user-granted-read-loads-their-bootstrap-script-by-id](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 일괄 조회하면, 그 script 가 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.bulk_get_ids: user-1이 자기 default bootstrap script 를 id 로 일괄 조회합니다

Then

- 자기 default script 하나가 응답으로 옵니다
  - length = 1
  - [0].id: 심어 둔 default script 와 같다
  - [0].field_id: 응답의 id 와 같다
  - [0].user_id: 호출한 사용자와 같다
  - [0].created_at: 이 실행이 쓴 시각

<a id="batch_loading-a-strangers-bootstrap-script-is-rejected-in-the-batch"></a>

#### [a-strangers-bootstrap-script-is-rejected-in-the-batch](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 script 와 다른 사용자의 script 를 id 로 일괄 조회하면, 호출은 성공하되 다른 사용자의 script 자리는 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 같은 도메인의 다른 사용자도 bootstrap script 하나를 갖습니다, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-2: revision 1 의 내용이 'echo stranger' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.bulk_get_ids: user-1이 자기 default bootstrap script 와 다른 사용자의 bootstrap script 를 id 로 일괄 조회합니다

Then

- 자기 script 는 오고, 다른 사용자의 script 자리는 권한 부족으로 거부됩니다
  - length = 2
  - [0].id: 심어 둔 default script 와 같다
  - [0].field_id: 응답의 id 와 같다
  - [0].user_id: 호출한 사용자와 같다
  - [0].created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-their-bootstrap-script"></a>

#### [a-user-granted-read-reads-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_reading.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 읽으면, 그 script 가 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.get: user-1이 자기 default bootstrap script 를 id 로 읽습니다

Then

- bootstrap script 전체가 응답으로 옵니다
  - id: 심어 둔 default script 와 같다
  - field_id: 응답의 id 와 같다
  - user_id: 호출한 사용자와 같다
  - created_at: 이 실행이 쓴 시각

<a id="reading-a-user-granted-nothing-may-not-read-their-bootstrap-script"></a>

#### [a-user-granted-nothing-may-not-read-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_reading.py): pass

아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 id 로 읽으려 하면, script 가 있는지 알려 주지 않는 답으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다

When

- BootstrapScriptAdapter.get: user-1이 자기 default bootstrap script 를 id 로 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### purge

<a id="purging-a-user-granted-update-purges-their-bootstrap-script"></a>

#### [a-user-granted-update-purges-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 지우면, 지운 script 의 id 가 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.purge: user-1이 default 가 아닌 자기 bootstrap script 를 지웁니다

Then

- 지운 script 의 id 가 응답으로 옵니다
  - field_id: 심어 둔 default 가 아닌 script 와 같다

<a id="purging-a-user-granted-read-may-not-purge-their-bootstrap-script"></a>

#### [a-user-granted-read-may-not-purge-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 지우려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.purge: user-1이 default 가 아닌 자기 bootstrap script 를 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-the-default-bootstrap-script-is-not-purged"></a>

#### [the-default-bootstrap-script-is-not-purged](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

자기 사용자에 READ, UPDATE 권한을 받은 사용자라도 자기 default bootstrap script 를 지우려 하면, default 를 먼저 바꾸라며 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.purge: user-1이 자기 default bootstrap script 를 지웁니다

Then

- 거부됩니다
  - 거부: DefaultBootstrapScriptPurgeForbidden

### scoped_search

<a id="searching-a-user-granted-read-searches-their-bootstrap-scripts"></a>

#### [a-user-granted-read-searches-their-bootstrap-scripts](/tests/scenario/bai_scenario/manager/bootstrap_script/test_searching.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 중 default 가 아닌 것을 검색하면, 그 script 만 오고 default script 와 다른 사용자의 script 는 오지 않습니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 같은 도메인의 다른 사용자도 bootstrap script 하나를 갖습니다, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-2: revision 1 의 내용이 'echo stranger' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.scoped_search: user-1이 자기 bootstrap script 중 default 가 아닌 것을 만든 시각이 늦은 순으로 10개까지 검색합니다

Then

- default 가 아닌 자기 script 하나만 응답으로 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - len(items) = 1
  - items[0].id: 심어 둔 default 가 아닌 script 와 같다
  - items[0].field_id: 응답의 id 와 같다
  - items[0].user_id: 호출한 사용자와 같다
  - items[0].created_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-search-their-bootstrap-scripts"></a>

#### [a-user-granted-nothing-may-not-search-their-bootstrap-scripts](/tests/scenario/bai_scenario/manager/bootstrap_script/test_searching.py): pass

아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 검색하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다

When

- BootstrapScriptAdapter.scoped_search: user-1이 자기 bootstrap script 중 default 가 아닌 것을 만든 시각이 늦은 순으로 10개까지 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### add_revision

<a id="revising-a-user-granted-update-adds-a-revision"></a>

#### [a-user-granted-update-adds-a-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_revising.py): pass

자기 사용자에 READ, UPDATE 권한을 받은 사용자가 자기 bootstrap script 의 내용을 바꾸면, revision 2 가 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.add_revision: user-1이 default 가 아닌 자기 bootstrap script 의 내용을 'echo new' 로 바꿉니다

Then

- revision 전체가 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 만듭니다
  - field_id: 응답의 id 와 같다
  - script_id: 심어 둔 default 가 아닌 script 와 같다
  - revision_number = 2
  - script = 'echo new'
  - creator_id: 호출한 사용자와 같다
  - created_at: 이 실행이 쓴 시각

<a id="revising-a-user-granted-read-may-not-add-a-revision"></a>

#### [a-user-granted-read-may-not-add-a-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_revising.py): pass

자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 의 내용을 바꾸려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.add_revision: user-1이 default 가 아닌 자기 bootstrap script 의 내용을 'echo new' 로 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### bulk_get_current_revisions

<a id="batch_loading_revisions-a-user-granted-read-loads-their-bootstrap-script-current-revision"></a>

#### [a-user-granted-read-loads-their-bootstrap-script-current-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading_revisions.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 의 가장 마지막 revision 을 일괄 조회하면, 그 script 의 가장 마지막 revision 이 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.bulk_get_current_revisions: user-1이 자기 default bootstrap script 의 가장 마지막 revision 을 일괄 조회합니다

Then

- 자기 default script 의 가장 마지막 revision 하나가 응답으로 옵니다
  - length = 1
  - [0].id: 심어 둔 default script 의 revision 1 와 같다
  - [0].field_id: 응답의 id 와 같다
  - [0].script_id: 심어 둔 default script 와 같다
  - [0].revision_number = 1
  - [0].script = 'echo default'
  - [0].creator_id: 호출한 사용자와 같다
  - [0].created_at: 이 실행이 쓴 시각

<a id="batch_loading_revisions-a-strangers-bootstrap-script-revision-is-rejected-in-the-batch"></a>

#### [a-strangers-bootstrap-script-revision-is-rejected-in-the-batch](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading_revisions.py): pass

자기 사용자에 READ 권한을 받은 사용자가 자기 script 와 다른 사용자의 script 의 가장 마지막 revision 을 일괄 조회하면, 호출은 성공하되 다른 사용자의 script 자리는 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 같은 도메인의 다른 사용자도 bootstrap script 하나를 갖습니다, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-2: revision 1 의 내용이 'echo stranger' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.bulk_get_current_revisions: user-1이 자기 default bootstrap script 와 다른 사용자의 bootstrap script 의 가장 마지막 revision 을 일괄 조회합니다

Then

- 자기 script 는 오고, 다른 사용자의 script 자리는 권한 부족으로 거부됩니다
  - length = 2
  - [0].id: 심어 둔 default script 의 revision 1 와 같다
  - [0].field_id: 응답의 id 와 같다
  - [0].script_id: 심어 둔 default script 와 같다
  - [0].revision_number = 1
  - [0].script = 'echo default'
  - [0].creator_id: 호출한 사용자와 같다
  - [0].created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission

### create

<a id="creating-a-user-granted-update-adds-a-bootstrap-script"></a>

#### [a-user-granted-update-adds-a-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_creating.py): pass

자기 사용자에 UPDATE 권한을 받은 사용자가 bootstrap script 를 추가하면, 새 script 의 revision 1 이 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.create: user-1이 자기 사용자에 내용이 'echo new' 인 bootstrap script 를 추가합니다

Then

- revision 전체가 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 만듭니다
  - field_id: 응답의 id 와 같다
  - script_id: 건너뜀: 데이터베이스가 만듭니다
  - revision_number = 1
  - script = 'echo new'
  - creator_id: 호출한 사용자와 같다
  - created_at: 이 실행이 쓴 시각

<a id="creating-a-user-granted-read-may-not-add-a-bootstrap-script"></a>

#### [a-user-granted-read-may-not-add-a-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_creating.py): pass

자기 사용자에 READ 권한만 받은 사용자가 bootstrap script 를 추가하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.create: user-1이 자기 사용자에 내용이 'echo new' 인 bootstrap script 를 추가합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### switch_default

<a id="switching_default-a-user-granted-update-switches-their-default-script"></a>

#### [a-user-granted-update-switches-their-default-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_switching_default.py): pass

자기 사용자에 UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 default 로 지정하면, 그 script 가 응답으로 옵니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.switch_default: user-1이 default 가 아닌 자기 bootstrap script 를 default 로 지정합니다

Then

- bootstrap script 전체가 응답으로 옵니다
  - id: 심어 둔 default 가 아닌 script 와 같다
  - field_id: 응답의 id 와 같다
  - user_id: 호출한 사용자와 같다
  - created_at: 이 실행이 쓴 시각

<a id="switching_default-a-user-granted-read-may-not-switch-their-default-script"></a>

#### [a-user-granted-read-may-not-switch-their-default-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_switching_default.py): pass

자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 default 로 지정하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo default' 인 bootstrap script 하나를 갖습니다
  - 일반 사용자 user-1: 그 bootstrap script 를 default 로 지정합니다
  - 일반 사용자 user-1: revision 1 의 내용이 'echo extra' 인 bootstrap script 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- BootstrapScriptAdapter.switch_default: user-1이 default 가 아닌 자기 bootstrap script 를 default 로 지정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

