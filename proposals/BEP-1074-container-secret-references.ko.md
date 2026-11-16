# 컨테이너 secret 참조

## 관련 이슈

- BA-7480(session 과 deployment 의 secret)
- BEP-1065(Encrypted Secret-Key Storage)에 의존한다. `SecretColumn` 과 key provider pool 을 제공한다
- 관련 BEP-1052(Scoped App Config Redesign). 같은 scope 축의 선례

## 1. 목표

### 1.1 문제

`environ` 이 API key 나 token 을 컨테이너에 전달하는 유일한 방법이다. `sessions.environ` 과 `deployment_revisions.environ` 은 평문 JSONB 이므로, session 이나 deployment 를 읽을 수 있는 사람은 값을 읽고 DB dump 도 값을 그대로 담는다.

같은 값을 계속 다시 제공해야 한다. session 은 자주 생성되고 버려지며, 그때마다 사용자가 key 를 다시 붙여 넣는다. 값을 변경하려면 그 값을 가진 모든 곳을 찾아야 하고, 어떤 값이 어디로 갔는지 기록하는 것이 없다.

### 1.2 이 BEP 가 정의하는 것

불변 version 으로 저장하는 이름 있는 secret, 그리고 session 과 deployment revision 이 **특정 version 을 참조**해 컨테이너에 주입받는 구조를 정의한다.

### 1.3 범위 밖

| 항목 | 이유 |
|---|---|
| 고정된 이름 있는 단일 자격 증명 | 컨테이너 레지스트리 비밀번호, HuggingFace token, 오브젝트 스토리지 access key, wsproxy token. 이 구조를 그것들에 재사용할 수 있고 그것이 더 나은 답이다. 1.5 를 참고한다 |
| `notification_channels.config` 안의 SMTP 비밀번호 | field 이름이 고정된 pydantic spec 이고 key/value 묶음이 아니다. 위와 같은 후속 작업이다 |
| dotfile | 파일 이름과 내용의 map 을 msgpack blob 으로 담고, environment variable 짝이 아니다 |
| 컨테이너 안의 평문 | 값을 environment variable 로 전달하는 동안 피할 수 없다. 3.6 을 참고한다 |
| revision preset 과 resource group 기본값 | 같은 구조를 그것들에도 적용할 수 있지만 merge 규칙을 먼저 정의해야 한다. 후속 작업 |
| 실행 중인 컨테이너에 값 적용 | container environment variable 은 생성 시 고정된다 |

### 1.4 강한 요구 사항

**revision 은 불변이어야 한다.** 한 revision 에서 시작한 replica 는 언제 시작했든 같은 값을 가져야 한다. 이 요구 사항이 아래 설계의 대부분을 정한다.

### 1.5 고정된 이름 있는 자격 증명으로 확장

registry token 과 storage access key 도 `secrets` 와 `secret_versions` 를 참조할 수 있고, 그것이 각자의 column 에 `SecretColumn` 을 두는 것보다 낫다. 암호문이 테이블 하나에 있으므로 재암호화 pass 가 다루는 범위가 자격 증명을 가진 domain 수와 무관하게 유지되고, rotation 이 한 곳에서 일어나며, 값을 읽기로는 내보내지 않는다는 규칙을 domain 마다 따로 따를 필요가 없다.

다만 참조의 의미가 다르다.

| 대상 | 참조 | 이유 |
|---|---|---|
| 컨테이너 주입 | 고정한 version | 1.4. 한 revision 의 replica 는 갈라지면 안 된다 |
| 외부 호출 자격 증명 | 최신 version | 호출마다 지금 유효한 값이 필요하다. snapshot 을 원하지 않는다 |

연결 방식도 다르다. 고정된 이름 있는 값에는 `env_key` 에 대응하는 것이 없으므로 참조가 3.1 의 binding 테이블이 아니라 그 row 의 foreign key column 에 있다.

**이 BEP 는 컨테이너 주입만 정의한다.** 아래의 version 고정 규칙은 그 범위 안에서 성립한다. 확장이 필요로 하는 global scope 와 최신 version 참조는 열어 둔다.

## 2. 영역별 현재 상태와 범위

### 2.1 저장

| | 항목 |
|---|---|
| ✅ | `SecretColumn`: 평문과 암호문이 한 column 에 함께 있는 자기 서술적 저장(`models/base.py`) |
| ✅ | `KeyProviderPool`: 암호화, 복호화, provider 선택. 이미 `RepositoryArgs` 로 모든 repository 에 주입된다 |
| ✅ | `sessions.environ`, `kernels.environ`, `deployment_revisions.environ`: 모두 평문 |
| ➕ | `secrets`: 이름과 소유 scope 를 담는 껍데기 |
| ➕ | `secret_versions`: 값이 있는 곳. 불변 |
| ➕ | `secret_bindings`: session 이나 revision 이 어느 environment variable 이름으로 어느 version 을 받는지 |

