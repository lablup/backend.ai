## auto_generated_file

[어댑터](/src/ai/backend/manager/api/adapters/auto_generated_file/adapter.py)

시나리오: 완성

- ops 구성 (10)
  - add_revision: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_get_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_get_revision_ids: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - get_default_auto_generated_file_by_path: 대표 성공 ✓ · 대표 거부 ✓
  - list_default_auto_generated_files: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - purge_default_auto_generated_file: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - search_revisions: 대표 성공 ✓ · 대표 거부 ✓
- ops + 직접 구현 (1)
  - update_default_auto_generated_file: 성공 있음 1 · 거부 있음 2 (scope_search_ops, single_entity)
- 직접 구현 (3)
  - create: 성공 있음 1 · 거부 있음 1 (scope)
  - create_default_auto_generated_file: 성공 있음 1 · 거부 있음 1 (scope, single_entity)
  - switch_default: 성공 있음 1 · 거부 있음 1 (single_entity)

**add_revision**

| 시나리오 | 판정 |
|---|---|
| [UPDATE 를 받은 사용자가 자기 auto-generated file 에 revision 을 더하면, 그 내용과 권한이 revision 2 로 응답으로 오고 revision 1 은 그대로 남습니다](#v2_revisions-a-user-granted-update-adds-a-revision-to-an-auto-generated-file) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 에 revision 을 더하려 하면, 권한 부족으로 거부되고 revision 은 1 하나로 남습니다](#v2_revisions-a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file) | 거부 |

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 auto-generated file 을 id 로 일괄 조회하면, 그 파일이 응답으로 옵니다](#v2_reading-a-user-granted-read-loads-an-auto-generated-file-by-id) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#v2_reading-a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file) | 거부 |

**bulk_get_revision_ids**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 auto-generated file 의 revision 을 id 로 일괄 조회하면, 그 revision 이 응답으로 옵니다](#v2_revisions-a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 의 revision 을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#v2_revisions-a-user-granted-nothing-gets-a-rejection-for-a-revision) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 auto-generated file 을 id 로 읽으면, 그 파일이 응답으로 옵니다](#v2_reading-a-user-granted-read-gets-an-auto-generated-file) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 id 로 읽으려 하면, 권한 부족으로 거부됩니다](#v2_reading-a-user-granted-nothing-may-not-get-an-auto-generated-file) | 거부 |

**get_default_auto_generated_file_by_path**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 default 로 지정된 auto-generated file 을 읽으면, 가장 마지막 revision 의 내용이 옵니다](#config_files-a-user-granted-read-on-their-auto-generated-files-reads-the-default-one) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 읽으려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-read-an-auto-generated-file) | 거부 |
| [READ 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 읽으려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | 거부 |

**list_default_auto_generated_files**

| 시나리오 | 판정 |
|---|---|
| [도메인 스코프에서 auto-generated file READ 를 받은 사용자가 그 도메인의 파일 목록을 조회하면, default 로 지정된 파일이 옵니다](#organization_files-a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files) | 성공 |
| [프로젝트 스코프에서 auto-generated file READ 를 받은 사용자가 그 프로젝트의 파일 목록을 조회하면, default 로 지정된 파일이 옵니다](#organization_files-a-user-granted-file-read-in-a-project-lists-its-auto-generated-files) | 성공 |
| [READ 를 받은 사용자가 자기 auto-generated file 목록을 조회하면, default 로 지정된 파일만 가장 마지막 revision 의 내용과 함께 옵니다](#config_files-a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 목록을 조회하려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-list-their-auto-generated-files) | 거부 |
| [도메인 READ 만 받은 사용자가 그 도메인의 auto-generated file 목록을 조회하려 하면, 권한 부족으로 거부됩니다](#organization_files-a-user-granted-only-domain-read-may-not-list-its-auto-generated-files) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [HARD_DELETE 를 받은 사용자가 default 로 지정되지 않은 자기 auto-generated file 을 지우면, 지운 파일의 id 가 오고 파일과 그 revision 이 모두 지워집니다](#v2_files-a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 지우려 하면, 권한 부족으로 거부됩니다](#v2_files-a-user-granted-nothing-may-not-purge-an-auto-generated-file) | 거부 |
| [HARD_DELETE 를 받은 사용자가 default 로 지정된 자기 auto-generated file 을 지우려 하면, 거부되고 그 파일은 그대로 남습니다](#v2_files-purging-the-auto-generated-file-set-as-default-is-refused) | 거부 |

**purge_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [READ 와 HARD_DELETE 를 받은 사용자가 default 로 지정된 auto-generated file 을 지우면, 지웠다는 응답이 오고 파일과 그 revision 이 모두 지워집니다](#config_files-a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 지우려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-delete-an-auto-generated-file) | 거부 |
| [READ 와 HARD_DELETE 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 지우려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 scope 에서 default 로 지정된 auto-generated file 을 path 오름차순으로 한 페이지 조회하면, default 로 지정되지 않은 파일과 다른 사용자의 파일은 빠지고 자기 파일 둘만 path 순서로 옵니다](#v2_search-a-user-granted-read-lists-their-auto-generated-files-set-as-default) | 성공 |
| [권한을 받지 않은 사용자가 자기 scope 의 auto-generated file 을 조회하려 하면, 권한 부족으로 거부됩니다](#v2_search-a-user-granted-nothing-may-not-list-auto-generated-files) | 거부 |

**search_revisions**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 auto-generated file 의 revision 을 번호로 걸러 한 페이지 조회하면, 걸러진 revision 과 다른 파일의 revision 은 빠지고 그 파일의 revision 만 번호 순서로 옵니다](#v2_revisions-a-user-granted-read-searches-the-revisions-of-an-auto-generated-file) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 의 revision 을 조회하려 하면, 권한 부족으로 거부됩니다](#v2_revisions-a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file) | 거부 |

**update_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [READ 와 UPDATE 를 받은 사용자가 default 로 지정된 auto-generated file 을 고치면, 빈 응답이 오고, 파일의 권한이 바뀌며 새 내용이 revision 2 로 추가됩니다](#config_files-a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 고치려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-update-an-auto-generated-file) | 거부 |
| [READ 와 UPDATE 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 고치려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [자기 auto-generated file 에 CREATE 를 받은 사용자가 auto-generated file 을 만들면, 그 파일은 default 로 지정되지 않은 채 응답으로 오고 내용은 revision 1 로 남습니다](#v2_files-a-user-granted-create-creates-an-auto-generated-file-not-set-as-default) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 만들려 하면, 권한 부족으로 거부됩니다](#v2_files-a-user-granted-nothing-may-not-create-an-auto-generated-file) | 거부 |

**create_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [자기 auto-generated file 에 CREATE 와 UPDATE 를 받은 사용자가 auto-generated file 을 만들면, 빈 응답이 오고, 그 파일은 내용을 revision 1 로 갖고 그 경로의 default 로 지정됩니다](#config_files-a-user-granted-create-and-update-on-their-auto-generated-files-writes-one) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 만들려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-write-an-auto-generated-file) | 거부 |

**switch_default**

| 시나리오 | 판정 |
|---|---|
| [UPDATE 를 받은 사용자가 같은 path 의 default 로 지정되지 않은 자기 auto-generated file 을 default 로 지정하면, 그 파일이 default 로 지정된 채 오고 이전 default 는 default 로 지정되지 않은 파일로 남습니다](#v2_default-a-user-granted-update-switches-the-default-auto-generated-file-of-a-path) | 성공 |
| [권한을 받지 않은 사용자가 자기 auto-generated file 을 default 로 지정하려 하면, 권한 부족으로 거부됩니다](#v2_default-a-user-granted-nothing-may-not-switch-the-default-auto-generated-file) | 거부 |

### add_revision

<a id="v2_revisions-a-user-granted-update-adds-a-revision-to-an-auto-generated-file"></a>

#### [a-user-granted-update-adds-a-revision-to-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

UPDATE 를 받은 사용자가 자기 auto-generated file 에 revision 을 더하면, 그 내용과 권한이 revision 2 로 응답으로 오고 revision 1 은 그대로 남습니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file UPDATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.add_revision: user-1이 자기 .vimrc auto-generated file 에 내용 'set nonumber\n', 권한 600 을 다음 revision 으로 더합니다

Then

- 더한 내용이 revision 2 로 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - field_id: 건너뜀: 데이터베이스가 생성합니다
  - auto_generated_file_id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - revision_number = 2
  - data = 'set nonumber\n'
  - permission = '600'
  - creator_id: 파일 주인의 id 와 같다
  - created_at: 이 실행이 쓴 시각

<a id="v2_revisions-a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 에 revision 을 더하려 하면, 권한 부족으로 거부되고 revision 은 1 하나로 남습니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.add_revision: user-1이 자기 .vimrc auto-generated file 에 내용 'set nonumber\n', 권한 600 을 다음 revision 으로 더합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### bulk_get_ids

<a id="v2_reading-a-user-granted-read-loads-an-auto-generated-file-by-id"></a>

#### [a-user-granted-read-loads-an-auto-generated-file-by-id](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

READ 를 받은 사용자가 자기 auto-generated file 을 id 로 일괄 조회하면, 그 파일이 응답으로 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.bulk_get_ids: user-1이 자기 .vimrc auto-generated file 을 id 로 일괄 조회합니다

Then

- 심어 둔 파일 하나가 응답으로 옵니다
  - length = 1
  - id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - entity_id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - scope_type = 'user'
  - scope_id: 파일 주인의 id 와 같다
  - path = '.vimrc'
  - is_default = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="v2_reading-a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.bulk_get_ids: user-1이 자기 .vimrc auto-generated file 을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### bulk_get_revision_ids

<a id="v2_revisions-a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id"></a>

#### [a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

READ 를 받은 사용자가 자기 auto-generated file 의 revision 을 id 로 일괄 조회하면, 그 revision 이 응답으로 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.bulk_get_revision_ids: user-1이 자기 .vimrc auto-generated file 의 revision 1 을 id 로 일괄 조회합니다

Then

- revision 1 하나가 응답으로 옵니다
  - length = 1
  - id: 심어 둔 revision 의 id 와 같다
  - field_id: 심어 둔 revision 의 id 와 같다
  - auto_generated_file_id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - revision_number = 1
  - data = 'set number\n'
  - permission = '644'
  - creator_id: 파일 주인의 id 와 같다
  - created_at: 이 실행이 쓴 시각

<a id="v2_revisions-a-user-granted-nothing-gets-a-rejection-for-a-revision"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-a-revision](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 의 revision 을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.bulk_get_revision_ids: user-1이 자기 .vimrc auto-generated file 의 revision 1 을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### get

<a id="v2_reading-a-user-granted-read-gets-an-auto-generated-file"></a>

#### [a-user-granted-read-gets-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

READ 를 받은 사용자가 자기 auto-generated file 을 id 로 읽으면, 그 파일이 응답으로 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.get: user-1이 자기 .vimrc auto-generated file 을 id 로 읽습니다

Then

- 심어 둔 파일이 응답으로 옵니다
  - id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - entity_id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - scope_type = 'user'
  - scope_id: 파일 주인의 id 와 같다
  - path = '.vimrc'
  - is_default = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="v2_reading-a-user-granted-nothing-may-not-get-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-get-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 id 로 읽으려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.get: user-1이 자기 .vimrc auto-generated file 을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_default_auto_generated_file_by_path

<a id="config_files-a-user-granted-read-on-their-auto-generated-files-reads-the-default-one"></a>

#### [a-user-granted-read-on-their-auto-generated-files-reads-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 를 받은 사용자가 default 로 지정된 auto-generated file 을 읽으면, 가장 마지막 revision 의 내용이 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1이 자기 auto-generated file 하나를 읽습니다

Then

- 그 경로의 default 파일이 가장 마지막 revision 의 내용과 함께 옵니다
  - response = {'path': '.vimrc', 'perm': '644', 'data': 'set number\n'}

<a id="config_files-a-user-granted-nothing-may-not-read-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-read-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 읽으려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1이 자기 auto-generated file 하나를 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="config_files-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 읽으려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1이 자기 auto-generated file 하나를 읽습니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

### list_default_auto_generated_files

<a id="organization_files-a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files"></a>

#### [a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

도메인 스코프에서 auto-generated file READ 를 받은 사용자가 그 도메인의 파일 목록을 조회하면, default 로 지정된 파일이 옵니다

Given

- 도메인 하나는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 그 도메인 스코프의 역할로 auto_generated_file READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 역할 config-file-reader-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 config-file-reader-1: auto_generated_file 전체에 READ 허용
  - 일반 사용자 user-1: 역할 config-file-reader-1 보유

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1이 그 owner 의 default 로 지정된 auto-generated file 목록을 조회합니다

Then

- 그 owner 의 default 파일 하나가 path, 권한, 내용과 함께 옵니다
  - response = [{'path': '.vimrc', 'permission': '644', 'data': 'set number\n'}]

<a id="organization_files-a-user-granted-file-read-in-a-project-lists-its-auto-generated-files"></a>

#### [a-user-granted-file-read-in-a-project-lists-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

프로젝트 스코프에서 auto-generated file READ 를 받은 사용자가 그 프로젝트의 파일 목록을 조회하면, default 로 지정된 파일이 옵니다

Given

- 프로젝트 하나는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 그 프로젝트 스코프의 역할로 auto_generated_file READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 역할 config-file-reader-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 config-file-reader-1: auto_generated_file 전체에 READ 허용
  - 일반 사용자 user-1: 역할 config-file-reader-1 보유

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1이 그 owner 의 default 로 지정된 auto-generated file 목록을 조회합니다

Then

- 그 owner 의 default 파일 하나가 path, 권한, 내용과 함께 옵니다
  - response = [{'path': '.vimrc', 'permission': '644', 'data': 'set number\n'}]

<a id="config_files-a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones"></a>

#### [a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 를 받은 사용자가 자기 auto-generated file 목록을 조회하면, default 로 지정된 파일만 가장 마지막 revision 의 내용과 함께 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 default 로 지정되지 않은 .bashrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'export EDITOR=vim\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - auto-generated file .bashrc: default 로 지정되지 않은 파일
  - auto-generated file .bashrc: 내용이 'export EDITOR=vim\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1이 default 로 지정된 자기 auto-generated file 목록을 조회합니다

Then

- default 로 지정된 .vimrc 파일만 가장 마지막 revision 의 내용과 함께 목록에 옵니다
  - files = [('.vimrc', '644', 'set number\n')]

<a id="config_files-a-user-granted-nothing-may-not-list-their-auto-generated-files"></a>

#### [a-user-granted-nothing-may-not-list-their-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 목록을 조회하려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1이 default 로 지정된 자기 auto-generated file 목록을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="organization_files-a-user-granted-only-domain-read-may-not-list-its-auto-generated-files"></a>

#### [a-user-granted-only-domain-read-may-not-list-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

도메인 READ 만 받은 사용자가 그 도메인의 auto-generated file 목록을 조회하려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 그 도메인 스코프의 역할로 domain READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 역할 config-file-reader-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 config-file-reader-1: domain 전체에 READ 허용
  - 일반 사용자 user-1: 역할 config-file-reader-1 보유

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1이 그 owner 의 default 로 지정된 auto-generated file 목록을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### purge

<a id="v2_files-a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default"></a>

#### [a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

HARD_DELETE 를 받은 사용자가 default 로 지정되지 않은 자기 auto-generated file 을 지우면, 지운 파일의 id 가 오고 파일과 그 revision 이 모두 지워집니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file HARD_DELETE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.purge: user-1이 자기 .vimrc auto-generated file 을 지웁니다

Then

- 지운 파일의 id 가 응답으로 옵니다
  - entity_id: 심어 둔 .vimrc auto-generated file 의 값와 같다

<a id="v2_files-a-user-granted-nothing-may-not-purge-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-purge-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 지우려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.purge: user-1이 자기 .vimrc auto-generated file 을 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="v2_files-purging-the-auto-generated-file-set-as-default-is-refused"></a>

#### [purging-the-auto-generated-file-set-as-default-is-refused](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

HARD_DELETE 를 받은 사용자가 default 로 지정된 자기 auto-generated file 을 지우려 하면, 거부되고 그 파일은 그대로 남습니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 자기 auto-generated file HARD_DELETE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.purge: user-1이 자기 .vimrc auto-generated file 을 지웁니다

Then

- 거부됩니다
  - 거부: DefaultDotfilePurgeForbidden

### purge_default_auto_generated_file

<a id="config_files-a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one"></a>

#### [a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 와 HARD_DELETE 를 받은 사용자가 default 로 지정된 auto-generated file 을 지우면, 지웠다는 응답이 오고 파일과 그 revision 이 모두 지워집니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ, HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 자기 auto-generated file READ, HARD_DELETE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 역할 config-file-role-1: auto_generated_file 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1이 자기 auto-generated file 하나를 지웁니다

Then

- 지웠다는 응답이 옵니다
  - response = {'success': True}

<a id="config_files-a-user-granted-nothing-may-not-delete-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-delete-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 지우려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1이 자기 auto-generated file 하나를 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="config_files-deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 와 HARD_DELETE 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 지우려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ, HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ, HARD_DELETE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 역할 config-file-role-1: auto_generated_file 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1이 자기 auto-generated file 하나를 지웁니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

### scoped_search

<a id="v2_search-a-user-granted-read-lists-their-auto-generated-files-set-as-default"></a>

#### [a-user-granted-read-lists-their-auto-generated-files-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_search.py): pass

READ 를 받은 사용자가 자기 scope 에서 default 로 지정된 auto-generated file 을 path 오름차순으로 한 페이지 조회하면, default 로 지정되지 않은 파일과 다른 사용자의 파일은 빠지고 자기 파일 둘만 path 순서로 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 default 로 지정된 .bashrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'export EDITOR=vim\n'), 같은 도메인의 다른 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다, 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .bashrc: default 로 지정되지 않은 파일
  - auto-generated file .bashrc: 내용이 'export EDITOR=vim\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .bashrc: 그 경로의 default 로 지정됩니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.scoped_search: user-1이 자기 scope 의 auto-generated file 중 default 로 지정된 것만 path 오름차순으로 10개까지 조회합니다

Then

- default 로 지정된 자기 파일 둘만 path 순서로 실린 한 페이지가 응답으로 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 심어 둔 default 로 지정된 .bashrc 파일와 같다
  - items[0].entity_id: 심어 둔 default 로 지정된 .bashrc 파일와 같다
  - items[0].scope_type = 'user'
  - items[0].scope_id: 파일 주인의 id 와 같다
  - items[0].path = '.bashrc'
  - items[0].is_default = True
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 심어 둔 default 로 지정된 .vimrc 파일와 같다
  - items[1].entity_id: 심어 둔 default 로 지정된 .vimrc 파일와 같다
  - items[1].scope_type = 'user'
  - items[1].scope_id: 파일 주인의 id 와 같다
  - items[1].path = '.vimrc'
  - items[1].is_default = True
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각

<a id="v2_search-a-user-granted-nothing-may-not-list-auto-generated-files"></a>

#### [a-user-granted-nothing-may-not-list-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_search.py): pass

권한을 받지 않은 사용자가 자기 scope 의 auto-generated file 을 조회하려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다

When

- AutoGeneratedFileAdapter.scoped_search: user-1이 자기 scope 의 auto-generated file 중 default 로 지정된 것만 path 오름차순으로 10개까지 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_revisions

<a id="v2_revisions-a-user-granted-read-searches-the-revisions-of-an-auto-generated-file"></a>

#### [a-user-granted-read-searches-the-revisions-of-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

READ 를 받은 사용자가 자기 auto-generated file 의 revision 을 번호로 걸러 한 페이지 조회하면, 걸러진 revision 과 다른 파일의 revision 은 빠지고 그 파일의 revision 만 번호 순서로 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n', revision 2 의 내용 'set nonumber\n', revision 3 의 내용 'set relativenumber\n'), 사용자는 default 로 지정되지 않은 .bashrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'export EDITOR=vim\n'), 사용자는 자기 auto-generated file 에 대한 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .vimrc: 내용이 'set nonumber\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .vimrc: 내용이 'set relativenumber\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .bashrc: default 로 지정되지 않은 파일
  - auto-generated file .bashrc: 내용이 'export EDITOR=vim\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.search_revisions: user-1이 자기 .vimrc auto-generated file 의 revision 중 번호가 2 이상인 것을 번호 내림차순으로 한 개만 조회합니다

Then

- revision 1 과 다른 파일의 revision 은 빠지고, revision 3 하나가 오며 전체 수는 2 입니다
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - len(items) = 1
  - id: 심어 둔 revision 의 id 와 같다
  - field_id: 심어 둔 revision 의 id 와 같다
  - auto_generated_file_id: 심어 둔 .vimrc auto-generated file 의 id 와 같다
  - revision_number = 3
  - data = 'set relativenumber\n'
  - permission = '644'
  - creator_id: 파일 주인의 id 와 같다
  - created_at: 이 실행이 쓴 시각

<a id="v2_revisions-a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 의 revision 을 조회하려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n', revision 2 의 내용 'set nonumber\n', revision 3 의 내용 'set relativenumber\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .vimrc: 내용이 'set nonumber\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - auto-generated file .vimrc: 내용이 'set relativenumber\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.search_revisions: user-1이 자기 .vimrc auto-generated file 의 revision 중 번호가 2 이상인 것을 번호 내림차순으로 한 개만 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update_default_auto_generated_file

<a id="config_files-a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one"></a>

#### [a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 와 UPDATE 를 받은 사용자가 default 로 지정된 auto-generated file 을 고치면, 빈 응답이 오고, 파일의 권한이 바뀌며 새 내용이 revision 2 로 추가됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - 자기 auto-generated file READ, UPDATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 역할 config-file-role-1: auto_generated_file 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1이 자기 .vimrc auto-generated file 의 권한을 600, 내용을 'set nonumber\n' 로 바꿉니다

Then

- 고친 파일의 path 와 바뀐 권한, 바뀐 내용이 응답으로 옵니다
  - path = '.vimrc'
  - perm = '600'
  - data = 'set nonumber\n'

<a id="config_files-a-user-granted-nothing-may-not-update-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-update-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 고치려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1이 자기 .vimrc auto-generated file 의 권한을 600, 내용을 'set nonumber\n' 로 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="config_files-updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

READ 와 UPDATE 를 받은 사용자가 default 로 지정되지 않은 auto-generated file 을 고치려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file READ, UPDATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 READ 허용
    - 역할 config-file-role-1: auto_generated_file 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1이 자기 .vimrc auto-generated file 의 권한을 600, 내용을 'set nonumber\n' 로 바꿉니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

### create

<a id="v2_files-a-user-granted-create-creates-an-auto-generated-file-not-set-as-default"></a>

#### [a-user-granted-create-creates-an-auto-generated-file-not-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

자기 auto-generated file 에 CREATE 를 받은 사용자가 auto-generated file 을 만들면, 그 파일은 default 로 지정되지 않은 채 응답으로 오고 내용은 revision 1 로 남습니다

Given

- 도메인 하나와 사용자 하나, 사용자는 자기 auto-generated file 에 대한 CREATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 auto-generated file CREATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.create: user-1이 자기 .vimrc auto-generated file 을 하나 만듭니다

Then

- default 로 지정되지 않은 새 파일이 응답으로 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - scope_type = 'user'
  - scope_id: 파일 주인의 id 와 같다
  - path = '.vimrc'
  - is_default = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="v2_files-a-user-granted-nothing-may-not-create-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-create-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 만들려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.create: user-1이 자기 .vimrc auto-generated file 을 하나 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create_default_auto_generated_file

<a id="config_files-a-user-granted-create-and-update-on-their-auto-generated-files-writes-one"></a>

#### [a-user-granted-create-and-update-on-their-auto-generated-files-writes-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

자기 auto-generated file 에 CREATE 와 UPDATE 를 받은 사용자가 auto-generated file 을 만들면, 빈 응답이 오고, 그 파일은 내용을 revision 1 로 갖고 그 경로의 default 로 지정됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 자기 auto-generated file 에 대한 CREATE, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 auto-generated file CREATE, UPDATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 CREATE 허용
    - 역할 config-file-role-1: auto_generated_file 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.create_default_auto_generated_file: user-1이 자기 auto-generated file 을 하나 만듭니다

Then

- 만든 파일의 path, 권한, 내용이 그대로 응답으로 옵니다
  - path = '.vimrc'
  - perm = '644'
  - data = 'set number\n'

<a id="config_files-a-user-granted-nothing-may-not-write-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-write-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 만들려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AutoGeneratedFileAdapter.create_default_auto_generated_file: user-1이 자기 auto-generated file 을 하나 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### switch_default

<a id="v2_default-a-user-granted-update-switches-the-default-auto-generated-file-of-a-path"></a>

#### [a-user-granted-update-switches-the-default-auto-generated-file-of-a-path](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_default.py): pass

UPDATE 를 받은 사용자가 같은 path 의 default 로 지정되지 않은 자기 auto-generated file 을 default 로 지정하면, 그 파일이 default 로 지정된 채 오고 이전 default 는 default 로 지정되지 않은 파일로 남습니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 자기 auto-generated file 에 대한 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - 자기 auto-generated file UPDATE 권한을 부여한 역할 배정
    - 역할 config-file-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 config-file-role-1: auto_generated_file 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 config-file-role-1 보유

When

- AutoGeneratedFileAdapter.switch_default: user-1이 default 로 지정되지 않은 자기 .vimrc auto-generated file 을 default 로 지정합니다

Then

- 지정한 파일이 default 로 지정된 채 응답으로 옵니다
  - id: 심어 둔 default 로 지정되지 않은 파일와 같다
  - entity_id: 심어 둔 default 로 지정되지 않은 파일와 같다
  - scope_type = 'user'
  - scope_id: 파일 주인의 id 와 같다
  - path = '.vimrc'
  - is_default = True
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="v2_default-a-user-granted-nothing-may-not-switch-the-default-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-switch-the-default-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_default.py): pass

권한을 받지 않은 사용자가 자기 auto-generated file 을 default 로 지정하려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 default 로 지정된 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 default 로 지정되지 않은 .vimrc auto-generated file 을 갖고 있습니다(권한 644, revision 1 의 내용 'set number\n'), 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다
  - default auto-generated file .vimrc: 그 경로의 default 로 지정됩니다
  - auto-generated file .vimrc: default 로 지정되지 않은 파일
  - auto-generated file .vimrc: 내용이 'set number\n' 이고 권한이 644 인 revision 하나를 갖습니다

When

- AutoGeneratedFileAdapter.switch_default: user-1이 default 로 지정되지 않은 자기 .vimrc auto-generated file 을 default 로 지정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