### 2.2 scope 와 권한

| | 항목 |
|---|---|
| ✅ | RBAC virtual scope 그래프. 모든 엔티티가 scope 를 겸한다 |
| ✅ | `app_config_fragments` 의 `(scope_type, scope_id)` 축과 CHECK 제약. 같은 모양의 선례 |
| ✅ | `models/mixins/timestamp.py`: `CreatedAtMixin` 과 `UpdatedAtMixin` 이 별도이므로 테이블이 필요한 것만 가진다 |
| ✅ | `domains` 는 `name` 을 key 로 사용하면서 별도의 `DomainID` GUID column 을 가진다 |
| ➕ | `SecretScopeType`: user, project, domain |
| ➕ | 생성은 scope 에 대한 쓰기 권한을, 참조는 읽기 권한을 요구한다는 규칙 |

### 2.3 revision 수명 주기

| | 항목 |
|---|---|
| ✅ | revision 은 불변이다. update spec 이 없고 `environ` 을 변경하면 새 revision 이 생긴다 |
| ✅ | revision 을 활성화하면 모든 replica 를 다시 생성한다. route 는 revision 에 묶인다 |
| ✅ | 오래된 revision 을 활성화하는 것이 rollback 이다. 전용 API 는 없다 |
| ✅ | `revision_history_limit` 의 기본값은 10 이고 그것을 넘은 revision 은 영구 삭제된다 |
| ➕ | revision 과 함께 secret binding 을 생성하는 경로 |

### 2.4 agent 로의 전달

| | 항목 |
|---|---|
| ✅ | `KernelCreationConfig["environ"]` 이 Callosum msgpack 으로 agent 에 전달된다 |
| ✅ | agent 가 `environ.txt` 를 작성하고 Docker `Env` 배열을 설정한다 |
| ✅ | `debug.log-kernel-config` 를 활성화하면 config 전체를 log 에 덤프한다. 유일한 log 유출이다 |
| ✅ | event 와 감사 로그는 environment variable 을 담지 않는다 |
| ➕ | RPC payload 에서 `environ` 과 별도 field 로 secret 을 보내고, log dump 에서 가린다 |

## 3. 구현 설계

### 3.1 테이블 셋

**`secrets`**: 엔티티다. 값을 가지지 않는다.

| column | 내용 |
|---|---|
| `id` | |
| `scope_type` | user, project, domain |
| `scope_id` | 소유 엔티티의 id. 셋 다 GUID 이므로 column 하나로 처리한다 |
| `name` | |

`UNIQUE(scope_type, scope_id, name)`. `member_of` 가 소유 scope 엔티티인 `EntityCreator` 로 선언한다. 자기 virtual scope node 를 프로비저닝하므로 공유와 권한 부여가 가능하다.

**`secret_versions`**: `secrets` 의 field 다. 값이 있는 유일한 곳이다.

| column | 내용 |
|---|---|
| `id` | |
| `secret_id` | |
| `version` | secret 안에서 1부터 증가한다 |
| `value` | `SecretColumn` |

`UNIQUE(secret_id, version)`. **update spec 을 선언하지 않는다.** 값을 변경하면 version 이 추가된다.

`version` 은 먼저 읽지 않고 INSERT 안에서 계산한다. 그 secret 의 가장 큰 번호에 1을 더하는 scalar subquery 다. INSERT 앞에 읽기가 없으므로 `secrets` row 에 lock 이 필요 없다. 동시에 들어온 두 INSERT 가 같은 번호를 고를 수 있고, unique 제약이 진 쪽을 거부하면 호출자가 재시도한다. `deployment_revisions.revision_number` 도 같은 방식이다.

row 를 잠그는 것이 더 나쁘다. `secrets` row 에 lock 을 걸면 version 추가가 그 secret 의 이름 변경과 경쟁한다.

**`secret_bindings`**: session 과 revision 의 field 다.

| column | 내용 |
|---|---|
| `id` | |
| `owner_type` | session, deployment revision |
| `owner_id` | |
| `env_key` | 이 값이 컨테이너에서 갖는 environment variable 이름 |
| `version_id` | `secret_versions.id` 에 대한 foreign key, `ON DELETE RESTRICT` |

`UNIQUE(owner_type, owner_id, env_key)`, `INDEX(owner_type, owner_id)`, `INDEX(version_id)`.

**참조 무결성이 필요한 쪽만 foreign key 다.** `version_id` 는 실제 foreign key 이므로 참조된 version 을 삭제하면 DB 가 거부한다. `INDEX(version_id)` 는 역방향 조회를 맡는다. 어떤 session 과 revision 이 한 version 을 사용하는지 찾는 것이 유출된 값에 대응하는 방법이다. owner 쪽은 두 타입에 걸치므로 enumerated column 이고, 그 정리는 3.9 가 다룬다.

`env_key` 가 binding 에 있으므로 **secret 하나를 여러 이름으로 전달할 수 있다.** secret 의 이름과 컨테이너 안에서의 이름은 별개다.

### 3.2 참조는 version 을 고정한다

binding 은 `secrets` 가 아니라 `secret_versions` 를 참조한다. 이것이 1.4 를 만족한다.

| | 결과 |
|---|---|
| 값 rotation | 새 version 이 생긴다. 기존 binding 은 이전 version 을 계속 참조한다 |
| 한 revision 의 replica | 언제 시작했든 같은 version 과 같은 값 |
| 새 값 적용 | 새 revision 이 새 version 을 참조한다. 명시적 rollout |
| Rollback | 오래된 revision 이 오래된 version 을 참조하므로 그 시점의 값으로 돌아간다 |

**컨테이너 주입에는 "최신" 참조를 허용하지 않는다.** 그것을 허용하면 값이 바뀐 뒤 다시 생성한 replica 만 새 값을 받고, 한 revision 안에서 값이 갈라진다. 그것은 revision 이 배포 단위라는 성질을 깨뜨린다. 외부 호출 자격 증명은 반대 요구를 가지며 1.5 가 다룬다.

생성 요청이 secret 을 지정할 수 있고, service 가 **그 시점의 최신 version** 을 binding 에 고정한다. version 을 직접 지정하는 것도 받는다. 재현 가능한 deployment 에 필요하다.

### 3.3 읽기는 값으로 응답하지 않는다

| 대상 | 응답 |
|---|---|
| secret | 이름, scope, version 목록(번호와 생성 시각), 각 version 의 참조 수 |
| session 또는 revision | environment variable 이름과, 각각이 어느 secret 의 어느 version 번호에서 왔는지 |

값은 어떤 경로로도 나가지 않는다. 가린 값도 마찬가지다. 가린 값을 생성하려면 복호화가 필요하고, 그것은 읽기 경로에 아무 이득 없이 복호화를 두는 일이다.

출처로 응답하는 것은 안전하고 필요하다. UI 가 "revision 추가" form 을 채워야 하는데 값을 읽을 수 없으므로 출처 이름이 값을 대신한다.

### 3.4 생성 시 기록하고 이후에 변경하지 않는다

session 이나 revision 의 binding 은 생성 요청에서만 생성한다.

session 은 생성되자마자 scheduling 에 들어가고, container environment variable 은 생성 시 고정된다. update API 를 두면 적용되지 않는 변경이 성공한 것처럼 보인다. revision 은 애초에 불변이다.

binding 생성은 owner 생성과 transaction 하나를 공유한다. `FieldCreator` 는 확정된 owner id 로 row 를 생성하는 spec 이고 `atomic_create_fields` 가 그것을 실행한다. 값 암호화는 key provider 를 호출하므로 transaction 이 열리기 전에 일어난다.

### 3.5 secret 값이 변경되면

**이미 있는 session 과 revision 은 영향을 받지 않는다.** binding 이 version 을 고정하기 때문이다. kernel 을 재시작하면 같은 version 을 읽으므로 같은 값을 받는다.

새 값을 사용하려면 새 session 을 생성하거나, deployment 라면 새 version 을 참조하는 새 revision 을 생성해 활성화한다. 후자가 rollout 이고, 변경된 값이 컨테이너에 이르는 유일한 길이다.

### 3.6 경계는 컨테이너 표면이다

복호화는 session 이 시작할 때 한 번 일어난다. 그 뒤 값은 오늘 `environ` 이 가는 경로를 따른다.

**컨테이너 안에서 secret 은 평문이고 그것을 차단할 수 없다.** environment variable 은 `/proc/<pid>/environ` 으로 읽을 수 있고 자식 process 가 상속한다. 저장과 전달 방식을 변경해도 달라지지 않는다. Kubernetes Secret 을 environment variable 로 주입하거나 외부 저장소에서 가져온 값을 내보내도 같은 곳에 놓인다. 차단하는 유일한 방법은 application 이 파일이나 API 를 직접 읽는 방식뿐이고, 그러면 값을 environment variable 로 전달한다는 요구 자체가 없어진다.

그래서 이 BEP 가 닫는 것은 **컨테이너 표면 밖**이고, 그것이 처음에 문제로 제기된 범위다.

| 지점 | 결과 |
|---|---|
| DB | secret 이 `sessions.environ` 이나 `kernels.environ` 에 기록되지 않는다. 암호문은 `secret_versions` 에만 있다 |
| 읽기 응답 | 3.3 |
| agent log | `debug.log-kernel-config` 의 config dump 는 secret 의 key 이름만 남긴다 |
| event 와 감사 로그 | environment variable 을 담은 적이 없다 |
| 컨테이너 안(environment variable, `environ.txt`, pickled restart config) | 평문. 위 이유로 경계 안이다 |
| `docker inspect`, host scratch 디렉터리 | 평문. 닫을 수 있지만 이 BEP 범위 밖이다(열린 질문) |

secret 이 `sessions.environ` 에 들어가지 않는 것은 무언가가 차단해서가 아니라 **secret 이 그 경로로 다니지 않기 때문이다.** session draft 는 binding 을 `environ` 과 별도로 가지며, session 과 kernel row 를 생성하는 spec 은 건드리지 않는다.

**RPC payload 에서 secret 을 `environ` 과 분리하는 이유는 log 가리기 하나다.** 값은 어차피 agent 에서 `environ` 로 합쳐지므로 manager 가 미리 합쳐도 결과는 같다. 하지만 그러면 agent 의 config dump 가 어느 항목이 secret 인지 구분할 수 없다. 분리가 동작하는 것은 dump 가 합치기 전에 일어나기 때문이므로, 그 순서를 code 에 고정해야 한다.

합친 뒤 secret field 를 config 에서 제거한다. 곧바로 재시작을 위해 config 전체를 직렬화해 컨테이너가 읽는 디렉터리에 저장하므로, 남겨 두면 같은 값을 두 번 저장한다.

### 3.7 이름 충돌

secret 은 environment variable 이름을 가진다. 두 경우를 생성 시 거부한다.

| | |
|---|---|
| `environ` 에 이미 있는 이름 | merge 우선순위를 정의하면 조용히 덮어쓴다. 거부하는 편이 낫다 |
| `BACKENDAI_` 로 시작하는 이름 | 시스템이 주입하는 variable 을 덮어쓴다 |

session 과 revision 모두 한 요청에서 `environ` 과 binding 을 생성하므로 검사도 거기서 한다.

### 3.8 시각

| 테이블 | 가지는 것 | 이유 |
|---|---|---|
| `secrets` | 생성, 변경 | 이름이 바뀔 수 있다 |
| `secret_versions` | 생성 | 값을 변경하는 동작이 없다 |
| `secret_bindings` | 생성 | 3.4 |

불변 row 의 updated-at column 은 변경되지 않는 column 이다. `deployment_revisions` 도 같은 이유로 생성 시각만 가진다.

### 3.9 삭제와 정리

| 대상 | 규칙 |
|---|---|
| version | 참조하는 binding 이 없을 때만 삭제할 수 있다. foreign key 가 강제한다 |
| secret | version 이 하나도 남지 않았을 때만 삭제할 수 있다 |
| session 또는 revision 삭제 | 그 binding 도 함께 삭제한다 |

version 은 rotation 마다 하나씩 쌓이지만 session 처럼 대량으로 생성되지 않으므로 크기는 문제가 아니다. 참조가 남아 있는 동안 값이 DB 에 있는 것은 옳다. 그 값을 사용하는 session 이나 revision 이 살아 있다는 의미다.

**자동 정리를 제공하지 않는다.** 참조 수가 0이 되는 순간이 삭제해도 안전한 순간이라는 보장이 없다. 그 수는 이 시스템이 아는 참조만 세고, 값이 외부에서 아직 유효한지는 말하지 않는다. 수로 줄이는 것도 여기서는 틀렸다. revision 은 다시 생성할 수 있는 파생물이지만 secret 값은 원본이고, 삭제하면 외부에서 다시 발급하는 것만이 복구 수단으로 남는다. 사용자가 삭제한다.

session 삭제 경로가 둘이다. v2 delete 는 `_teardown_entity` 를 거치므로 binding 삭제를 거기에 추가한다. retention policy 의 bulk delete 는 거치지 않으므로 자기 정리 항목이 필요하다. `entity_labels` 에도 이미 같은 누락이 있다.

version 은 retention policy 대상이 아니다. 그 framework 는 오래전에 terminal 상태에 이른 row 를 삭제하고, version 은 terminal 상태가 없고 시간이 지나도 낡지 않는다. 다만 session retention 이 간접적으로 작용한다. session 이 삭제되면 binding 도 함께 삭제되고, 그것이 version 을 삭제할 수 있게 한다. 그것을 위해 연결할 것은 없다.

## 4. 이전과 호환

새 테이블 셋이고 기존 column 은 바뀌지 않는다. `environ` 은 그대로다.

`environ` 에 평문으로 있는 secret 은 자동으로 변환하지 않는다. 시스템이 어느 항목이 secret 인지 구분할 방법이 없기 때문이다. 사용자가 secret 을 등록하고 다음 session 이나 revision 부터 참조로 전환한다.

`secret_versions.value` 를 BA-7044 의 재암호화 대상 목록에 항목 하나로 추가한다.

## 5. 구현 계획

| 단계 | 내용 |
|---|---|
| 1 | `secrets`, `secret_versions`: 엔티티, version, 세 scope, v2 표준 동작, API/CLI/SDK |
| 2 | `secret_bindings` 와 session 주입: 전달 경로, RPC 분리, log 가리기 |
| 3 | deployment revision binding |

2와 3은 1에 의존한다. 2와 3은 서로 독립이다.

## 결정 요약

| 결정 | 내용 |
|---|---|
| 저장 단위 | 불변 version 을 가진 이름 있는 secret. 값은 `secret_versions` 에만 있다 |
| 참조 형태 | 컨테이너 주입은 version 을 고정한다. 이 범위 안에 "최신" 참조는 없다 |
| 배포 단위 | revision. deployment 는 즉시 효력이 생기는 값을 가지고, secret 은 컨테이너 재생성을 요구한다 |
| scope | user, project, domain. 이 BEP 안에 global scope 는 없다 |
| 고정된 이름 있는 자격 증명 | 같은 구조를 참조로 재사용한다. 이 BEP 범위 밖 |
| 읽기 응답 | key 이름과 출처. 값도 가린 값도 아니다 |
| 변경 | 생성 시에만. session 이나 revision 의 binding 은 이후에 바뀌지 않는다 |
| 값 변경의 효과 | 기존 session 과 revision 은 영향받지 않는다. 새 session 이나 새 revision 이 값을 가진다 |
| version 번호 | INSERT 안의 subquery 와 unique 제약. row lock 없음 |
| version 정리 | 참조가 없을 때 사용자가 삭제한다. 자동 정리 없음, retention 대상 아님 |
| 노출 경계 | 컨테이너 표면. 바깥은 닫혀 있고 안은 environment variable 전달의 성질상 평문이다 |
| RPC 분리 | log 가리기 하나를 위한 분리다. 합친 뒤 config 에서 제거한다 |
| 이름 충돌 | `environ` 에 이미 있는 이름과 `BACKENDAI_` 접두사는 생성 시 거부한다 |

## 열린 질문

| 항목 | 내용 |
|---|---|
| project 와 domain secret 생성 | project secret 생성이 project admin 을 요구하는지, member 면 되는지 |
| 감사 | secret 참조를 감사 로그에 기록하는지, 어느 동작에 기록하는지 |
| global scope | 1.5 의 확장에 필요하다. 그곳의 생성을 superadmin 으로 제한하는지 |
| `docker inspect` 노출 | secret 을 컨테이너 `Env` 배열 대신 파일로 전달해 닫는다. 모든 컨테이너가 그 파일을 읽는 runner 를 거치는지 확인이 먼저다 |
| host 디스크의 평문 | secret 을 담는 디렉터리를 자체적으로 RAM 기반으로 구성하는지. 현재 RAM 기반 scratch mode 는 scratch 전체를 포괄하고 Linux 와 root 를 요구한다 |

## 참고

- BEP-1065 Encrypted Secret-Key Storage: `SecretColumn` 과 key provider
- BEP-1052 Scoped App Config Redesign: `(scope_type, scope_id)` 축의 선례
- BEP-1062 Virtual Scope RBAC Ownership Model
- 선례: GCP Secret Manager 의 secret 과 불변 version, AWS Secrets Manager 의 version 과 staging label, HashiCorp Vault KV v2 의 version 보존, 그리고 객체 이름을 변경해 rollout 을 트리거하는 Kubernetes 의 불변 Secret 관용구
