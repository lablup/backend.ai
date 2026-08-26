# 3. 실 동작 테스트

살아 있는 매니저에 요청을 보내 답을 좁힌 조사. 배선이 존재하고 아무도 호출하지 않는다는 것까지는
1부가 말할 수 있지만, 요청이 도착했을 때 무슨 일이 일어나는지는 실행만이 답한다. 세 조사의 관계와
진행 상태는 [README](./README.md)에 있다.

| | |
|---|---|
| Jira | BA-7489 |
| 기준 커밋 | `05e005d18b` |
| 대상 | 매니저 직결 API `http://127.0.0.1:8091`, HMAC 키페어 인증 |
| 주체 | superadmin, domain admin, 일반 사용자 2명, monitor |
| 방법 | 카탈로그의 각 액션을 실제로 도달하는 경로(REST v2 / GraphQL / CLI / v1 / bgtask)로 실행하고, 감사 행을 DB에서 직접 대조 |
| 범위 밖 | `session`(63), `deployment`(85) |
| 슬라이스 | 3개를 병렬로 실행 — 신원·권한 / 저장소·아티팩트 / 리소스·플랫폼 |

## 게이트란

`gate`는 카탈로그 컬럼이자 코드의 enum이다(`actions/types.py:51` `ActionGate` — "Who a wired
processor lets through"). **그 액션을 실행하려면 통과해야 하는 검사가 무엇인가**를 뜻한다.

| gate | 통과하는 사람 | 카탈로그 |
|---|---|---:|
| `permission` | 호출자의 권한을 검사해 통과한 사람만. 어디를 검사하는지는 `kind`가 정한다 | 561 |
| `public` | 인증만 됐으면 누구나 | 42 |
| `anonymous` | 아무 권한도 요구하지 않는다 | 5 |

## 판정 분류

**실패**는 액션이 제 일을 하지 못하는 것, **경고**는 동작은 하는데 선언·기록이 실제와 다르거나,
정보가 새거나, 의도를 알 수 없는 것이다. 행은 배타적으로 배정된다 — `E-`가 하나라도 붙으면 실패,
없이 `W-`만 붙으면 경고다. 한 행이 판정을 둘 이상 달 수 있다(`E-GATE+W-AUDIT`).

| 대분류 | 판정 | 뜻 | 질문 |
|---|---|---|---|
| **실패** | `E-GATE` | 사용자가 자기 자원에 접근하지 못한다 | Q2 |
| | `E-ARG` | 특정 인자 경로로는 제 일을 하지 못한다 — 다른 인자로는 성공한다 | Q1 |
| | `E-EXEC` | 도달하지만 어떤 주체·입력으로도 성공하지 않는다 | Q1 |
| | `E-BULK` | 벌크가 항목별로, 순서대로 답하지 않는다 | Q5 |
| **경고** | `W-GATE` | superadmin 전용인지 알기 어렵다 — 라우트가 RBAC보다 먼저 superadmin을 요구한다 | Q2 |
| | `W-LEAK` | 한 호출자가 없는 자원과 접근 권한이 없는 자원을 구별할 수 있다 | Q4 |
| | `W-GUARD` | 게이트는 선언대로 만나지만 그것을 정당화하는 근거가 런타임에 없다 | Q2 |
| | `W-AUDIT` | 감사 행이 카탈로그와 다르거나, 남아야 할 행이 없다 | Q3 |
| | `W-UNREACH` | 배선은 있으나 그것을 고르는 클라이언트 경로가 없다 | Q1 |
| **미실행** | `X` | 백엔드 부재 또는 공유 스택 보호 | — |

### 경계에서 정한 것

| 규칙 | 근거 |
|---|---|
| `W-UNREACH`는 경고다 | API가 없다는 것이지 동작이 깨진 것이 아니다. 1부가 `W`(죽은 배선)로 이미 판정한 것과 같은 대상이다 |
| `E-GATE`는 발견 내용으로만 올린다 | 사용자가 자기 자원에 접근하지 못한다고 **실증된** 18행만 `E-GATE`다. 나머지는 라우트가 superadmin을 요구한다는 사실까지만 확인됐으므로 경고에 둔다 |
| `global`/`permission`에서 비-admin이 403을 받는 것은 `성공`이다 | 2부 A절 — `GlobalActionProcessor`가 `SuperAdminActionValidator`를 고정한다. 선언된 게이트가 그대로 작동한 것이다 |
| `E-EXEC`와 `W-UNREACH`를 나눈다 | 수정이 다르다. `W-UNREACH`는 배선을 잇거나 지우는 일이고, `E-EXEC`는 결함을 고치는 일이다 |
| `W-LEAK`은 한 호출자 기준이다 | admin이 404를 받고 비-admin이 403을 받는 것은 게이트가 둘일 뿐 누출이 아니다 |

### `W-LEAK` — 무엇이 새는가

응답이 **없는 자원**과 **있지만 내 것이 아닌 자원**을 다르게 답하면, 한 호출자가 그 차이만으로
자기 것이 아닌 자원의 존재를 확인할 수 있다. id를 하나씩 넣어 보면 실재하는 id의 목록이 나온다.

10행이 네 모양으로 나뉜다.

| 모양 | 무엇이 일어나는가 | 행 |
|---|---|---:|
| 권한 검사 이전에 404 | 없는 id는 소유 검사에 닿기 전에 404가 나고, 있는 id는 검사까지 가서 403이 난다. 두 코드가 곧 존재 여부다 | 5 |
| 거부 응답이 데이터를 싣는다 | 403 본문이 소유자 UUID를 담아, 막으면서 누구 것인지 알려 준다 | 2 |
| 무인증 표면의 계정 열거 | `authorize`는 401 본문이 같아도 `traceback`이 미존재 계정과 오답 비밀번호를 가르고, `signup`은 응답이 기존 이메일과 신규 이메일로 갈린다 | 2 |
| 목록은 막고 낱건은 준다 | `search_users_by_domain`은 자기 도메인 목록을 거부하는데 `get_user`가 같은 행을 한 건씩 내준다 | 1 |

앞의 두 모양 7행은 원인이 하나다 — **owner lookup이 게이트보다 먼저 돈다.** 액션 7개를 각각
고치는 것이 아니라 순서를 뒤집는 한 번의 수정일 가능성이 높다.

한 호출자 기준이라는 것이 이 판정의 경계다. admin이 404를 받고 비-admin이 403을 받는 것은
게이트가 둘일 뿐 누출이 아니다. 그 기준을 적용해 한 슬라이스는 자기 집계를 40여 건에서 1건으로
내렸다. 그래서 10행은 **하한이다** — 모든 `single_entity`·`lookup` 액션에 대해 한 호출자로
(없는 id / 남의 id / 내 id) 셋을 넣어 비교하는 전수 조사는 하지 못했다.

`E-ARG`는 레거시 경로 조사에서 필요해진 판정이다. `E-EXEC`가 "어떤 입력으로도 성공하지 않는다"인
반면 `E-ARG`는 특정 인자 경로만 망가진 것이다. BA-7501이 원형 — resource preset을 id로는 찾고
이름으로는 못 찾는다.

`W-GUARD`는 1부의 `G`와 같은 뜻이다. 1부가 `G`로 판정한 harbor webhook이 3부에서도 같은 판정이라,
두 문서를 오가는 독자가 같은 액션에서 같은 결론을 본다.

`감사` 컬럼의 `행 없음 (성공 read — 정책상 정상)`은 `W-AUDIT`가 아니다. `AuditLogPolicy`는 모든
변경과 모든 실패를 기록하고, 성공한 read는 opt-in된 경우만 기록한다. 이 배포에는 opt-in된 read가
없다.

## 총계

| 항목 | 수 |
|---|---:|
| 카탈로그 행 (`session`·`deployment` 제외) | 506 |
| 이 문서의 행 수 | 506 |
| — 실패 | 39 |
| — 경고 | 225 |
| — 미실행 | 26 |
| — 성공 | 216 |

위 수치는 카탈로그 경로 506행이다. 여기에 더해 레거시 GraphQL 경로 48행을 concern별 하위 섹션에 실었다 — 실패 8, 경고 20, 미실행 2, 성공 18. 이미 센 액션의 다른 경로이므로 총계에 더하지 않는다.

행은 배타적으로 배정된다 — `E-`가 하나라도 붙으면 실패, 없이 `W-`만 붙으면 경고다.

`vfolder`는 어댑터 수준의 bulk 루프 2행을 따로 세어 카탈로그 68행에 대해 70행이다.

## 판정별

| 대분류 | 판정 | 뜻 | 질문 | 건수 |
|---|---|---|---|---:|
| 실패 | `E-GATE` | 사용자가 자기 자원에 접근하지 못한다 | Q2 | 18 |
| 실패 | `E-EXEC` | 도달하지만 어떤 주체·입력으로도 성공하지 않는다 | Q1 | 11 |
| 실패 | `E-BULK` | 벌크가 항목별로, 순서대로 답하지 않는다 | Q5 | 11 |
| 경고 | `W-GATE` | superadmin 전용인지 알기 어렵다 — 라우트가 RBAC보다 먼저 superadmin을 요구한다 | Q2 | 117 |
| 경고 | `W-LEAK` | 한 호출자가 없는 자원과 접근 권한이 없는 자원을 구별할 수 있다 | Q4 | 10 |
| 경고 | `W-GUARD` | 게이트는 선언대로 만나지만 그것을 정당화하는 근거가 런타임에 없다 | Q2 | 3 |
| 경고 | `W-AUDIT` | 감사 행이 카탈로그와 다르거나, 남아야 할 행이 없다 | Q3 | 115 |
| 경고 | `W-UNREACH` | 배선은 있으나 그것을 고르는 클라이언트 경로가 없다 | Q1 | 32 |
| 미실행 | `X` | 백엔드 부재 또는 공유 스택 보호 | — | 26 |
| 성공 | — | 다섯 축 어디에도 걸리지 않음 | — | 216 |

한 행이 판정을 둘 이상 달 수 있어 판정별 합은 행 수보다 크다.

| 복합 판정 | 건수 |
|---|---:|
| `W-GATE+W-AUDIT` | 34 |
| `E-BULK+W-AUDIT` | 4 |
| `E-BULK+W-GATE` | 3 |
| `E-EXEC+W-AUDIT` | 2 |
| `E-EXEC+W-GATE` | 2 |
| `E-GATE+W-AUDIT` | 2 |
| `E-GATE+E-EXEC` | 1 |
| `E-GATE+W-LEAK` | 1 |
| `W-GUARD+W-AUDIT` | 1 |
| `W-LEAK+W-AUDIT` | 1 |
| `W-LEAK+W-GUARD+W-AUDIT` | 1 |

## concern별 행 수

| concern | 실패 | 경고 | 미실행 | 성공 | 합계 |
|---|---:|---:|---:|---:|---:|
| [app_config](#app-config) | 1 | 6 | 0 | 14 | 21 |
| [artifact_registry](#artifact-registry) | 2 | 43 | 5 | 21 | 71 |
| [container_registry](#container-registry) | 3 | 16 | 7 | 13 | 39 |
| [label](#label) | 1 | 3 | 0 | 1 | 5 |
| [metric](#metric) | 0 | 4 | 0 | 10 | 14 |
| [notification_center](#notification-center) | 0 | 10 | 1 | 2 | 13 |
| [organization](#organization) | 13 | 51 | 0 | 35 | 99 |
| [rbac](#rbac) | 4 | 12 | 0 | 3 | 19 |
| [resource_group](#resource-group) | 4 | 25 | 7 | 41 | 77 |
| [resource_policy](#resource-policy) | 2 | 15 | 0 | 3 | 20 |
| [system](#system) | 0 | 14 | 1 | 30 | 45 |
| [vfolder](#vfolder) | 5 | 21 | 5 | 39 | 70 |
| [visibility](#visibility) | 4 | 5 | 0 | 4 | 13 |
| **합계** | **39** | **225** | **26** | **216** | **506** |

컬럼은 `backend.ai mgr ops list`의 것에서 각 섹션 제목이 대신하는 `concern`과 `backing`을 빼고, 실행 결과 넷(`경로`·`admin`·`비-admin`·`감사`)과 `판정`·`사유`를 더한 구성이다.

## app_config

21행 — 실패 1, 경고 6, 미실행 0, 성공 14.

### app_config — 성공 외 (7행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `app_config_allow_list` | `create` | `create_app_config_allow_list` | `global` | `permission` | cli:admin app-config-allow-list create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `app_config_definition` | `create` | `create_app_config_definition` | `global` | `permission` | cli:admin app-config-definition create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `app_config_allow_list` | `get` | `bulk_get_app_config_allow_lists` | `bulk` | `permission` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 선택하는 필드 없음 — DataLoader만 배선, GraphQL `appConfigAllowList`는 create 페이로드뿐 |
| `app_config_definition` | `get` | `bulk_get_app_config_definitions` | `bulk` | `permission` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 선택하는 필드 없음 — DataLoader만 배선, GraphQL `appConfigDefinition`은 create 페이로드뿐 |
| `app_config` | `search` | `search_app_configs` | `scope` | `permission` | rest:POST /v2/app-config/my/get | ok | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `E-GATE` | 자기 스코프 거부 — 본인 user 스코프 READ가 superadmin 외 전원 거부 (F6) |
| `app_config_fragment` | `search` | `search_app_config_fragments` | `scope` | `permission` | rest:POST /v2/app-config-fragments/scoped/by-names | ok | ok (타 사용자 스코프 포함) | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 스코프 미구속 — 호출자가 준 scope를 그대로 owner로 써 임의 사용자 스코프를 읽는다 (F1) |
| `app_config_fragment` | `upsert` | `global_bulk_upsert_app_config_fragments` | `global` | `permission` | rest:POST /v2/app-config-fragments/scoped/bulk-upsert (public scope) | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) / public 스코프 쓰기 1회에 global·scope 두 행이 남는다 |

### app_config — 성공 (14행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `app_config_fragment` | `get` | `bulk_get_app_config_fragments` | `bulk` | `permission` | cli:app-config-fragment get / my app-config-fragment get | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `app_config_allow_list` | `get` | `get_app_config_allow_list` | `single_entity` | `permission` | cli:admin app-config-allow-list get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `app_config_definition` | `get` | `get_app_config_definition` | `single_entity` | `permission` | cli:admin app-config-definition get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `app_config_fragment` | `get` | `get_app_config_fragment` | `single_entity` | `permission` | rest:GET /v2/app-config-fragments/{id} | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `app_config_fragment` | `purge` | `bulk_purge_app_config_fragments` | `bulk` | `permission` | cli:app-config-fragment bulk-purge ... ... | ok | 부분 성공 — 거부 항목은 `failed` | 일치 (entity_type 개별 미확인) | `성공` | 벌크 정상 — 항목별 `items`/`failed`, 비-admin에게 거부와 miss가 같은 문구 |
| `app_config_allow_list` | `purge` | `purge_app_config_allow_list` | `single_entity` | `permission` | cli:admin app-config-allow-list purge | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `app_config_definition` | `purge` | `purge_app_config_definition` | `single_entity` | `permission` | cli:admin app-config-definition purge | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `app_config_fragment` | `purge` | `purge_app_config_fragment` | `single_entity` | `permission` | cli:app-config-fragment purge | ok | 403 not-enough-permission | 일치 (entity_type 개별 미확인) | `성공` | — |
| `app_config_allow_list` | `search` | `admin_search_app_config_allow_lists` | `global` | `permission` | cli:admin app-config-allow-list search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `app_config_definition` | `search` | `global_search_app_config_definitions` | `global` | `permission` | cli:admin app-config-definition search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `app_config_fragment` | `search` | `admin_search_app_config_fragments` | `global` | `permission` | cli:admin app-config-fragment search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `app_config` | `search` | `anonymous_search_app_configs` | `scope` | `anonymous` | rest:POST /v2/app-config/public/get (no auth) | ok | ok (무인증) | 행 없음 (성공 read — 정책상 정상) | `성공` | anonymous 게이트 — 무인증으로 도달, 선언대로 |
| `app_config_allow_list` | `update` | `update_app_config_allow_list` | `single_entity` | `permission` | cli:admin app-config-allow-list update | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `app_config_fragment` | `upsert` | `bulk_upsert_app_config_fragments` | `scope` | `permission` | cli:app-config-fragment update / my app-config-fragment update | ok | ok | 일치 | `성공` | — |

## artifact_registry

71행 — 실패 2, 경고 43, 미실행 5, 성공 21.

### artifact_registry — 성공 외 (50행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `artifact` | `create` | `delegate_import_artifact_revision_batch` | `global` | `permission` | `gql:delegateImportArtifacts` | 미실행 | 403 user_auth_forbidden | 해당 없음 | `X` | 백엔드 부재 — 위임 대상 reservoir 인스턴스가 없다 |
| `artifact` | `create` | `delegate_scan_artifacts` | `global` | `permission` | `gql:delegateScanArtifacts` | 미실행 | 403 user_auth_forbidden | 해당 없음 | `X` | 백엔드 부재 — 위임 대상 reservoir 인스턴스가 없다 |
| `artifact` | `delete` | `delete_artifacts` | `global` | `permission` | `cli:artifact delete` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `artifact`) | `E-BULK+W-AUDIT` | entity type 불일치 — 감사 `global`. 없는 id 두 개에 200 `{"artifacts": []}` + `status=success`, 항목별 응답 없음 (F9) |
| `artifact` | `get` | `get_artifact` | `single_entity` | `permission` | `cli:artifact get` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `artifact` | `search` | `get_artifact_revisions` | `single_entity` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 호출자가 없다 |
| `artifact` | `lookup` | `lookup_artifact_revision_owner` | `lookup` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 직접 경로 없음 — revision 액션 내부에서만 실행된다 |
| `artifact` | `lookup` | `lookup_bulk_artifact_revision_owner` | `lookup` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `artifact` | `update` | `restore_artifacts` | `global` | `permission` | `cli:artifact restore` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` **and operation=update** (a DELETED->ALIVE transition`) | `E-BULK+W-AUDIT` | soft delete 역전이 — DELETED→ALIVE인데 감사 `operation=update`. entity type도 `global`. 항목별 응답 없음 (F9) |
| `artifact` | `get` | `retrieve_models` | `global` | `permission` | `gql:scanArtifactModels` | ok | 403 user_auth_forbidden | 일치 | `W-AUDIT` | entity type 불일치 — 감사 `global` |
| `artifact` | `create` | `scan_artifacts` | `global` | `permission` | `gql:scanArtifacts` | ok | 403 user_auth_forbidden | 일치 | `W-AUDIT` | 레지스트리 이름 결합 — 프록시 TOML에 없는 이름이면 불투명한 404. entity type도 `global` (F3) |
| `artifact` | `update` | `update_artifact` | `single_entity` | `permission` | `cli:artifact update` | ok | 403 backendai_generic_forbidden | 일치 (`update_artifact \| artifact \| update \| single_entity`) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact` | `update` | `upsert_artifacts` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 프로세서 우회 — 서비스가 자기 메서드를 직접 호출해 게이트·감사가 건너뛰어진다 (`artifact/service.py:334,651`) |
| `artifact_registry` | `create` | `create_hugging_face_registry` | `global` | `permission` | `cli:huggingface-registry create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 카탈로그 `artifact_registry` / 감사 `global` |
| `artifact_registry` | `create` | `create_reservoir_registry` | `global` | `permission` | `cli:reservoir-registry create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `artifact_registry` | `delete` | `delete_hugging_face_registry` | `single_entity` | `permission` | `cli:huggingface-registry delete` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `artifact_registry` | `delete` | `delete_reservoir_registry` | `single_entity` | `permission` | `cli:reservoir-registry delete` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_registry` | `get` | `get_hugging_face_registry` | `single_entity` | `permission` | `cli:huggingface-registry get` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_registry` | `get` | `get_reservoir_registry` | `single_entity` | `permission` | `cli:reservoir-registry get` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_registry` | `search` | `list_hugging_face_registry` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 라우트·CLI·GQL 어디에도 호출자가 없다 |
| `artifact_registry` | `search` | `list_reservoir_registries` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 같은 사유 |
| `artifact_registry` | `lookup` | `lookup_artifact_registry` | `lookup` | `public` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 직접 경로 없음 — 다른 액션의 소유자 해석 단계에서만 실행된다 |
| `artifact_registry` | `update` | `update_hugging_face_registry` | `single_entity` | `permission` | `cli:huggingface-registry update` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_registry` | `update` | `update_reservoir_registry` | `single_entity` | `permission` | `cli:reservoir-registry update` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_revision` | `update` | `approve_artifact_revision` | `single_entity` | `permission` | `cli:artifact revision approve` | 400 artifact_access_bad-request | 403 backendai_generic_forbidden | 일치 (entity_id가 revision이 아닌 소유 artifact) | `W-GATE` | 라우트 게이트 선점 — 같은 사유. 감사 `entity_id`는 revision이 아니라 소유 artifact를 가리킨다 |
| `artifact_revision` | `create` | `associate_with_storage` | `single_entity` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 프로세서 우회 — 서비스가 직접 호출한다 (`revision/service.py:586`) |
| `artifact_revision` | `update` | `cancel_import` | `single_entity` | `permission` | `cli:artifact revision cancel-import` | ok | 403 backendai_generic_forbidden | 일치 (entity_id가 소유 artifact) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다. 더해 상태 가드가 없어 어떤 상태든 SCANNED로 되돌리고, REJECTED 판정을 뒤집거나 AVAILABLE이면 파일을 고아로 남긴다 (F2) |
| `artifact_revision` | `delete` | `cleanup_artifact_revision` | `single_entity` | `permission` | `cli:artifact revision cleanup` | ok | 403 backendai_generic_forbidden | 일치 (entity_id가 소유 artifact) | `W-GATE` | 라우트 게이트 선점 — 같은 사유. AVAILABLE에서만 동작해 `cancel_import` 뒤에는 회수 경로가 사라진다 (F2) |
| `artifact_revision` | `delete` | `disassociate_with_storage` | `single_entity` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 프로세서 우회 — 서비스가 직접 호출한다 (`revision/service.py:676`) |
| `artifact_revision` | `get` | `get_artifact_revision` | `single_entity` | `permission` | `cli:artifact revision get` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `artifact_revision` | `get` | `get_artifact_revision_readme` | `single_entity` | `permission` | `gql/rest (blocked upstream)` | 미실행 | 미실행 | 해당 없음 | `X` | 스키마 형태 불일치 — GQL 필드 형태를 맞추지 못해 구동하지 못했다 |
| `artifact_revision` | `get` | `get_artifact_revision_verification_result` | `single_entity` | `permission` | `gql/rest (blocked upstream)` | 미실행 | 미실행 | 해당 없음 | `X` | 스키마 형태 불일치 — 같은 사유 |
| `artifact_revision` | `get` | `get_download_presigned_url` | `single_entity` | `permission` | `gql:getPresignedDownloadUrl` | ok | 403 user_auth_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — 같은 사유. 서명 URL은 감사 행 없이 발급된다 |
| `artifact_revision` | `get` | `get_download_progress` | `single_entity` | `permission` | `gql/rest (blocked upstream)` | 미실행 | 미실행 | 해당 없음 | `X` | 관측 시점 부재 — 진행 중인 import bgtask를 잡아야 한다 |
| `artifact_revision` | `update` | `get_upload_presigned_url` | `single_entity` | `permission` | `gql:getPresignedUploadUrl` | 403 artifact_update_forbidden | 403 user_auth_forbidden | 일치 (status=error) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `artifact_revision` | `create` | `import_artifact_revision` | `single_entity` | `permission` | `gql:importArtifacts` | ok | 403 user_auth_forbidden | 일치 (entity_id가 소유 artifact) | `W-GATE` | 라우트 게이트 선점 — 같은 사유. bgtask 기반이며 `tasks { taskId }`로 반환된다 |
| `artifact_revision` | `update` | `reject_artifact_revision` | `single_entity` | `permission` | `cli:artifact revision reject` | ok | 403 backendai_generic_forbidden | 일치 (entity_id가 소유 artifact) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `object_storage` | `create` | `create_object_storage` | `global` | `permission` | `cli:object-storage create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `object_storage`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `object_storage` / 감사 `global` |
| `object_storage` | `get` | `get_object_storage` | `single_entity` | `permission` | `cli:object-storage get` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `object_storage` | `purge` | `purge_object_storage` | `single_entity` | `permission` | `cli:object-storage delete` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `object_storage` | `update` | `update_object_storage` | `single_entity` | `permission` | `cli:object-storage update` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `storage_namespace` | `lookup` | `lookup_storage_namespace` | `lookup` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 직접 경로 없음 — 같은 사유 |
| `storage_namespace` | `create` | `register_storage_namespace` | `global` | `permission` | `cli:storage-namespace register` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `storage_namespace`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `storage_namespace` / 감사 `global`. 존재하지 않는 `storage_id`도 그대로 받는다 (F14) |
| `storage_namespace` | `purge` | `unregister_storage_namespace` | `single_entity` | `permission` | `cli:storage-namespace unregister` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `vfs_storage` | `create` | `create_vfs_storage` | `global` | `permission` | `cli:vfs-storage create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `vfs_storage`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `vfs_storage` / 감사 `global` |
| `vfs_storage` | `get` | `get_vfs_storage` | `single_entity` | `permission` | `cli:vfs-storage get` | ok | 403 backendai_generic_forbidden | 일치 (entity_type `vfs_storage`) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 먼저 걸려 선언된 단일 엔티티 RBAC 검사가 실행되지 않는다 |
| `vfs_storage` | `lookup` | `lookup_vfs_storage` | `lookup` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 직접 경로 없음 — 다른 액션의 소유자 해석 단계에서만 실행된다 |
| `vfs_storage` | `purge` | `purge_vfs_storage` | `single_entity` | `permission` | `cli:vfs-storage delete` | 404 on | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `vfs_storage` | `update` | `set_vfs_quota_scope` | `global` | `permission` | `rest-v1:POST /admin/quota-scopes/set and gql:set_quota_scope` | 200 both | 403 on | 불일치 — REST 경로는 entity_type이 `global`, 레거시 GQL 경로는 행 없음 | `W-AUDIT` | 프로세서 우회 — REST 경로는 행을 남기나 레거시 GQL `set_quota_scope`는 프로세서를 건너뛰어 행도 RBAC 검사도 없다 (F16.4) |
| `vfs_storage` | `delete` | `unset_vfs_quota_scope` | `global` | `permission` | `rest-v1:POST /admin/quota-scopes/unset and gql:unset_quota_scope` | 200 both | 403 on | 불일치 — REST 경로는 entity_type이 `global`, 레거시 GQL 경로는 행 없음 | `W-AUDIT` | 프로세서 우회 — 같은 사유 (F16.4) |
| `vfs_storage` | `update` | `update_vfs_storage` | `single_entity` | `permission` | `cli:vfs-storage update` | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |

### artifact_registry — 성공 (21행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `artifact` | `get` | `retrieve_model` | `global` | `permission` | `gql:scanArtifactModels (single-model input)` | ok | 403 user_auth_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact` | `search` | `search_artifact_revisions` | `global` | `permission` | `gql:artifactRevisions` | ok | 403 user_auth_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact` | `search` | `search_artifacts` | `global` | `permission` | `cli:admin artifact search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact` | `search` | `search_artifacts_with_revisions` | `global` | `permission` | `gql:artifacts` | ok | 403 user_auth_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `get` | `get_artifact_registry_meta` | `single_entity` | `permission` | `cli:artifact-registry get / rest:GET /v2/artifact-registries/{id}` | ok | 403 role_create_forbidden | 일치 (entity_type `artifact_registry`) | `성공` | — |
| `artifact_registry` | `get` | `get_artifact_registry_metas` | `global` | `permission` | `gql:artifactRegistryMetas` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `get` | `get_hugging_face_registries` | `global` | `permission` | `gql (list resolver)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `get` | `get_reservoir_registries` | `global` | `permission` | `gql (list resolver)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `search` | `search_artifact_registries` | `global` | `permission` | `gql:artifactRegistries` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `search` | `search_hugging_face_registries` | `global` | `permission` | `cli:huggingface-registry search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `artifact_registry` | `search` | `search_reservoir_registries` | `global` | `permission` | `cli:reservoir-registry search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 비밀값 노출 — 응답 본문에 `secret_key`가 평문으로 실린다 (F13) |
| `object_storage` | `get` | `bulk_get_object_storages` | `bulk` | `permission` | `gql:node(id:) via DataLoader (aliased batch)` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `object_storage` | `search` | `list_object_storages` | `global` | `permission` | `gql:objectStorages` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `object_storage` | `search` | `search_object_storages` | `global` | `permission` | `cli:object-storage search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 비밀값 노출 — 응답 본문에 `secret_key`가 평문으로 실린다 (F13) |
| `storage_namespace` | `get` | `bulk_get_storage_namespaces` | `bulk` | `permission` | `gql:node(id:) via DataLoader (aliased batch)` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `storage_namespace` | `search` | `search_storage_namespaces` | `global` | `permission` | `cli:storage-namespace search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `storage_namespace` | `search` | `search_storage_namespaces_of_storage` | `global` | `permission` | `cli:storage-namespace get-by-storage` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 참조 무결성 없음 — 존재하지 않는 스토리지의 고아 행을 그대로 돌려준다 (F14) |
| `vfs_storage` | `get` | `get_vfs_quota_scope` | `global` | `permission` | `rest-v1:GET /admin/quota-scopes/{host}/{qsid}` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfs_storage` | `search` | `list_vfs_storages` | `global` | `permission` | `cli:vfs-storage list-all` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfs_storage` | `search` | `search_vfs_quota_scopes` | `global` | `permission` | `rest-v1:POST /admin/quota-scopes/search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfs_storage` | `search` | `search_vfs_storages` | `global` | `permission` | `cli:vfs-storage search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |

## container_registry

39행 — 실패 3, 경고 16, 미실행 7, 성공 13.

### container_registry — 성공 외 (26행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `container_registry` | `delete` | `clear_images` | `global` | `permission` | `gql_legacy:clear_images / rest-v1:POST /container-registries/clear` | ok | 200 ok:false | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 카탈로그 `container_registry` / 감사 `global`. 거부가 200 본문의 `ok:false`로 온다 (F16.3) |
| `container_registry` | `create` | `create_container_registry` | `global` | `permission` | `cli:admin container-registry create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `container_registry`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `container_registry` / 감사 `global` |
| `container_registry` | `create` | `create_registry_quota` | `global` | `permission` | `gql_legacy (harbor quota mutations)` | 미실행 | 미실행 | 해당 없음 | `X` | 백엔드 부재 — Harbor 인스턴스가 없다 |
| `container_registry` | `delete` | `delete_container_registry` | `global` | `permission` | `cli:admin container-registry delete` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `container_registry` | `delete` | `delete_registry_quota` | `global` | `permission` | `gql_legacy (harbor quota mutations)` | 미실행 | 미실행 | 해당 없음 | `X` | 백엔드 부재 — Harbor 인스턴스가 없다 |
| `container_registry` | `update` | `handle_harbor_webhook` | `global` | `anonymous` | `rest-v1:POST /container-registries/webhook/harbor` | 500 backendai_generic_internal-error | 해당 없음 | 일치 (`handle_harbor_webhook\|global\|update\|global`, status=error) | `W-GUARD+W-AUDIT` | 게이트 근거 미흡 — `anonymous`를 정당화하는 것은 웹훅 시크릿 비교인데, 그 비교가 `extra.webhook_auth_header`가 있을 때만 실행된다(`service.py:214`). 이 배포의 네 레지스트리 모두 해당 값이 null이라 검사가 한 번도 돌지 않고, 무자격 호출자가 지정한 호스트로 매니저가 나간다. entity type도 `global` (F4) |
| `container_registry` | `get` | `read_registry_quota` | `global` | `permission` | `gql_legacy (harbor quota mutations)` | 미실행 | 미실행 | 해당 없음 | `X` | 백엔드 부재 — Harbor 인스턴스가 없다 |
| `container_registry` | `update` | `rescan_images` | `global` | `permission` | `gql_legacy:rescan_images / rest-v1:POST /container-registries/rescan` | ok | 200 ok:false | 불일치 — entity_type이 `global` (카탈로그 `container_registry`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `container_registry` / 감사 `global`. 거부가 403이 아니라 200 본문의 `ok:false`로 온다. bgtask 기반 (F16.3) |
| `container_registry` | `update` | `update_container_registry` | `global` | `permission` | `cli:admin container-registry update / gql:modify_container_registry` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `container_registry` | `update` | `update_registry_quota` | `global` | `permission` | `gql_legacy (harbor quota mutations)` | 미실행 | 미실행 | 해당 없음 | `X` | 백엔드 부재 — Harbor 인스턴스가 없다 |
| `image` | `create` | `alias_image` | `global` | `permission` | `gql_legacy:alias_image` | ok | 200 ok:false | 불일치 — entity_type이 `global` (`alias_image\|global\|create\|global``) | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `image` | `create` | `alias_image_by_id` | `global` | `permission` | `cli:admin image alias create` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` (카탈로그 `image`) | `W-AUDIT` | entity type 불일치 — 카탈로그 `image` / 감사 `global` |
| `image` | `delete` | `clear_image_custom_resource_limit` | `global` | `permission` | `gql_legacy:clear_image_custom_resource_limit` | ok | 200 ok:false | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `image` | `delete` | `clear_image_custom_resource_limit_by_id` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 호출자가 없다 |
| `image` | `delete` | `dealias_image` | `global` | `permission` | `gql_legacy:dealias_image` | ok | 200 ok:false | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `image` | `delete` | `forget_image` | `global` | `permission` | `gql_legacy:forget_image` | ok | 200 ok:false | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `image` | `create` | `preload_image` | `global` | `permission` | `gql_legacy:preload_image` | 200 not-implemented | 200 not-implemented | 해당 없음 | `E-EXEC` | 실행 불능 — 뮤테이션 경로는 살아 있으나 어떤 입력에도 `Not implemented.`만 돌려준다 |
| `image` | `purge` | `purge_image` | `global` | `permission` | `bgtask (image purge task)` | 미실행 | 해당 없음 | 해당 없음 | `X` | 직접 구동 불가 — 이미지 purge bgtask에서만 호출된다 |
| `image` | `purge` | `purge_images` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — bgtask는 단수 `purge_image`를 쓴다 |
| `image` | `restore` | `restore_image_by_id` | `single_entity` | `permission` | `rest:POST /v2/images/restore` | 404 image_read_not-found | 403 backendai_generic_forbidden | 일치 (`restore_image_by_id \| image \| restore`, status=error) | `E-EXEC+W-GATE` | 실행 불능 — `ImageRow.get`의 기본 상태 필터가 ALIVE라 복구 대상인 DELETED 이미지를 영영 찾지 못한다. 라우트 게이트 선점도 함께 (F8) |
| `image` | `create` | `scan_image` | `global` | `permission` | `gql_legacy (single-image scan)` | 미실행 | 403 | 해당 없음 | `X` | 외부 영향 회피 — 제3자 레지스트리로 나가는 스캔이라 구동하지 않았다 |
| `image` | `update` | `set_image_resource_limit_by_id` | `global` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 호출자가 없다 |
| `image` | `delete` | `unload_image` | `global` | `permission` | `gql_legacy:unload_image` | 200 not-implemented | 200 not-implemented | 해당 없음 | `E-EXEC` | 실행 불능 — 같은 사유 |
| `image` | `delete` | `untag_image_from_registry` | `global` | `permission` | `gql_legacy:untag_image_from_registry` | 미실행 | 403 | 해당 없음 | `X` | 백엔드 부재 — Harbor 인스턴스가 없다 |
| `image` | `update` | `update_image` | `global` | `permission` | `gql_legacy:modify_image` | ok | 200 ok:false | 불일치 — entity_type이 `global` (`update_image\|global\|update\|global``) | `W-AUDIT` | entity type 불일치 — 같은 사유 |
| `image` | `update` | `update_image_by_id` | `global` | `permission` | `cli:admin image update` | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global` | `W-AUDIT` | entity type 불일치 — 같은 사유 |

### container_registry — 성공 (13행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `image` | `delete` | `forget_image_by_id` | `single_entity` | `permission` | `cli:admin image forget` | ok | 403 backendai_generic_forbidden | 일치 (`forget_image_by_id\|image\|delete\|single_entity`, entity_id recorded) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `image` | `purge` | `purge_image_by_id` | `single_entity` | `permission` | `cli:admin image purge` | 404 on | 403 backendai_generic_forbidden | 일치 (entity_type `image`) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `container_registry` | `get` | `get_container_registries` | `global` | `permission` | `rest-v1:GET /container-registries` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `container_registry` | `get` | `load_all_container_registries` | `global` | `permission` | `gql_legacy (image resolvers)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `container_registry` | `get` | `load_container_registries` | `global` | `permission` | `rest-v1:GET /container-registries/load` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `container_registry` | `search` | `search_container_registries` | `global` | `permission` | `cli:admin container-registry search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `search` | `get_all_images` | `global` | `permission` | `gql_legacy:images` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `search` | `get_image_by_id` | `global` | `permission` | `gql_legacy:image_node(id:)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `search` | `get_image_by_identifier` | `global` | `permission` | `gql_legacy:image(reference:)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `get` | `get_image_installed_agents` | `global` | `permission` | `gql_legacy:image.installed_agents` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | 등록된 컴퓨트 에이전트가 없어 빈 결과 |
| `image` | `search` | `get_images_by_canonicals` | `global` | `permission` | `gql_legacy (canonical batch load)` | ok | 403 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `search` | `search_aliases` | `global` | `permission` | `cli:admin image alias search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `image` | `search` | `search_images` | `global` | `permission` | `cli:admin image search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |

## label

5행 — 실패 1, 경고 3, 미실행 0, 성공 1.

### label — 성공 외 (4행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `label` | `lookup` | `lookup_bulk_entity_label_owner` | `lookup` | `permission` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — bulk field 연산이 배선되지 않았다 (1부 `W`) |
| `label` | `lookup` | `lookup_entity_label_owner` | `lookup` | `permission` | cli:entity-label purge (내부 lookup) | 404 database_access_not-found | 404 database_access_not-found | 일치 | `W-LEAK` | 게이트 전 실행 — F2의 구분 누출을 만드는 지점 (F2) |
| `label` | `search` | `search_entity_labels` | `bulk` | `permission` | cli:entity-label search | ok | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `E-BULK` | atomic 처리 — 한 항목 거부로 전체 실패, miss가 거부 목록에 섞인다 (F3) |
| `label` | `update` | `purge_entity_label` | `single_entity` | `permission` | cli:entity-label purge | ok | 403 role_create_forbidden / 404 database_access_not-found | 일치 | `W-LEAK` | 게이트 전 owner lookup — 실재 라벨은 403, 없는 라벨은 404로 갈린다 (F2) |

### label — 성공 (1행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `label` | `update` | `upsert_entity_label` | `single_entity` | `permission` | cli:entity-label upsert | ok | 403 role_create_forbidden | 일치 | `성공` | — |

## metric

14행 — 실패 0, 경고 4, 미실행 0, 성공 10.

### metric — 성공 외 (4행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `prometheus_query_preset` | `create` | `create_prometheus_query_preset` | `global` | `permission` | cli:admin prometheus-query-definition create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `prometheus_query_preset_category` | `create` | `create_prometheus_query_preset_category` | `global` | `permission` | cli:admin prometheus-query-definition-category create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `prometheus_query_preset` | `get` | `execute_prometheus_query_preset` | `single_entity` | `permission` | cli:prometheus-query-definition execute | ok | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 읽기와 실행 분리 — preset은 public으로 전문 공개, 실행은 monitor까지 거부 (F12) |
| `prometheus_query_preset` | `search` | `public_search_container_metrics` | `global` | `public` | gql:user_utilization_metric | ok | ok (본인) / GraphQL Permission denied (타인) | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 액션 밖 검사 — gql_legacy 리졸버가 `RuntimeError`로 소유권을 검사한다 (F13) |

### metric — 성공 (10행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `prometheus_query_preset_category` | `get` | `public_bulk_get_prometheus_query_preset_categories` | `bulk` | `public` | gql:prometheusQueryPresets | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 벌크 정상 — 위치대로, 중복 독립, null FK는 null (F16) |
| `prometheus_query_preset` | `get` | `preview_prometheus_query_preset` | `global` | `permission` | cli:admin prometheus-query-definition preview | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `prometheus_query_preset` | `get` | `get_prometheus_query_preset` | `single_entity` | `public` | cli:prometheus-query-definition get | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | public — PromQL 템플릿 전문이 인증만 하면 읽힌다 |
| `prometheus_query_preset_category` | `get` | `get_prometheus_query_preset_category` | `single_entity` | `public` | cli:prometheus-query-definition-category get | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `prometheus_query_preset` | `purge` | `purge_prometheus_query_preset` | `single_entity` | `permission` | cli:admin prometheus-query-definition delete | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `prometheus_query_preset_category` | `purge` | `purge_prometheus_query_preset_category` | `single_entity` | `permission` | cli:admin prometheus-query-definition-category delete | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `prometheus_query_preset` | `search` | `public_search_container_metric_metadata` | `global` | `public` | gql:container_utilization_metric_metadata | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `prometheus_query_preset` | `search` | `search_prometheus_query_presets` | `global` | `public` | cli:prometheus-query-definition search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `prometheus_query_preset_category` | `search` | `search_prometheus_query_preset_categories` | `global` | `public` | cli:prometheus-query-definition-category search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `prometheus_query_preset` | `update` | `update_prometheus_query_preset` | `single_entity` | `permission` | cli:admin prometheus-query-definition update | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |

## notification_center

13행 — 실패 0, 경고 10, 미실행 1, 성공 2.

### notification_center — 성공 외 (11행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `notification_channel` | `create` | `create_notification_channel` | `global` | `permission` | rest:POST /v2/notifications/channels | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `notification_rule` | `create` | `create_notification_rule` | `global` | `permission` | rest:POST /v2/notifications/rules | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `notification_rule` | `create` | `process_notification` | `global` | `permission` | bgtask:event_dispatcher/notification | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 이벤트 디스패처가 구동한다 |
| `notification_channel` | `get` | `get_notification_channel` | `single_entity` | `permission` | rest:GET /v2/notifications/channels/{id} | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_rule` | `get` | `get_notification_rule` | `single_entity` | `permission` | rest:GET /v2/notifications/rules/{id} | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_channel` | `purge` | `purge_notification_channel` | `single_entity` | `permission` | cli:notification channel delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_rule` | `purge` | `purge_notification_rule` | `single_entity` | `permission` | cli:notification rule delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_channel` | `update` | `update_notification_channel` | `single_entity` | `permission` | rest:PATCH /v2/notifications/channels/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_channel` | `update` | `validate_notification_channel` | `single_entity` | `permission` | rest:POST /v2/notifications/channels/validate | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 전달 실패를 500으로 보고 — 검증 결과가 아니라 서버 오류로 나온다 (F5) |
| `notification_rule` | `update` | `update_notification_rule` | `single_entity` | `permission` | rest:PATCH /v2/notifications/rules/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `notification_rule` | `update` | `validate_notification_rule` | `single_entity` | `permission` | rest:POST /v2/notifications/rules/validate | 400 backendai_parsing_invalid-parameters / 500 | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 전달 실패를 500으로 보고 — 완전한 이벤트 페이로드를 손으로 채워야 한다 (F5) |

### notification_center — 성공 (2행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `notification_channel` | `search` | `search_notification_channels` | `global` | `permission` | cli:notification channel search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `notification_rule` | `search` | `search_notification_rules` | `global` | `permission` | cli:notification rule search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |

## organization

99행 — 실패 13, 경고 51, 미실행 0, 성공 35.

### organization — 성공 외 (64행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `auth` | `create` | `authorize` | `global` | `anonymous` | rest:POST /auth/authorize | ok | 해당 없음 | 불일치 — 카탈로그 `auth` / 감사 `global` | `W-LEAK+W-AUDIT` | 구분 누출 — 401 본문은 같으나 `traceback`이 미존재 계정과 오답 비밀번호를 가른다 (F4, F10) |
| `auth` | `delete` | `global_revoke_login_session` | `global` | `permission` | rest:POST /v2/login-sessions/revoke | 404 auth_read_not-found | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `auth` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 거부는 미들웨어가 선점해 행이 없다 (F10, F12) |
| `auth` | `update` | `global_unblock_user` | `global` | `permission` | rest:POST /v2/login-sessions/unblock-user | ok | 403 backendai_generic_forbidden | 불일치 — 미존재 계정에 `success` 행 | `W-AUDIT` | 허위 성공 기록 — 없는 계정에도 200과 success 행 (F9, F10) |
| `auth` | `update` | `update_password_no_auth` | `global` | `anonymous` | rest:POST /auth/update-password-no-auth | 400 backendai_generic_bad-request | 해당 없음 | 불일치 — 카탈로그 `auth` / 감사 `global` | `E-EXEC+W-AUDIT` | 설정으로 비활성 — 어떤 입력에도 `Unsupported function.`을 반환한다. 결함이 아니라 배포 설정 (F10) |
| `domain` | `update` | `create_domain_dotfile` | `single_entity` | `permission` | rest-v1:POST /domain-config/dotfiles | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 도메인 관리자가 자기 도메인에 UPDATE를 갖지 않는다 (F15) |
| `domain` | `delete` | `delete_domain` | `single_entity` | `permission` | rest:POST /v2/domains/delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 선행해 RBAC 검사가 돌지 않고 거부 행도 없다 (F12) |
| `domain` | `update` | `delete_domain_dotfile` | `single_entity` | `permission` | rest-v1:DELETE /domain-config/dotfiles | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 도메인 관리자가 자기 도메인에 UPDATE를 갖지 않는다 (F15) |
| `domain` | `create` | `global_create_domain` | `global` | `permission` | rest-v1:POST /admin/domains | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `domain` / 감사 `global` | `W-AUDIT` | entity type 불일치 — v1 라우트만 이 액션에 닿는다 (F10) |
| `domain` | `create` | `global_create_domain_node` | `global` | `permission` | rest:POST /v2/domains | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `domain` / 감사 `global` | `W-AUDIT` | entity type 불일치 — `/v2/domains`는 `global_create_domain`이 아니라 이쪽에 닿는다 (F10) |
| `domain` | `search` | `global_search_domains` | `global` | `permission` | rest:POST /v2/domains/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점해 denied 행이 남지 않는다 (F12) |
| `domain` | `lookup` | `lookup_domain` | `lookup` | `public` | 없음 (내부 호출: `/v2/domains/{name}`·`/v2/users/domains/{name}/…` 선행) | 404 database_access_not-found | 404 database_access_not-found | 일치 | `W-LEAK` | 구분 누출 — 권한 검사 이전에 404가 나 도메인 이름을 열거할 수 있다 (F13) |
| `domain` | `restore` | `restore_domain` | `single_entity` | `permission` | rest:POST /v2/domains/restore | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 선행해 RBAC 검사가 돌지 않고 거부 행도 없다 (F12) |
| `domain` | `search` | `search_rg_domains` | `global` | `public` | rest:GET /v2/resource-groups/{name}/allowed-domains | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 게이트 선점 — `public` 선언이나 라우트가 superadmin_required다 (F12) |
| `domain` | `update` | `update_domain_dotfile` | `single_entity` | `permission` | rest-v1:PATCH /domain-config/dotfiles | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 도메인 관리자가 자기 도메인에 UPDATE를 갖지 않는다 (F15) |
| `domain` | `update` | `update_domain_node` | `single_entity` | `permission` | rest:PATCH /v2/domains/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — `/v2/domains/{name}`은 `update_domain`이 아니라 이쪽에 닿는다 (F12) |
| `error_log` | `update` | `delete_error_log` | `single_entity` | `permission` | rest-v1:POST /logs/error/{log_id}/clear | 404 database_access_not-found | 403 role_create_forbidden (타인 소유) / 404 (미존재) | 일치 | `W-LEAK` | 구분 누출 — 타인 소유 로그는 403, 미존재는 404로 갈려 id를 열거할 수 있다 (F13) |
| `error_log` | `search` | `global_search_error_logs` | `global` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 라우트 없음 — `GET /logs/error`는 언제나 scope 변종을 고른다 |
| `keypair` | `get` | `get_default_keypairs` | `bulk` | `permission` | 없음 (내부 호출: adapters/user·project가 `main_access_key`를 채울 때) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 권한 과다 — bulk 게이트가 타인의 `main_access_key` 노출을 막지 못한다 (F1) |
| `keypair` | `get` | `get_keypair` | `single_entity` | `permission` | rest:GET /v2/keypairs/{access_key} | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `E-GATE+W-AUDIT` | 게이트 선점 — 소유자조차 자기 키페어를 못 읽는다 (F12) |
| `keypair` | `update` | `purge_keypair` | `single_entity` | `permission` | rest:DELETE /v2/keypairs/{access_key} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `login_history` | `search` | `global_search_login_history` | `global` | `permission` | rest:POST /v2/login-history/search | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | 행 없음 (결함) | `E-EXEC+W-AUDIT` | 응답 직렬화 실패 — `client_ip`가 `inet`인데 DTO는 `str`이라 통과한 주체도 500을 받는다 (F7, F12) |
| `login_history` | `search` | `search_login_history` | `scope` | `permission` | rest:POST /v2/login-history/my/search | 500 backendai_generic_internal-error | 500 backendai_generic_internal-error | 행 없음 (성공 read — 정책상 정상) | `E-EXEC` | 응답 직렬화 실패 — 액션은 성공하고 `client_ip` 직렬화에서 죽어 누구도 결과를 못 받는다 (F7) |
| `login_session` | `search` | `global_search_login_sessions` | `global` | `permission` | rest:POST /v2/login-sessions/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `login_session` | `update` | `revoke_login_session` | `single_entity` | `permission` | rest:POST /v2/login-sessions/my/revoke | 404 database_access_not-found | 403 role_create_forbidden (타인 소유) / 404 (미존재) | 일치 | `W-LEAK` | 구분 누출 — 타인 소유 세션은 403, 미존재는 404로 갈려 세션 id를 열거할 수 있다 (F13) |
| `project` | `update` | `assign_users_to_project` | `single_entity` | `permission` | rest:POST /v2/projects/{id}/users/assign | ok | 403 role_create_forbidden | 일치 | `E-BULK` | 벌크 응답 결함 — 미존재 user id는 응답에도 감사에도 안 나오고, 중복 하나가 전체를 409로 되돌린다 (F2, F14) |
| `project` | `create` | `create_project` | `scope` | `permission` | rest:POST /v2/projects | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — `scope` 선언이나 superadmin_required라 도메인 관리자가 만들 수 없다 (F12) |
| `project` | `delete` | `delete_project` | `single_entity` | `permission` | rest:POST /v2/projects/delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 본문 키가 v1식 `group_id`다 (F12, F15) |
| `project` | `get` | `get_project` | `single_entity` | `permission` | rest:GET /v2/projects/{id} | 404 database_access_not-found | 403 role_create_forbidden | 일치 | `W-GATE` | 권한 부족 — 소속 프로젝트에도 READ가 없다 (F5) |
| `project` | `search` | `global_search_project_usage_per_month` | `global` | `permission` | rest-v1:GET /resource/usage/month | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `project` | `search` | `global_search_project_usage_per_period` | `global` | `permission` | rest-v1:GET /resource/usage/period | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `project` | `search` | `global_search_projects` | `global` | `permission` | rest:POST /v2/projects/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `project` | `purge` | `purge_project` | `single_entity` | `permission` | rest:POST /v2/projects/purge | 404 group_read_not-found | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 같은 미존재 입력에 delete·restore와 다른 error_code를 낸다 (F12, F15) |
| `project` | `restore` | `restore_project` | `single_entity` | `permission` | rest:POST /v2/projects/restore | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 본문 키가 v1식 `group_id`다 (F12, F15) |
| `project` | `search` | `search_projects_by_user` | `scope` | `permission` | gql:UserV2.projects | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 자기 user 스코프에서 자기 프로젝트 목록을 못 읽는다 (F5) |
| `project` | `update` | `update_project` | `single_entity` | `permission` | rest:PATCH /v2/projects/{id} | ok | 403 backendai_generic_forbidden | 불일치 — 500인 실행에 `success` 행 | `W-GATE+W-AUDIT` | 허위 성공 기록 — 미존재 id에 500이면서 감사는 success (F9, F12) |
| `user` | `update` | `admin_create_keypair` | `single_entity` | `permission` | rest:POST /v2/keypairs | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `update` | `admin_delete_ssh_keypair` | `single_entity` | `permission` | rest:DELETE /v2/keypairs/{access_key}/ssh | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `get` | `admin_get_ssh_keypair` | `single_entity` | `permission` | rest:GET /v2/keypairs/{access_key}/ssh | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `update` | `admin_register_ssh_keypair` | `single_entity` | `permission` | rest:POST /v2/keypairs/ssh | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `create` | `create_user` | `scope` | `permission` | rest:POST /v2/users | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 만들어진 계정에 `default`·`model-store` 멤버 롤이 자동 부여된다 (F1, F12) |
| `user` | `delete` | `delete_user` | `single_entity` | `permission` | rest:POST /v2/users/delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `get` | `get_user` | `single_entity` | `permission` | rest:GET /v2/users/{id} | ok | ok (같은 도메인) / 403 role_create_forbidden (타 도메인) | 일치 | `W-GATE` | 권한 과다 — 같은 도메인 사용자의 전체 레코드와 `main_access_key`가 평사용자에게 열린다 (F1) |
| `user` | `create` | `global_create_users` | `global` | `permission` | gql:adminBulkCreateUsersV2 | ok | 403 backendai_generic_internal-error | 불일치 — 카탈로그 `user` / 감사 `global`, 일부 실패인데 `success` | `E-BULK+W-AUDIT` | 벌크 응답 결함 — 미존재 도메인 한 건이 배치 전체를 중단시킨다 (F17, F19) |
| `user` | `get` | `global_get_user_month_stats` | `global` | `permission` | rest-v1:GET /resource/stats/admin/month | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `user` | `purge` | `global_purge_users` | `global` | `permission` | gql:adminBulkPurgeUsersV2 | ok | 403 backendai_generic_internal-error | 불일치 — 카탈로그 `user` / 감사 `global`, 일부 실패인데 `success` | `E-BULK+W-AUDIT` | 벌크 응답 결함 — 성공은 개수만 오고 어떤 사용자가 지워졌는지 알 수 없다 (F18, F19) |
| `user` | `search` | `global_search_keypairs` | `global` | `permission` | rest:POST /v2/keypairs/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `user` | `search` | `global_search_users` | `global` | `permission` | rest:POST /v2/users/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `user` | `update` | `global_update_users` | `global` | `permission` | gql:adminBulkUpdateUsersV2 | ok | 403 backendai_generic_internal-error | 불일치 — 카탈로그 `user` / 감사 `global`, 일부 실패인데 `success` | `W-AUDIT` | entity type 불일치 — 벌크 응답 자체는 입력 순서대로 항목별로 답한다 (F10, F19) |
| `user` | `update` | `logout` | `single_entity` | `permission` | rest:POST /auth/logout | ok | ok | 불일치 — 없는 세션 토큰에 `success` 행 | `W-AUDIT` | 허위 성공 기록 — 존재하지 않는 세션에도 200과 success 행 (F9) |
| `user` | `lookup` | `lookup_bulk_error_log_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | `lookup` | `lookup_bulk_keypair_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | `lookup` | `lookup_bulk_login_history_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | `lookup` | `lookup_bulk_login_session_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | `lookup` | `lookup_error_log_owner` | `lookup` | `permission` | 없음 (내부 호출: `POST /logs/error/{id}/clear` 선행) | 404 database_access_not-found | 403 role_create_forbidden (타인 소유) / 404 (미존재) | 일치 | `W-LEAK` | 구분 누출 — 한 호출자가 타인 소유 403과 미존재 404를 가른다. 403 본문이 소유자 UUID까지 준다 (F13) |
| `user` | `lookup` | `lookup_login_history_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 single field 연산을 배선하지 않는다 |
| `user` | `lookup` | `lookup_login_session_owner` | `lookup` | `permission` | 없음 (내부 호출: `POST /v2/login-sessions/my/revoke` 선행) | 404 database_access_not-found | 403 role_create_forbidden (타인 소유) / 404 (미존재) | 일치 | `W-LEAK` | 구분 누출 — 한 호출자가 타인 소유 403과 미존재 404를 가른다. 403 본문이 소유자 UUID까지 준다 (F13) |
| `user` | `lookup` | `lookup_user_by_access_key` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — 프로세서에만 등록되고 호출자가 없다 |
| `user` | `restore` | `restore_user` | `single_entity` | `permission` | rest:POST /v2/users/restore | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user` | `search` | `search_users_by_domain` | `scope` | `permission` | rest:POST /v2/users/domains/{domain_name}/search | ok | 403 role_create_forbidden | 일치 | `E-GATE+W-LEAK` | 권한 부족 — 자기 도메인 목록이 막히는데 `get_user`는 같은 행을 한 건씩 내준다 (F1, F13) |
| `user` | `search` | `search_users_by_project` | `scope` | `permission` | rest:POST /v2/users/projects/{project_id}/search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 권한 과다 — 프로젝트 구성원 전원의 `main_access_key`가 평사용자에게 열린다 (F1) |
| `user` | `search` | `search_users_by_role` | `global` | `permission` | rest:POST /v2/users/roles/{role_id}/search | ok | 403 user_auth_forbidden | 불일치 — 카탈로그 `user` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 게이트는 프로세서가 강제하고 거부 행도 남는다 (F10) |
| `user` | `create` | `signup` | `global` | `anonymous` | rest:POST /auth/signup | ok | 해당 없음 | 불일치 — 카탈로그 `user` / 감사 `global` | `W-LEAK+W-GUARD+W-AUDIT` | 게이트 근거 미흡 — `anonymous`를 정당화하는 `PRE_SIGNUP` 훅이 등록돼 있지 않고 `success_if_no_hook=True`라 무조건 통과한다 (F4, F10, F20) |
| `user` | `update` | `update_password` | `single_entity` | `permission` | rest:POST /auth/update-password | ok | 401 user_auth_unauthorized | 불일치 — 400으로 끝난 실행에 `success` 행 | `W-AUDIT` | 허위 성공 기록 — 새 비밀번호 불일치로 아무것도 안 바뀌었는데 success (F9) |
| `user` | `update` | `update_user` | `single_entity` | `permission` | rest:PATCH /v2/users/{id} | ok | 403 backendai_generic_forbidden | 일치 | `E-GATE+W-AUDIT` | 게이트 선점 — 자기 레코드도 이 라우트로는 고칠 수 없다 (F12) |

### organization — 성공 (35행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `domain` | `purge` | `purge_domain` | `single_entity` | `permission` | rest-v1:POST /admin/domains/purge | 409 domain_purge_conflict | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `domain` | `update` | `update_domain` | `single_entity` | `permission` | rest-v1:PATCH /admin/domains/{name} | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `user` | `purge` | `purge_user` | `single_entity` | `permission` | rest-v1:POST /admin/users/purge | 404 user_read_not-found | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `auth` | `get` | `public_get_role` | `global` | `public` | rest:GET /auth/role | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `auth` | `get` | `public_resolve_access_key_scope` | `global` | `public` | 없음 (내부 호출: rest/session·service·userconfig 핸들러) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `auth` | `get` | `public_resolve_user_scope` | `global` | `public` | 없음 (내부 호출: rest/vfolder 핸들러) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `domain` | `get` | `get_domain` | `single_entity` | `public` | rest:GET /v2/domains/{name} | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 선언대로 `public` — 인증된 누구나 모든 도메인을 읽으므로 거부 상태 자체가 없다 |
| `error_log` | `update` | `create_error_log` | `single_entity` | `permission` | rest-v1:POST /logs/error | ok | ok | 일치 | `성공` | — |
| `error_log` | `search` | `search_error_logs` | `scope` | `permission` | rest-v1:GET /logs/error | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `keypair` | `update` | `update_keypair` | `single_entity` | `permission` | rest:PATCH /v2/keypairs/my | ok | ok | 일치 | `성공` | — |
| `login_session` | `search` | `search_login_sessions` | `scope` | `permission` | rest:POST /v2/login-sessions/my/search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project` | `update` | `create_project_dotfile` | `single_entity` | `permission` | rest-v1:POST /group-config/dotfiles | ok | 403 backendai_generic_forbidden | 일치 | `성공` | — |
| `project` | `update` | `delete_project_dotfile` | `single_entity` | `permission` | rest-v1:DELETE /group-config/dotfiles | ok | 403 backendai_generic_forbidden | 일치 | `성공` | — |
| `project` | `lookup` | `lookup_project` | `lookup` | `public` | 없음 (내부 호출: rest/resource_group·cluster_template·session_template 핸들러) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project` | `search` | `search_projects_by_domain` | `scope` | `permission` | gql:domainProjectsV2 | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `project` | `update` | `unassign_users_from_project` | `single_entity` | `permission` | rest:POST /v2/projects/{id}/users/unassign | ok | 403 role_create_forbidden | 일치 | `성공` | 입력 순서는 지키지 않으나 모든 id가 식별자를 달고 한 번씩 답해져 대조가 된다 (F14) |
| `project` | `update` | `update_project_dotfile` | `single_entity` | `permission` | rest-v1:PATCH /group-config/dotfiles | ok | 403 backendai_generic_forbidden | 일치 | `성공` | — |
| `user` | `update` | `create_keypair_dotfile` | `single_entity` | `permission` | rest-v1:POST /user-config/dotfiles | ok | ok | 일치 | `성공` | — |
| `user` | `update` | `delete_keypair_dotfile` | `single_entity` | `permission` | rest-v1:DELETE /user-config/dotfiles | ok | ok | 일치 | `성공` | — |
| `user` | `update` | `generate_ssh_keypair` | `single_entity` | `permission` | rest:PATCH /auth/ssh-keypair | ok | ok | 일치 | `성공` | — |
| `user` | `get` | `get_bootstrap_script` | `single_entity` | `permission` | rest-v1:GET /user-config/bootstrap-script | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `get` | `get_ssh_keypair` | `single_entity` | `permission` | rest:GET /auth/ssh-keypair | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `get` | `get_user_month_stats` | `single_entity` | `permission` | rest-v1:GET /resource/stats/user/month | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `update` | `issue_keypair` | `single_entity` | `permission` | rest:POST /v2/keypairs/my/issue | ok | ok | 일치 | `성공` | — |
| `user` | `lookup` | `lookup_keypair` | `lookup` | `permission` | 없음 (내부 호출: `/v2/keypairs/{ak}` GET·DELETE 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `user` | `lookup` | `lookup_keypair_owner` | `lookup` | `permission` | 없음 (내부 호출: keypair single_entity 연산의 동반 lookup) | ok | 해당 없음 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `lookup` | `lookup_keypair_owner_by_access_key` | `lookup` | `permission` | 없음 (내부 호출: `/v2/keypairs/{ak}/ssh` 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `user` | `lookup` | `lookup_user` | `lookup` | `public` | 없음 (내부 호출: gql_legacy/keypair 리졸버) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `search` | `search_keypairs` | `scope` | `permission` | rest:POST /v2/keypairs/my/search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `delete` | `signout` | `single_entity` | `permission` | rest:POST /auth/signout | ok | ok | 일치 | `성공` | — |
| `user` | `update` | `switch_default_access_key` | `single_entity` | `permission` | rest:POST /v2/keypairs/my/switch-main | ok | 403 keypair_read_forbidden | 일치 | `성공` | — |
| `user` | `update` | `update_bootstrap_script` | `single_entity` | `permission` | rest-v1:POST /user-config/bootstrap-script | ok | ok | 일치 | `성공` | — |
| `user` | `update` | `update_full_name` | `single_entity` | `permission` | rest:POST /auth/update-full-name | ok | ok | 일치 | `성공` | 필수 `email`을 읽지 않고 언제나 호출자를 고친다. 타인 주소로도 교차 수정은 일어나지 않는다 (F15) |
| `user` | `update` | `update_keypair_dotfile` | `single_entity` | `permission` | rest-v1:PATCH /user-config/dotfiles | ok | ok | 일치 | `성공` | — |
| `user` | `update` | `upload_ssh_keypair` | `single_entity` | `permission` | rest:POST /auth/ssh-keypair | 400 keypair_create_invalid-data-format | 400 keypair_create_invalid-data-format | 일치 | `성공` | — |

### organization — 레거시 API (16행)

`api/gql_legacy/`에서 v2 프로세서에 도달하는 경로다. 위 표의 행과 같은 액션을 다른 경로로 실행한 것이라 총계에 더하지 않는다.

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `domain` | `create` | `global_create_domain_node` | `global` | `permission` | gql_legacy:CreateDomainNode | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-UNREACH+W-AUDIT` | 인자 발산 — `scaling_groups`로 리소스 그룹까지 붙이는데 REST `CreateDomainInput`에 그 필드가 없다 (LA1) |
| `domain` | `update` | `update_domain_node` | `single_entity` | `permission` | gql_legacy:ModifyDomainNode | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-UNREACH+W-AUDIT` | 인자 발산 — `sgroups_to_add`·`sgroups_to_remove`가 REST `UpdateDomainInput`에 없다 (LA1) |
| `domain` | `create` | `global_create_domain` | `global` | `permission` | gql_legacy:CreateDomain | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-AUDIT` | v1 REST와 동일. 기본 프로젝트를 함께 만든다 — `POST /v2/domains`는 만들지 않는다 (LA2) |
| `domain` | `update` | `update_domain` | `single_entity` | `permission` | gql_legacy:ModifyDomain | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-AUDIT` | 거부 표현 발산 — v2는 403, 레거시는 200 `ok:false` |
| `domain` | `delete` | `delete_domain` | `single_entity` | `permission` | gql_legacy:DeleteDomain | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-AUDIT` | 거부 표현 발산 — 인자·액션·성공 행은 v2와 같다 |
| `domain` | `purge` | `purge_domain` | `single_entity` | `permission` | gql_legacy:PurgeDomain | 409 `domain_purge_conflict` | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-AUDIT` | 거부 표현 발산 — 실패 행은 v2와 같다 |
| `project` | `update` | `update_project` | `single_entity` | `permission` | gql_legacy:ModifyGroup | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-UNREACH+W-AUDIT` | 인자 발산 — `user_update_mode`·`user_uuids`로 멤버십을 함께 고치는데 REST `UpdateProjectInput`에 없다 (LA3) |
| `project` | `delete` | `delete_project` | `single_entity` | `permission` | gql_legacy:DeleteGroup | ok | 200 `ok:false` | 불일치 — 거부에 행 없음 | `W-AUDIT` | 거부 표현 발산 — `gid` UUID 주소지정까지 v2와 같다 |
| `user` | `delete` | `delete_user` | `single_entity` | `permission` | gql_legacy:DeleteUser | ok | 200 `ok:false` | 불일치 — 미존재 이메일에 행 없음 | `W-AUDIT` | 기록 발산 — 리졸버가 액션 이전에 이메일을 풀다 실패해 행이 없다. v2는 `delete_user\|error`를 남긴다 |
| `user` | `purge` | `purge_user` | `single_entity` | `permission` | gql_legacy:PurgeUser | ok | 200 `ok:false` | 불일치 — 미존재 이메일에 행 없음 | `W-AUDIT` | 기록 발산 — v2는 `purge_user\|error`를 남기고 레거시는 아무것도 남기지 않는다 |
| `domain` | `lookup` | `lookup_domain` | `lookup` | `public` | gql_legacy:DomainConnection (`domain_nodes`) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project` | `create` | `create_project` | `scope` | `permission` | gql_legacy:CreateGroup | ok | 200 `ok:false` | 일치 | `성공` | `resource_policy` 기본값이 `"default"`라 생략해도 성공한다 — 같은 생략이 REST v2에서는 400이다 |
| `project` | `purge` | `purge_project` | `single_entity` | `permission` | gql_legacy:PurgeGroup | ok | 200 `ok:false` | 일치 | `성공` | — |
| `user` | `create` | `create_user` | `scope` | `permission` | gql_legacy:CreateUser | ok | 200 `ok:false` | 일치 | `성공` | `group_ids`·`container_*`까지 v2 `CreateUserInput`과 필드가 같다 |
| `user` | `update` | `update_user` | `single_entity` | `permission` | gql_legacy:ModifyUser | ok | 200 `ok:false` | 일치 | `성공` | `main_access_key`를 주면 `switch_default_access_key`가 이어 돈다 — v2 PATCH도 같다 |
| `user` | `update` | `admin_create_keypair` | `single_entity` | `permission` | gql_legacy:CreateKeyPair | ok | 200 `ok:false` | 일치 | `성공` | 이메일로 주소지정하고 `lookup_user`로 UUID를 풀어 v2와 같은 인자로 액션을 만든다. 미존재 이메일은 `lookup_user\|error` |

## rbac

19행 — 실패 4, 경고 12, 미실행 0, 성공 3.

### rbac — 성공 외 (16행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `entity_invitation` | `update` | `accept_entity_invitation` | `scope` | `permission` | rest:POST /v2/entity-invitations/{id}/accept · cli:entity-invitation accept | 404 entity-invitation_read_not-found | 403 role_create_forbidden | 일치 | `E-GATE+E-EXEC` | 누구도 완료 불가 — 초대 대상은 RBAC가 막고, RBAC를 우회하는 superadmin은 대상이 아니다 (F16) |
| `entity_invitation` | `get` | `get_entity_invitation` | `single_entity` | `permission` | rest:GET /v2/entity-invitations/{id} · cli:entity-invitation get | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 초대장에 적힌 당사자가 자기 초대장을 못 읽는다 (F16) |
| `entity_invitation` | `update` | `reject_entity_invitation` | `scope` | `permission` | rest:POST /v2/entity-invitations/{id}/reject · cli:entity-invitation reject | 404 entity-invitation_read_not-found | 403 role_create_forbidden | 일치 | `E-EXEC+W-GATE` | 누구도 완료 불가 — accept와 같은 원인 (F16) |
| `entity_invitation` | `search` | `search_entity_invitations` | `scope` | `permission` | rest:POST /v2/entity-invitations/scoped/search · cli:entity-invitation scoped-search | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 자기 user 스코프에서 자기 앞으로 온 초대를 못 찾는다 (F16) |
| `role_permission_preset` | `update` | `bulk_add_role_permission_presets` | `single_entity` | `permission` | rest:POST /v2/role-presets/{id}/permissions/add | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 상태·코드 불일치 — 미존재 preset에 409인데 error_code는 `database_generic_not-found`다 (F12, F15) |
| `role_permission_preset` | `update` | `bulk_remove_role_permission_presets` | `bulk` | `permission` | rest:POST /v2/role-presets/permissions/remove | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 벌크 응답은 항목별로 답하고 miss를 구분한다 (F12) |
| `role_permission_preset` | `search` | `search_role_permission_presets` | `scope` | `permission` | rest:POST /v2/role-presets/{id}/permissions/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 상태 코드 오류 — 미존재 preset도 200에 빈 목록이라 없는 것과 빈 것이 구분되지 않는다 (F12, F15) |
| `role_preset` | `delete` | `bulk_delete_role_presets` | `bulk` | `permission` | rest:POST /v2/role-presets/bulk-delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 벌크 응답은 `items`·`failed`로 모든 id를 한 번씩 답한다 (F12) |
| `role_preset` | `purge` | `bulk_purge_role_presets` | `bulk` | `permission` | rest:POST /v2/role-presets/bulk-purge | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 벌크 응답은 `items`·`failed`로 모든 id를 한 번씩 답한다 (F12) |
| `role_preset` | `restore` | `bulk_restore_role_presets` | `bulk` | `permission` | rest:POST /v2/role-presets/bulk-restore | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — 벌크 응답은 `items`·`failed`로 모든 id를 한 번씩 답한다 (F12) |
| `role_preset` | `create` | `create_role_preset` | `global` | `permission` | rest:POST /v2/role-presets | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `role_preset` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 거부는 미들웨어가 선점해 행이 없다 (F10, F12) |
| `role_preset` | `get` | `get_role_preset` | `single_entity` | `permission` | rest:GET /v2/role-presets/{id} | 404 database_access_not-found | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `role_preset` | `lookup` | `lookup_role_permission_preset_owner` | `lookup` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 도달 불가 owner lookup — 이 도메인은 single field 연산을 배선하지 않는다 |
| `role_preset` | `purge` | `purge_role_preset` | `single_entity` | `permission` | 없음 | 해당 없음 | 해당 없음 | 해당 없음 | `W-UNREACH` | 배선됐지만 호출 안 됨 — API는 `bulk_purge`만 호출한다 |
| `role_preset` | `search` | `search_role_presets` | `global` | `permission` | rest:POST /v2/role-presets/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `role_preset` | `update` | `update_role_preset` | `single_entity` | `permission` | rest:PATCH /v2/role-presets/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |

### rbac — 성공 (3행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `entity_invitation` | `delete` | `cancel_entity_invitation` | `single_entity` | `permission` | rest:DELETE /v2/entity-invitations/{id} · cli:entity-invitation cancel | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `entity_invitation` | `create` | `create_entity_invitation` | `scope` | `permission` | rest:POST /v2/entity-invitations · cli:entity-invitation create | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `role_preset` | `lookup` | `lookup_bulk_role_permission_preset_owner` | `lookup` | `permission` | 없음 (내부 호출: `POST /v2/role-presets/permissions/remove` 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |

## resource_group

77행 — 실패 4, 경고 25, 미실행 7, 성공 41.

### resource_group — 성공 외 (36행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `resource_group` | `create` | `global_create_resource_group` | `global` | `permission` | cli:admin resource-group create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `resource_preset` | `create` | `global_create_resource_preset` | `global` | `permission` | rest:POST /v2/resource-presets | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `resource_group` | `delete` | `disassociate_resource_group_from_domains` | `single_entity` | `permission` | cli:admin resource-group allow-domains --remove | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — `default` 도메인 바인딩 훼손 우려 |
| `resource_group` | `delete` | `disassociate_resource_group_from_projects` | `single_entity` | `permission` | cli:admin resource-group allow-projects --remove | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — `default` 프로젝트 바인딩 훼손 우려 |
| `resource_preset` | `delete` | `delete_resource_preset` | `single_entity` | `permission` | rest:DELETE /v2/resource-presets/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `agent` | `get` | `global_load_agent_container_counts` | `global` | `public` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 선택하는 필드 없음 — `api/adapters/agent/adapter.py`만 부르고 이를 고르는 GraphQL 필드가 없다 |
| `resource_group` | `get` | `global_get_wsproxy_version` | `global` | `public` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 클라이언트 경로 없음 — resource_group registry에 해당 경로가 없다 |
| `resource_group` | `get` | `global_resolve_resource_group_ids` | `global` | `permission` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 내부 헬퍼 — 라우트가 없다 |
| `domain_fair_share` | `get` | `get_domain_fair_share` | `scope` | `permission` | cli:fair-share domain get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `project_fair_share` | `get` | `get_project_fair_share` | `scope` | `permission` | cli:fair-share project get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `user_fair_share` | `get` | `get_user_fair_share` | `scope` | `permission` | cli:fair-share user get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `agent` | `get` | `get_agent_resource_by_slot` | `single_entity` | `permission` | cli:resource-slot agent-resource search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `session` | `get` | `get_kernel_allocation_by_slot` | `single_entity` | `permission` | cli:resource-slot allocation search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `resource_preset` | `lookup` | `lookup_resource_preset` | `lookup` | `public` | rest:GET /v2/resource-presets/{id} (내부 lookup) | 404 resource-preset_read_not-found | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 선언은 public — 라우트가 superadmin으로 좁힌다 |
| `session` | `lookup` | `lookup_kernel_owner` | `lookup` | `permission` | 내부 lookup | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 세션 생성이 이 슬라이스 범위 밖 |
| `resource_preset` | `search` | `global_list_resource_presets` | `global` | `public` | rest:GET /resource/presets | 500 backendai_generic_internal-error | 500 backendai_generic_internal-error | 행 없음 (성공 read — 정책상 정상) | `E-EXEC` | ContextVar 미설정 — `normalize_slots()`가 매니저에 없는 `current_resource_slots`를 폴백 없이 읽어 항상 500 (F7) |
| `domain_fair_share` | `search` | `search_domain_fair_shares` | `scope` | `permission` | rest:POST /v2/fair-share/domains/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `domain_usage_bucket` | `search` | `search_domain_usage_buckets` | `scope` | `permission` | rest:POST /v2/resource-usage/domains/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `project_fair_share` | `search` | `search_project_fair_shares` | `scope` | `permission` | rest:POST /v2/fair-share/projects/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `project_usage_bucket` | `search` | `search_project_usage_buckets` | `scope` | `permission` | rest:POST /v2/resource-usage/projects/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `resource_group` | `search` | `scoped_search_resource_groups` | `scope` | `permission` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 클라이언트 경로 없음 — registry에 `/search`(superadmin)만 있다 |
| `user_fair_share` | `search` | `search_user_fair_shares` | `scope` | `permission` | rest:POST /v2/fair-share/users/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `user_usage_bucket` | `search` | `search_user_usage_buckets` | `scope` | `permission` | rest:POST /v2/resource-usage/users/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `agent` | `update` | `global_restart_agent` | `global` | `permission` | rest:POST /resource/watcher/agent/restart | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 공유 스택 불안정 우려 |
| `agent` | `update` | `global_start_agent` | `global` | `permission` | rest:POST /resource/watcher/agent/start | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 공유 스택 불안정 우려 |
| `agent` | `update` | `global_stop_agent` | `global` | `permission` | rest:POST /resource/watcher/agent/stop | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 공유 스택 불안정 우려 |
| `agent` | `update` | `global_sync_agent_registry` | `global` | `permission` | rest:session handler (내부) | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — `api/rest/session/handler.py`가 세션 경로 안에서만 부른다 |
| `agent` | `update` | `global_update_agent_resource_group` | `global` | `permission` | cli:admin agent update-resource-group | 404 agent_read_not-found | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `domain_fair_share` | `update` | `bulk_upsert_domain_fair_share_weights` | `scope` | `permission` | rest:POST /v2/fair-share/domains/bulk-upsert | ok | 403 backendai_generic_forbidden | 일치 | `E-BULK+W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 항목별 응답 없음 — `upserted_count`만 반환, 없는 도메인도 성공으로 기록 (F3) |
| `domain_fair_share` | `update` | `upsert_domain_fair_share_weight` | `scope` | `permission` | rest:POST /v2/fair-share/domains/upsert | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `project_fair_share` | `update` | `bulk_upsert_project_fair_share_weights` | `scope` | `permission` | rest:POST /v2/fair-share/projects/bulk-upsert | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `E-BULK+W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 항목별 응답 없음 — `upserted_count`만 반환 (F3) |
| `project_fair_share` | `update` | `upsert_project_fair_share_weight` | `scope` | `permission` | rest:POST /v2/fair-share/projects/upsert | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `user_fair_share` | `update` | `bulk_upsert_user_fair_share_weights` | `scope` | `permission` | rest:POST /v2/fair-share/users/bulk-upsert | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `E-BULK+W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 항목별 응답 없음 — `upserted_count`만 반환 (F3) |
| `user_fair_share` | `update` | `upsert_user_fair_share_weight` | `scope` | `permission` | rest:POST /v2/fair-share/users/upsert | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `resource_group` | `update` | `update_resource_group_fair_share_spec` | `single_entity` | `permission` | rest:PATCH /v2/resource-groups/{name}/fair-share-spec | 400 api_parsing_invalid-parameters | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `resource_preset` | `update` | `update_resource_preset` | `single_entity` | `permission` | rest:PATCH /v2/resource-presets/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 경로·본문 id 중복 — 본문 `id`가 필수인데 무시된다 (F8) |

### resource_group — 성공 (41행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `resource_group` | `create` | `associate_resource_group_with_domains` | `single_entity` | `permission` | cli:admin resource-group allow-domains --add | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `create` | `associate_resource_group_with_projects` | `single_entity` | `permission` | cli:admin resource-group allow-projects --add | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `create` | `associate_resource_group_with_keypairs` | `single_entity` | `permission` | gql_legacy:associate_scaling_group_with_keypair | ok | 200 `ok:false` "no permission" | 일치 | `성공` | REST v2 registry에는 keypair 경로가 없지만 레거시 뮤테이션이 이 액션에 도달한다 — 3부의 `W-UNREACH` 판정을 철회한다 (L4). 비-admin 거부가 403이 아니라 200 `ok:false`로 오는 것은 레거시 계층 공통 (B의 F11) |
| `resource_group` | `delete` | `disassociate_resource_group_from_keypairs` | `single_entity` | `permission` | gql_legacy:disassociate_scaling_group_with_keypair | ok | 200 `ok:false` "no permission" | 일치 | `성공` | REST v2 registry에는 keypair 경로가 없지만 레거시 뮤테이션이 이 액션에 도달한다 — 3부의 `W-UNREACH` 판정을 철회한다 (L4). 비-admin 거부가 403이 아니라 200 `ok:false`로 오는 것은 레거시 계층 공통 (B의 F11) |
| `agent` | `get` | `global_get_agent_total_resources` | `global` | `public` | cli:admin agent total-resources | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `agent` | `get` | `global_get_agent_watcher_status` | `global` | `permission` | rest:GET /resource/watcher | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 에이전트·워처 부재를 타입 없는 500으로 보고 (F15) |
| `resource_group` | `get` | `global_get_resource_group_usage` | `global` | `permission` | cli:resource-allocation resource-group-usage | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `session` | `get` | `get_domain_resource_overview` | `scope` | `permission` | cli:admin resource-allocation domain-usage | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `session` | `get` | `get_effective_allocation` | `scope` | `permission` | cli:my resource-allocation effective / admin ... effective | ok (my) / 404 (admin) | ok | 일치 | `성공` | admin 변형이 domain_name=""로 항상 404 — 리포지토리가 user_id로 도메인을 풀지 않는다 (F14) |
| `session` | `get` | `get_project_resource_overview` | `scope` | `permission` | cli:resource-allocation project-usage | ok | 403 not-enough-permission | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `resource_group` | `get` | `get_allowed_domains_for_resource_group` | `single_entity` | `permission` | cli:admin resource-group allowed-domains | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `get` | `get_allowed_projects_for_resource_group` | `single_entity` | `permission` | cli:admin resource-group allowed-projects | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `get` | `get_resource_group_resource_info` | `single_entity` | `permission` | cli:admin resource-group resource-info | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `domain` | `get` | `get_domain_usage` | `single_entity` | `permission` | cli:admin resource-allocation domain-usage | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project` | `get` | `get_project_usage` | `single_entity` | `permission` | cli:resource-allocation project-usage | ok | 403 not-enough-permission | 행 없음 (성공 read — 정책상 정상) | `성공` | 프로젝트 구성원이 자기 프로젝트 사용량에서 거부된다 |
| `user` | `get` | `get_keypair_usage` | `single_entity` | `permission` | cli:my resource-allocation keypair-usage | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user` | `get` | `resolve_keypair_context` | `single_entity` | `permission` | cli:my resource-allocation keypair-usage (내부) | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `agent` | `lookup` | `lookup_agent` | `lookup` | `public` | cli:admin agent update-resource-group (내부 lookup) | 404 agent_read_not-found | 해당 없음 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `resource_group` | `lookup` | `lookup_resource_group` | `lookup` | `public` | cli:admin resource-group resource-info (내부 lookup) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `resource_group` | `purge` | `purge_resource_group` | `single_entity` | `permission` | cli:admin resource-group delete | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `agent` | `search` | `global_search_agents` | `global` | `public` | cli:admin agent search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `agent` | `search` | `global_search_agent_resources` | `global` | `permission` | cli:resource-slot agent-resource search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `domain_fair_share` | `search` | `global_search_domain_fair_shares` | `global` | `permission` | cli:fair-share domain search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `domain_usage_bucket` | `search` | `global_search_domain_usage_buckets` | `global` | `permission` | cli:resource-usage domain search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project_fair_share` | `search` | `global_search_project_fair_shares` | `global` | `permission` | cli:fair-share project search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `project_usage_bucket` | `search` | `global_search_project_usage_buckets` | `global` | `permission` | cli:resource-usage project search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `resource_group` | `search` | `global_search_resource_groups` | `global` | `permission` | cli:admin resource-group search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `resource_preset` | `search` | `global_check_resource_presets` | `global` | `public` | rest:POST /resource/check-presets | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | `known_slot_types`를 명시로 넘겨 F7의 ContextVar 결함을 비껴간다 |
| `resource_preset` | `search` | `global_search_resource_presets` | `global` | `permission` | cli:admin resource-preset search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `session` | `search` | `global_search_resource_allocations` | `global` | `permission` | cli:resource-slot allocation search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user_fair_share` | `search` | `global_search_user_fair_shares` | `global` | `permission` | cli:fair-share user search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `user_usage_bucket` | `search` | `global_search_user_usage_buckets` | `global` | `permission` | cli:resource-usage user search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `resource_preset` | `search` | `check_preset_availability` | `scope` | `permission` | cli:admin resource-preset check-availability | ok | 403 not-enough-permission | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `agent` | `update` | `global_recalculate_agent_usage` | `global` | `permission` | rest:POST /resource/recalculate-usage | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | — |
| `resource_group` | `update` | `replace_resource_group_default_deployment_options` | `single_entity` | `permission` | cli:admin resource-group default-options get/replace | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `replace_resource_group_default_session_options` | `single_entity` | `permission` | cli:admin resource-group default-session-options get/replace | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `update_allowed_domains_for_resource_group` | `single_entity` | `permission` | cli:admin resource-group allow-domains | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `update_allowed_projects_for_resource_group` | `single_entity` | `permission` | cli:admin resource-group allow-projects | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `update_allowed_resource_groups_for_domain` | `single_entity` | `permission` | cli:admin resource-group allow-for-domain | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `update_allowed_resource_groups_for_project` | `single_entity` | `permission` | cli:admin resource-group allow-for-project | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `resource_group` | `update` | `update_resource_group` | `single_entity` | `permission` | cli:admin resource-group update | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |

### resource_group — 레거시 API (22행)

`api/gql_legacy/`에서 v2 프로세서에 도달하는 경로다. 위 표의 행과 같은 액션을 다른 경로로 실행한 것이라 총계에 더하지 않는다.

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `resource_preset` | `create` | `global_create_resource_preset` | `global` | `permission` | gql_legacy:CreateResourcePreset | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `global` | `W-AUDIT` | 감사 entity type 불일치 — A의 F10과 같은 지점 / `scaling_group_name`을 받아 생성하지만 그렇게 만든 preset은 레거시가 다시 못 찾는다 (LC1) |
| `resource_preset` | `update` | `update_resource_preset` | `single_entity` | `permission` | gql_legacy:ModifyResourcePreset | 404 database_access_not-found (name+그룹) / ok (id) | 200 `ok:false` "no permission" | 일치 | `E-ARG` | 인자 발산 — `_resolve_preset_id`가 `LookupResourcePresetAction(name=...)`만 넘겨 그룹 소속 preset을 name으로 영영 못 찾는다 (L1, BA-7501) |
| `resource_preset` | `delete` | `delete_resource_preset` | `single_entity` | `permission` | gql_legacy:DeleteResourcePreset | 404 database_access_not-found (name+그룹) / ok (id) | 200 `ok:false` "no permission" | 일치 | `E-ARG` | 인자 발산 — 같은 lookup 결함에 더해 `Arguments`에 그룹 인자 자체가 없어 스키마 변경 없이는 우회로가 없다 (L1, BA-7501) |
| `resource_preset` | `create` | (입력 타입) `CreateResourcePresetInput` | — | — | gql_legacy:CreateResourcePreset이 실어 나름 | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 뮤테이션이 아닌 `InputObjectType`이라 자체 경로가 없다. `CreateResourcePreset`으로 함께 확인 |
| `resource_group` | `create` | `global_create_resource_group` | `global` | `permission` | gql_legacy:CreateScalingGroup | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `global` | `W-AUDIT` | 감사 entity type 불일치 — A의 F10 / 인자·결과는 v2 경로와 동일 |
| `resource_group` | `update` | `update_resource_group` | `single_entity` | `permission` | gql_legacy:ModifyScalingGroup | ok | 200 `ok:false` "no permission" | 일치 | `성공` | v2 경로와 동일 — `update_resource_group \| resource_group \| update \| single_entity` |
| `resource_group` | `purge` | `purge_resource_group` | `single_entity` | `permission` | gql_legacy:DeleteScalingGroup | ok | 200 `ok:false` "no permission" | 일치 (entity_type 개별 미확인) | `성공` | v2 경로와 동일 |
| `resource_group` | `create` | `associate_resource_group_with_domains` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupWithDomain | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `domain`, 카탈로그는 `resource_group` | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 아닌데도 어긋난다 (LC2) |
| `resource_group` | `create` | `associate_resource_group_with_domains` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupsWithDomain | 404 database_access_not-found (혼합 배치) | 200 `ok:false` "no permission" | 행 없음 (결함) — lookup error 행만 남는다 | `E-BULK+W-AUDIT` | 벌크 응답 결함 — 잘못된 항목 하나로 전체가 atomic 실패, 항목별 응답이 없다 |
| `resource_group` | `delete` | `disassociate_resource_group_from_domains` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupWithDomain | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `domain` | `W-AUDIT` | 감사 entity type 불일치 (LC2) |
| `resource_group` | `delete` | `disassociate_resource_group_from_domains` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupsWithDomain | 404 database_access_not-found (혼합 배치) | 200 `ok:false` "no permission" | 행 없음 (결함) | `E-BULK+W-AUDIT` | 벌크 응답 결함 — atomic 실패, 유효 항목도 반영되지 않는다 |
| `resource_group` | `delete` | `disassociate_resource_group_from_domains` | `single_entity` | `permission` | gql_legacy:DisassociateAllScalingGroupsWithDomain | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 도메인의 모든 결합을 지운다. `default` 도메인에는 `default` 자원그룹 결합이 걸려 있고 버릴 도메인이 없다 |
| `resource_group` | `create` | `associate_resource_group_with_projects` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupWithUserGroup | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `project`, 카탈로그는 `resource_group` | `W-AUDIT` | 감사 entity type 불일치 (LC2) |
| `resource_group` | `create` | `associate_resource_group_with_projects` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupsWithUserGroup | 404 database_access_not-found (혼합 배치) | 200 `ok:false` "no permission" | 행 없음 (결함) | `E-BULK+W-AUDIT` | 벌크 응답 결함 — atomic 실패 |
| `resource_group` | `delete` | `disassociate_resource_group_from_projects` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupWithUserGroup | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `project` | `W-AUDIT` | 감사 entity type 불일치 (LC2) |
| `resource_group` | `delete` | `disassociate_resource_group_from_projects` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupsWithUserGroup | 404 database_access_not-found (혼합 배치) | 200 `ok:false` "no permission" | 행 없음 (결함) | `E-BULK+W-AUDIT` | 벌크 응답 결함 — atomic 실패 |
| `resource_group` | `delete` | `disassociate_resource_group_from_projects` | `single_entity` | `permission` | gql_legacy:DisassociateAllScalingGroupsWithGroup | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `project` | `W-AUDIT` | 감사 entity type 불일치 (LC2) / 빈 테이블에서 자기 결합만 추가·제거해 확인 |
| `resource_group` | `create` | `associate_resource_group_with_keypairs` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupWithKeyPair | ok | 200 `ok:false` "no permission" | 일치 | `성공` | 3부는 이 액션을 `W-UNREACH`로 뒀으나 레거시 경로가 있다 |
| `resource_group` | `create` | `associate_resource_group_with_keypairs` | `single_entity` | `permission` | gql_legacy:AssociateScalingGroupsWithKeyPair | 404 database_access_not-found (혼합 배치) | 200 `ok:false` "no permission" | 행 없음 (결함) | `E-BULK` | 벌크 응답 결함 — atomic 실패 |
| `resource_group` | `delete` | `disassociate_resource_group_from_keypairs` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupWithKeyPair | ok | 200 `ok:false` "no permission" | 일치 | `성공` | 3부는 이 액션을 `W-UNREACH`로 뒀으나 레거시 경로가 있다 |
| `resource_group` | `delete` | `disassociate_resource_group_from_keypairs` | `single_entity` | `permission` | gql_legacy:DisassociateScalingGroupsWithKeyPair | ok — 없는 항목을 조용히 버리고 성공 보고 | 200 `ok:false` "no permission" | 일치 | `E-BULK` | 벌크 응답 결함 — 같은 계열 중 유일하게 부분 성공을 전체 성공으로 답한다 |
| `agent` | `update` | `global_update_agent_resource_group` | `global` | `permission` | gql_legacy:ModifyAgent | ok | 200 `ok:false` "no permission" | 불일치 — entity_type이 `global` / `schedulable` 경로는 행 없음 (결함) | `W-AUDIT` | 인자 고정 — `policy=TERMINATE`·`force=False`를 하드코딩해 v2 CLI의 `--policy`·`--force`를 고를 수 없다  / `schedulable`만 넘기면 액션을 우회해 `agents`에 직접 쓴다 |

## resource_policy

20행 — 실패 2, 경고 15, 미실행 0, 성공 3.

### resource_policy — 성공 외 (17행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `keypair_resource_policy` | `get` | `get_keypair_resource_policy` | `single_entity` | `permission` | rest:GET /v2/resource-policies/keypair/{name} | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `keypair_resource_policy` | `create` | `global_create_keypair_resource_policy` | `global` | `permission` | rest:POST /v2/resource-policies/keypair | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `keypair_resource_policy` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 거부는 미들웨어가 선점해 행이 없다 (F10, F12) |
| `keypair_resource_policy` | `purge` | `global_purge_keypair_resource_policy` | `single_entity` | `permission` | rest:DELETE /v2/resource-policies/keypair/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `keypair_resource_policy` | `search` | `global_search_keypair_resource_policies` | `global` | `permission` | rest:POST /v2/resource-policies/keypair/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `keypair_resource_policy` | `search` | `search_keypair_resource_policies` | `scope` | `permission` | rest:GET /v2/resource-policies/keypair/my | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 정책 주인이 자기 정책을 못 읽는다 (F6) |
| `keypair_resource_policy` | `update` | `update_keypair_resource_policy` | `single_entity` | `permission` | rest:PATCH /v2/resource-policies/keypair/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `project_resource_policy` | `get` | `get_project_resource_policy` | `single_entity` | `permission` | rest:GET /v2/resource-policies/project/{name} | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `project_resource_policy` | `create` | `global_create_project_resource_policy` | `global` | `permission` | rest:POST /v2/resource-policies/project | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `project_resource_policy` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 거부는 미들웨어가 선점해 행이 없다 (F10, F12) |
| `project_resource_policy` | `purge` | `global_purge_project_resource_policy` | `single_entity` | `permission` | rest:DELETE /v2/resource-policies/project/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `project_resource_policy` | `search` | `global_search_project_resource_policies` | `global` | `permission` | rest:POST /v2/resource-policies/project/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `project_resource_policy` | `update` | `update_project_resource_policy` | `single_entity` | `permission` | rest:PATCH /v2/resource-policies/project/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user_resource_policy` | `get` | `get_user_resource_policy` | `single_entity` | `permission` | rest:GET /v2/resource-policies/user/{name} | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user_resource_policy` | `create` | `global_create_user_resource_policy` | `global` | `permission` | rest:POST /v2/resource-policies/user | ok | 403 backendai_generic_forbidden | 불일치 — 카탈로그 `user_resource_policy` / 감사 `global` | `W-AUDIT` | entity type 불일치 — 거부는 미들웨어가 선점해 행이 없다 (F10, F12) |
| `user_resource_policy` | `purge` | `global_purge_user_resource_policy` | `single_entity` | `permission` | rest:DELETE /v2/resource-policies/user/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |
| `user_resource_policy` | `search` | `global_search_user_resource_policies` | `global` | `permission` | rest:POST /v2/resource-policies/user/search | ok | 403 backendai_generic_forbidden | 행 없음 (결함) | `W-AUDIT` | 거부 행 없음 — 미들웨어가 선점한다 (F12) |
| `user_resource_policy` | `search` | `search_user_resource_policies` | `scope` | `permission` | rest:GET /v2/resource-policies/user/my | ok | 403 role_create_forbidden | 일치 | `E-GATE` | 권한 부족 — 정책 주인이 자기 정책을 못 읽는다 (F6) |
| `user_resource_policy` | `update` | `update_user_resource_policy` | `single_entity` | `permission` | rest:PATCH /v2/resource-policies/user/{name} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE+W-AUDIT` | 게이트 선점 — superadmin_required가 RBAC를 선점한다 (F12) |

### resource_policy — 성공 (3행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `keypair_resource_policy` | `lookup` | `lookup_keypair_resource_policy` | `lookup` | `permission` | 없음 (내부 호출: `/v2/resource-policies/keypair/{name}` GET·PATCH·DELETE 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `project_resource_policy` | `lookup` | `lookup_project_resource_policy` | `lookup` | `permission` | 없음 (내부 호출: `/v2/resource-policies/project/{name}` GET·PATCH·DELETE 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `user_resource_policy` | `lookup` | `lookup_user_resource_policy` | `lookup` | `permission` | 없음 (내부 호출: `/v2/resource-policies/user/{name}` GET·PATCH·DELETE 선행) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |

### resource_policy — 레거시 API (10행)

`api/gql_legacy/`에서 v2 프로세서에 도달하는 경로다. 위 표의 행과 같은 액션을 다른 경로로 실행한 것이라 총계에 더하지 않는다.

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `keypair_resource_policy` | `lookup` | `lookup_keypair_resource_policy` | `lookup` | `permission` | gql_legacy:Query.keypair_resource_policy | ok | 403 `role_create_forbidden` + `denied` 행 | 일치 | `W-GATE` | 게이트 발산 — 레거시는 RBAC가 판단하고 거부 행을 남긴다. REST `/v2/resource-policies/keypair/{name}`은 미들웨어가 선점해 아무것도 남기지 않는다 |
| `user_resource_policy` | `lookup` | `lookup_user_resource_policy` | `lookup` | `permission` | gql_legacy:Query.user_resource_policy | ok | 403 `role_create_forbidden` + `denied` 행 | 일치 | `W-GATE` | 게이트 발산 — 레거시 경로가 v2 경로보다 감사 가능하다 |
| `keypair_resource_policy` | `create` | `global_create_keypair_resource_policy` | `global` | `permission` | gql_legacy:CreateKeyPairResourcePolicy | ok | 200 `ok:false` | 불일치 — entity_type `global` | `성공` | v2와 같은 액션·같은 기록. `max_quota_scope_size`를 정수로 받는 점만 DTO 표기가 다르다 |
| `keypair_resource_policy` | `update` | `update_keypair_resource_policy` | `single_entity` | `permission` | gql_legacy:ModifyKeyPairResourcePolicy | ok | 200 `ok:false` | 일치 | `성공` | `lookup(name)` → `update(entity_id)`로 v2 경로와 인자가 같다 |
| `keypair_resource_policy` | `purge` | `global_purge_keypair_resource_policy` | `single_entity` | `permission` | gql_legacy:DeleteKeyPairResourcePolicy | ok | 200 `ok:false` | 일치 | `성공` | — |
| `user_resource_policy` | `create` | `global_create_user_resource_policy` | `global` | `permission` | gql_legacy:CreateUserResourcePolicy | ok | 200 `ok:false` | 불일치 — entity_type `global` | `성공` | — |
| `user_resource_policy` | `update` | `update_user_resource_policy` | `single_entity` | `permission` | gql_legacy:ModifyUserResourcePolicy | ok | 200 `ok:false` | 일치 | `성공` | — |
| `user_resource_policy` | `purge` | `global_purge_user_resource_policy` | `single_entity` | `permission` | gql_legacy:DeleteUserResourcePolicy | ok | 200 `ok:false` | 일치 | `성공` | — |
| `project_resource_policy` | `create` | `global_create_project_resource_policy` | `global` | `permission` | gql_legacy:CreateProjectResourcePolicy | ok | 200 `ok:false` | 불일치 — entity_type `global` | `성공` | — |
| `project_resource_policy` | `purge` | `global_purge_project_resource_policy` | `single_entity` | `permission` | gql_legacy:DeleteProjectResourcePolicy | ok | 200 `ok:false` | 일치 | `성공` | `ModifyProjectResourcePolicy`도 같은 모양이라 이 행에 함께 둔다 |

## system

45행 — 실패 0, 경고 14, 미실행 1, 성공 30.

### system — 성공 외 (15행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `login_client_type` | `create` | `create_login_client_type` | `global` | `permission` | cli:admin login-client-type create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `resource_slot_type` | `create` | `create_resource_slot_type` | `global` | `permission` | cli:resource-slot slot-type create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) / 전역 싱글턴 — 비활성·비필수로 추가 후 삭제, 14종 복원 |
| `retention_policy` | `create` | `create_retention_policy` | `global` | `permission` | rest:POST /v2/retention-policies | ok / 409 retention-policy_generic_conflict | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) / category enum 소진 — 시드 8종이 이미 차 있어 성공 경로가 409뿐 (F10) |
| `runtime_variant` | `create` | `create_runtime_variant` | `global` | `permission` | cli:admin runtime-variant create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `runtime_variant_preset` | `create` | `create_runtime_variant_preset` | `global` | `permission` | cli:admin runtime-variant-preset create | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `resource_slot_type` | `get` | `get_resource_slot_type` | `single_entity` | `public` | 없음 | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 클라이언트 경로 없음 — resource-slots registry에 단건 GET이 없다 |
| `retention_policy` | `get` | `get_retention_policy` | `single_entity` | `permission` | rest:GET /v2/retention-policies/{id} | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `runtime_variant` | `lookup` | `lookup_runtime_variant` | `lookup` | `public` | 내부 lookup | 미실행 | 미실행 | 해당 없음 | `X` | 미실행 — 실행한 경로 어디에서도 lookup 행이 남지 않아 발화를 확인하지 못했다 |
| `client_ip_masking_policy` | `purge` | `purge_client_ip_masking_policy` | `single_entity` | `permission` | rest:POST /v2/client-ip-masking-policies/purge | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) |
| `resource_slot_type` | `purge` | `purge_resource_slot_type` | `single_entity` | `permission` | cli:resource-slot slot-type delete | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 전역 싱글턴 — 14종 복원 확인 |
| `retention_policy` | `purge` | `delete_retention_policy` | `single_entity` | `permission` | rest:DELETE /v2/retention-policies/{id} | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / hard delete — 이후 purge가 404, purge와 구분되지 않는다 (F11) |
| `retention_policy` | `purge` | `purge_retention_policy` | `single_entity` | `permission` | rest:POST /v2/retention-policies/{id}/purge | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / delete와 동일한 파괴 연산 — 선행 delete 후 도달 불가 (F11) |
| `resource_slot_type` | `update` | `update_resource_slot_type` | `global` | `permission` | cli:resource-slot slot-type update | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `retention_policy` | `update` | `update_retention_policy` | `single_entity` | `permission` | rest:PATCH /v2/retention-policies/{id} | ok | 403 backendai_generic_forbidden | 일치 | `W-GATE` | 라우트 선행 — `superadmin_required`가 RBAC validator보다 먼저 거부한다 (auth.py:917) / 경로·본문 id 중복 — 본문 `id`가 필수인데 무시된다 (F8) |
| `client_ip_masking_policy` | `upsert` | `upsert_client_ip_masking_policy` | `global` | `permission` | rest:POST /v2/client-ip-masking-policies/upsert | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) / 전역 싱글턴 — 스냅샷 후 복원 완료 |

### system — 성공 (30행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `etcd_config` | `delete` | `delete_etcd_config` | `global` | `permission` | rest:POST /config/delete | ok | 403 backendai_generic_forbidden | 일치 | `성공` | `ba7489c/` 프리픽스에만 기록 후 삭제 |
| `runtime_variant` | `get` | `public_bulk_get_runtime_variants` | `bulk` | `public` | gql:runtimeVariantPresets | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 벌크 정상 — 입력마다 위치대로, 중복 독립, 없는 id는 null (F16) |
| `etcd_config` | `get` | `get_etcd_config` | `global` | `permission` | rest:POST /config/get | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | 없는 키는 404가 아니라 `result: null` |
| `etcd_config` | `get` | `get_resource_metadata` | `global` | `public` | rest:GET /config/resource-slots/details | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `etcd_config` | `get` | `get_resource_slots` | `global` | `public` | rest:GET /config/resource-slots | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `etcd_config` | `get` | `get_vfolder_types` | `global` | `public` | rest:GET /config/vfolder-types | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `manager_admin` | `get` | `fetch_manager_status` | `global` | `permission` | rest:GET /manager/status | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `manager_admin` | `get` | `get_db_connection_status` | `global` | `permission` | rest:GET /manager/prom | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `manager_admin` | `get` | `get_manager_announcement` | `global` | `permission` | rest:GET /manager/announcement | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `login_client_type` | `get` | `get_login_client_type` | `single_entity` | `public` | cli:login-client-type get | ok | ok | 일치 | `성공` | — |
| `runtime_variant` | `get` | `public_get_runtime_variant` | `single_entity` | `public` | cli:runtime-variant get | ok | ok | 일치 | `성공` | — |
| `runtime_variant_preset` | `get` | `public_get_runtime_variant_preset` | `single_entity` | `public` | cli:runtime-variant-preset get | ok | ok | 일치 | `성공` | — |
| `resource_slot_type` | `lookup` | `lookup_resource_slot_type` | `lookup` | `public` | cli:resource-slot slot-type delete (내부 lookup) | 404 database_access_not-found | 해당 없음 | 일치 | `성공` | — |
| `login_client_type` | `purge` | `purge_login_client_type` | `single_entity` | `permission` | cli:admin login-client-type delete | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `runtime_variant` | `purge` | `purge_runtime_variant` | `single_entity` | `permission` | cli:admin runtime-variant delete | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | 자식 정리 누락 — preset의 `runtime_variant_id`가 매달린 채 남는다 (F17) |
| `runtime_variant_preset` | `purge` | `purge_runtime_variant_preset` | `single_entity` | `permission` | cli:admin runtime-variant-preset delete | ok | 403 backendai_generic_forbidden | 일치 (entity_type 개별 미확인) | `성공` | — |
| `client_ip_masking_policy` | `search` | `search_client_ip_masking_policies` | `global` | `permission` | rest:POST /v2/client-ip-masking-policies/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `login_client_type` | `search` | `search_login_client_types` | `global` | `public` | cli:admin login-client-type search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 선언은 public — CLI는 `admin` 그룹에 두고 "admin scope"라 적는다 |
| `resource_slot_type` | `search` | `search_resource_slot_types` | `global` | `public` | cli:resource-slot slot-type search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `retention_policy` | `search` | `search_retention_policies` | `global` | `permission` | rest:POST /v2/retention-policies/search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `runtime_variant` | `search` | `search_runtime_variants` | `global` | `public` | cli:runtime-variant search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 선언은 public — CLI는 `admin` 그룹에 둔다 |
| `runtime_variant_preset` | `search` | `search_runtime_variant_presets` | `global` | `public` | cli:runtime-variant-preset search | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | 선언은 public — CLI는 `admin` 그룹에 둔다 |
| `service_catalog` | `search` | `search_service_catalogs` | `global` | `permission` | cli:admin service-catalog search | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `etcd_config` | `update` | `set_etcd_config` | `global` | `permission` | rest:POST /config/set | ok | 403 backendai_generic_forbidden | 일치 | `성공` | `ba7489c/` 프리픽스에만 기록 후 삭제 |
| `manager_admin` | `update` | `perform_scheduler_ops` | `global` | `permission` | rest:POST /manager/scheduler/operation | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 미지의 op가 400이 아니라 500 — enum 생성자가 try 밖 (F9) |
| `manager_admin` | `update` | `update_manager_announcement` | `global` | `permission` | rest:POST /manager/announcement | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 전역 싱글턴 — 스냅샷 후 복원 완료 |
| `manager_admin` | `update` | `update_manager_status` | `global` | `permission` | rest:PUT /manager/status | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 전역 싱글턴 — 현재 값 `running`으로만 기록 |
| `login_client_type` | `update` | `update_login_client_type` | `single_entity` | `permission` | cli:admin login-client-type update | ok | 403 backendai_generic_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `runtime_variant` | `update` | `update_runtime_variant` | `single_entity` | `permission` | cli:admin runtime-variant update | ok | 403 backendai_generic_forbidden | 일치 | `성공` | — |
| `runtime_variant_preset` | `update` | `update_runtime_variant_preset` | `single_entity` | `permission` | cli:admin runtime-variant-preset update | ok | 403 backendai_generic_forbidden | 일치 | `성공` | — |

## vfolder

70행 — 실패 5, 경고 21, 미실행 5, 성공 39.

### vfolder — 성공 외 (31행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `vfolder` | `delete` | `vfolder bulk-delete` (어댑터 루프) | `single_entity` | `permission` | `cli:vfolder bulk-delete` | 해당 없음 | 403 role_create_forbidden | 일치 (처리된 항목만 행 생성) | `E-BULK` | 배치 붕괴 — 4개 입력에 403 하나. 항목별 응답이 없고, 그런데도 허용된 항목은 soft delete까지 진행된다 (F9) |
| `vfolder` | `purge` | `vfolder bulk-purge` (어댑터 루프) | `single_entity` | `permission` | `cli:vfolder bulk-purge` | 해당 없음 | ok (항목별 실패는 본문 안) | 일치 (처리된 항목만 행 생성) | `E-BULK` | 위치 대응 상실 — `purged_count`와 `failed[]`만 주어 입력 위치를 되짚을 수 없고 중복이 두 번 세어진다 (F9) |
| `vfolder` | `update` | `change_vfolder_ownership` | `single_entity` | `permission` | `rest-v1:POST /folders/_/change-ownership` | 400 api_parsing_invalid-parameters | 403 backendai_generic_forbidden | 행 없음 (요청 파싱 단계에서 거부 — 액션 미실행) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 선언된 단일 엔티티 게이트를 대체한다 |
| `vfolder` | `get` | `create_vfolder_archive_download_session` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/request-download-archive` | 400 api_parsing_invalid-parameters | 403 role_create_forbidden | 해당 없음 | `X` | 요청 모델 불일치 — 검증 단계를 통과하지 못했다 |
| `vfolder` | `create` | `create_vfolder_upload_session` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/request-upload` | ok | 403 role_create_forbidden | 일치 | `W-GATE` | v1/v2 불일치 — v1은 CREATE, v2는 UPDATE를 요구한다 (F10) |
| `vfolder` | `update` | `create_vfolder_upload_session_v2` | `single_entity` | `permission` | `rest:POST /v2/vfolders/{id}/upload-session` | ok | 403 role_create_forbidden | 일치 | `W-GATE` | v1/v2 불일치 — v2는 UPDATE, v1은 CREATE를 요구한다 (F10) |
| `vfolder` | `delete` | `delete_vfolder_files` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/delete-files` | ok | 403 role_create_forbidden | 일치 | `W-GATE` | v1/v2 불일치 — v1은 SOFT_DELETE, v2는 UPDATE를 요구한다 (F10) |
| `vfolder` | `update` | `delete_vfolder_files_v2` | `single_entity` | `permission` | `cli:vfolder rm` | 404 on | 403 role_create_forbidden | 일치 | `W-GATE` | v1/v2 불일치 — v2는 UPDATE, v1은 SOFT_DELETE를 요구한다 (F10) |
| `vfolder` | `get` | `get_task_logs` | `scope` | `permission` | `rest (session task-log route)` | 미실행 | 미실행 | 해당 없음 | `X` | 선행 조건 부재 — 컴퓨트 에이전트가 없어 세션 태스크 로그가 생기지 않는다 |
| `vfolder` | `get` | `get_vfolder_usage` | `single_entity` | `permission` | `rest-v1:GET /folders/_/usage` | 404 vfolder_read_not-found | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — `superadmin_required`가 RBAC 검사를 대체한다 |
| `vfolder` | `get` | `get_vfolder_usage_legacy` | `single_entity` | `permission` | `rest-v1:GET /folders/_/usage` | 404 | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `vfolder` | `get` | `get_vfolder_used_bytes` | `single_entity` | `permission` | `rest-v1:GET /folders/_/used-bytes` | 404 vfolder_read_not-found | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 |
| `vfolder` | `get` | `global_batch_load_vfolders` | `global` | `permission` | `gql:node/DataLoader` | 미실행 | 미실행 | 해당 없음 | `X` | 직접 구동 불가 — GraphQL DataLoader 배치 경로로만 실행된다 |
| `vfolder` | `update` | `global_mount_host` | `global` | `permission` | `rest-v1:POST /folders/_/mounts` | 200 while | 403 backendai_generic_forbidden | 일치 (`global_mount_host \| global \| update`, status=success) | `W-AUDIT` | entity type 불일치 — 카탈로그 `vfolder` / 감사 `global`. 등록된 에이전트가 없어 실제로는 아무것도 마운트하지 않고 200을 준다 |
| `vfolder` | `update` | `global_umount_host` | `global` | `permission` | `rest-v1:POST /folders/_/umounts` | ok | 403 backendai_generic_forbidden | 일치 (status=success) | `W-AUDIT` | entity type 불일치 — 카탈로그 `vfolder` / 감사 `global` |
| `vfolder` | `lookup` | `lookup_accessible_vfolder` | `lookup` | `permission` | `rest-v1:GET /folders/{name} (name form)` | 미실행 | 미실행 | 해당 없음 | `X` | 별도 구동 안 함 — v1 이름 형태 경로에서 `_vfolder_resolver`가 쓰는 내부 단계 |
| `vfolder` | `lookup` | `lookup_vfolder` | `lookup` | `permission` | `없음` | 미실행 | 미실행 | 해당 없음 | `W-UNREACH` | 직접 경로 없음 — 단일 엔티티 vfolder 액션 내부에서만 실행된다 |
| `vfolder` | `search` | `public_list_shared_vfolders` | `global` | `public` | `rest-v1:GET /folders/_/shared` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `W-GUARD` | 게이트 근거 미흡 — `public`을 정당화하려면 결과가 호출자와 관련된 공유로 한정돼야 하나, `list_shared_vfolder_permissions(None)`이 vfolder 필터 없이 시스템 전체 공유 행을 돌려준다. 소유자도 수신자도 아닌 사용자가 수신자 UUID와 이메일까지 읽는다 (F17) |
| `vfolder` | `purge` | `purge_vfolder_v2` | `single_entity` | `permission` | `cli:vfolder purge` | 404 on | 403 role_create_forbidden | 일치 | `W-AUDIT` | purge가 purge가 아님 — `delete_vfolders_forever`를 불러 행이 `delete-complete`로 남는데 감사는 `purge \| success` (F5) |
| `vfolder` | `update` | `share_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/share` | 404 | 403 backendai_generic_forbidden | 일치 (status=error) | `E-GATE` | 라우트 게이트 선점 — `admin_required`라 폴더 소유자가 자기 폴더를 공유하지 못한다 (F7) |
| `vfolder` | `delete` | `unshare_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/unshare` | 404 | 403 backendai_generic_forbidden | 일치 (status=error, operation=delete) | `W-GATE` | 라우트 게이트 선점 — 같은 사유 (F7) |
| `vfolder` | `update` | `update_vfolder_sharing_status` | `single_entity` | `permission` | `rest-v1:POST /folders/_/sharing` | 400 api_parsing_invalid-parameters | 미실행 | 해당 없음 | `X` | 요청 모델 불일치 — 검증 단계를 통과하지 못했다 |
| `vfolder` | `create` | `vfolder_mkdir` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/mkdir` | ok | 403 role_create_forbidden | 일치 | `W-GATE` | v1/v2 불일치 — 같은 효과에 v1은 CREATE, v2는 UPDATE를 요구한다 (F10) |
| `vfolder` | `update` | `vfolder_mkdir_v2` | `single_entity` | `permission` | `cli:vfolder mkdir` | 404 on | 403 role_create_forbidden | 일치 (`vfolder_mkdir_v2\|vfolder\|update\|single_entity`) | `W-GATE` | v1/v2 불일치 — 같은 효과에 v2는 UPDATE, v1은 CREATE를 요구한다 (F10) |
| `vfolder_invitation` | `update` | `accept_invitation` | `single_entity` | `permission` | `rest-v1:POST /folders/invitations/accept` | ok | 403 role_create_forbidden | 일치 (status=denied) | `E-GATE` | 권한 행 부재 — 수신자가 자기 앞으로 온 초대를 수락하지 못한다 (F6) |
| `vfolder_invitation` | `purge` | `leave_invited_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/leave` | ok | 403 role_create_forbidden | 일치 (status=denied) | `W-GATE` | 권한 행 부재 — 같은 사유 (F6) |
| `vfolder_invitation` | `search` | `list_invitation` | `scope` | `permission` | `rest-v1:GET /folders/invitations/list` | ok | 403 role_create_forbidden | 일치 (status=denied) | `E-GATE` | 권한 행 부재 — `vfolder_invitation`에 permission 행이 하나도 없어 자기 user 스코프 READ조차 거부된다 (F6) |
| `vfolder_invitation` | `search` | `list_sent_invitations` | `scope` | `permission` | `rest-v1:GET /folders/invitations/list-sent` | ok | 403 role_create_forbidden | 일치 (status=denied) | `W-GATE` | 권한 행 부재 — 같은 사유 (F6) |
| `vfolder_invitation` | `update` | `reject_invitation` | `single_entity` | `permission` | `rest-v1:POST /folders/invitations/delete` | ok | 403 role_create_forbidden | 일치 (status=denied) | `W-GATE` | 권한 행 부재 — 같은 사유 (F6) |
| `vfolder_invitation` | `purge` | `revoke_invited_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/invitations/delete` | ok | 403 role_create_forbidden | 일치 (status=denied) | `W-GATE` | 권한 행 부재 — 같은 사유 (F6) |
| `vfolder_invitation` | `update` | `update_invitation` | `single_entity` | `permission` | `rest-v1:POST /folders/invitations/update/{inv_id}` | ok | 403 role_create_forbidden | 일치 (status=denied) | `W-GATE` | 권한 행 부재 — 같은 사유 (F6) |

### vfolder — 성공 (39행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `vfolder` | `get` | `get_vfolder_v2` | `single_entity` | `permission` | `cli:vfolder get / rest:GET /v2/vfolders/{id}` | ok | ok | 행 없음 (성공 read — 정책상 정상); 거부는 기록됨 | `성공` | 역할 부여대로 동작 — `role_domain_default_member`가 domain 스코프 vfolder READ를 가져 도메인 구성원이 통과한다. 액션이 아니라 역할 프리셋의 범위 문제이고, v1은 소유권을 검사해 모델이 갈린다 (F1) |
| `vfolder` | `create` | `clone_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/clone` | ok | 403 role_create_forbidden | 일치 (status=error) | `성공` | — |
| `vfolder` | `create` | `clone_vfolder_v2` | `single_entity` | `permission` | `cli:vfolder clone` | 400 vfolder_access_invalid-parameters | 403 role_create_forbidden | 일치 (status=error) | `성공` | — |
| `vfolder` | `create` | `create_vfolder` | `scope` | `permission` | `rest-v1:POST /folders` | ok | ok | 일치 | `성공` | — |
| `vfolder` | `get` | `create_vfolder_download_session` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/request-download` | ok | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `create_vfolder_download_session_v2` | `single_entity` | `permission` | `rest:POST /v2/vfolders/{id}/download-session` | ok | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `create` | `create_vfolder_in_project` | `scope` | `permission` | `cli:vfolder project-create` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `create` | `create_vfolder_v2` | `scope` | `permission` | `cli:vfolder create` | ok | ok | 일치 (entity_type `vfolder`, kind `scope`) | `성공` | — |
| `vfolder` | `purge` | `delete_forever_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/delete-from-trash-bin` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `delete` | `delete_vfolder_files_async` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/delete-files-async` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `delete` | `delete_vfolder_v2` | `single_entity` | `permission` | `cli:vfolder delete` | 404 on | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `purge` | `force_delete_vfolder` | `single_entity` | `permission` | `rest-v1:DELETE /folders/{id}/force` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `get` | `get_vfolder` | `single_entity` | `permission` | `rest-v1:GET /folders/{id} (v1 alias)` | 404 | 404 | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `get_vfolder_legacy_row` | `single_entity` | `permission` | `rest-v1:GET /folders/{id}` | 404 | 404 for | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `get_vfolder_quota` | `single_entity` | `permission` | `rest-v1:GET /folders/_/quota` | 404 vfolder_read_not-found | 400 storage-proxy_request_content-type-mismatch | 일치 (status=error — 실패는 항상 기록) | `성공` | 다운스트림 파싱 실패 — 같은 사유 (F16.6) |
| `vfolder` | `get` | `global_get_fstab_contents` | `global` | `permission` | `rest-v1:GET /folders/_/fstab` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `global_get_volume_perf_metric` | `global` | `permission` | `rest-v1:GET /folders/_/perf-metric` | 400 api_parsing_invalid-parameters | 403 backendai_generic_forbidden | 해당 없음 | `성공` | — |
| `vfolder` | `search` | `global_list_all_hosts` | `global` | `permission` | `rest-v1:GET /folders/_/all-hosts` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `global_list_allowed_types` | `global` | `permission` | `rest-v1:GET /folders/_/allowed-types` | ok | 403 user_auth_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `global_list_mounts` | `global` | `permission` | `rest-v1:GET /folders/_/mounts` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `global_search_vfolders` | `global` | `permission` | `cli:vfolder admin-search` | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `list_shared_vfolders` | `single_entity` | `permission` | `rest-v1:GET /folders/_/shared` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `list_vfolder` | `scope` | `permission` | `rest-v1:GET /folders` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `list_vfolder_files` | `single_entity` | `permission` | `rest-v1:GET /folders/{id}/files` | ok | 404 for | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `list_vfolder_files_v2` | `single_entity` | `permission` | `cli:vfolder ls` | 404 on | 403 role_create_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `delete` | `move_to_trash_vfolder` | `single_entity` | `permission` | `rest-v1:DELETE /folders` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `update` | `move_vfolder_file` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/move-file` | 400 vfolder_generic_bad-request | 403 role_create_forbidden | 일치 (status=error) | `성공` | — |
| `vfolder` | `update` | `move_vfolder_file_v2` | `single_entity` | `permission` | `cli:vfolder mv` | 404 on | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `purge` | `purge_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/purge` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `update` | `rename_vfolder_file` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/rename-file` | 400 vfolder_generic_bad-request | 403 role_create_forbidden | 일치 (status=error) | `성공` | — |
| `vfolder` | `restore` | `restore_vfolder_from_trash` | `single_entity` | `permission` | `cli:vfolder restore / rest-v1:POST /folders/restore-from-trash-bin` | 404 on | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `search` | `search_hosts` | `scope` | `permission` | `rest-v1:GET /folders/_/hosts` | 200 with | 200 with | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `get` | `search_storage_host_permissions` | `scope` | `permission` | `cli:my storage-host permissions` | ok | ok | 일치 (`vfolder\|get\|scope`) | `성공` | — |
| `vfolder` | `search` | `search_user_vfolders` | `scope` | `permission` | `cli:vfolder my-search` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `search` | `search_vfolders_in_project` | `scope` | `permission` | `cli:vfolder project-search` | ok | ok | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `vfolder` | `update` | `update_vfolder_attribute` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/rename and /update-options` | ok | 403 role_create_forbidden | 일치 | `성공` | — |
| `vfolder` | `update` | `update_vfolder_quota` | `single_entity` | `permission` | `rest-v1:POST /folders/_/quota` | ok | 400 storage-proxy_request_content-type-mismatch | 일치 (status=error) | `성공` | 다운스트림 파싱 실패 — 소유자 호출이 `storage-proxy_request_content-type-mismatch` 400으로 끝난다 (F16.6) |
| `vfolder_invitation` | `create` | `invite_vfolder` | `single_entity` | `permission` | `rest-v1:POST /folders/{id}/invite` | ok | ok | 일치 (`invite_vfolder\|vfolder\|create\|single_entity`) | `성공` | 권한 행 부재의 반대편 — vfolder에 걸린 게이트라 통과하지만, 만들어진 초대는 아무도 다루지 못한다 (F6) |
| `vfolder_invitation` | `update` | `update_invited_vfolder_mount_permission` | `single_entity` | `permission` | `rest-v1:POST /folders/_/shared` | ok | ok | 일치 (status=success) | `성공` | 허위 성공 — 공유가 없는 (vfolder, user) 쌍에도 200 `shared vfolder permission updated`를 준다 (F16.5) |

## visibility

13행 — 실패 4, 경고 5, 미실행 0, 성공 4.

### visibility — 성공 외 (9행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `export` | `create` | `export_audit_logs_c_s_v` | `global` | `permission` | cli:admin export audit-logs | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `export` | `create` | `export_keypairs_c_s_v` | `global` | `permission` | cli:admin export keypairs | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `export` | `create` | `export_projects_c_s_v` | `global` | `permission` | cli:admin export projects | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `export` | `create` | `export_sessions_c_s_v` | `global` | `permission` | cli:admin export sessions | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `export` | `create` | `export_users_c_s_v` | `global` | `permission` | cli:admin export users | ok | 403 backendai_generic_forbidden | 불일치 — entity_type이 `global`, 카탈로그 선언과 다름 | `W-AUDIT` | 감사 entity type 불일치 — `global` kind가 선언 대신 `global`을 기록 (A의 F10) |
| `export` | `create` | `export_my_keypairs_c_s_v` | `scope` | `permission` | cli:my export keypairs | ok | 403 user_auth_forbidden | 일치 | `E-GATE` | superadmin 선행 — 핸들러가 global `get_report`를 먼저 불러 scope 게이트에 닿지 않는다 (F4) |
| `export` | `create` | `export_my_sessions_c_s_v` | `scope` | `permission` | cli:my export sessions | ok | 403 user_auth_forbidden | 일치 | `E-GATE` | superadmin 선행 — 핸들러가 global `get_report`를 먼저 불러 scope 게이트에 닿지 않는다 (F4) |
| `audit_log` | `search` | `scoped_search_audit_logs` | `bulk` | `permission` | gql:scopedAuditLogsV2 | 500 backendai_parsing_invalid-parameters | 같은 오류 | 해당 없음 | `E-EXEC` | `client_ip` 타입 불일치 — `scopedAuditLogsV2`도 같은 결함으로 항상 실패 (브리프 F1) |
| `audit_log` | `search` | `search_audit_logs` | `global` | `permission` | cli:audit-log search | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | 해당 없음 | `E-EXEC` | `client_ip` 타입 불일치 — REST·`adminAuditLogsV2` 모두 항상 실패, 게이트 관측 불가 (브리프 F1) |

### visibility — 성공 (4행)

| entity_type | operation | action_name | kind | gate | 경로 | admin | 비-admin | 감사 | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|
| `export` | `create` | `export_sessions_by_project_c_s_v` | `scope` | `permission` | cli:admin export sessions-by-project | ok | 403 user_auth_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `export` | `create` | `export_users_by_domain_c_s_v` | `scope` | `permission` | cli:admin export users-by-domain | ok | 403 user_auth_forbidden | 일치 | `성공` | 라우트가 superadmin 전용 — `ActionGate`에 superadmin 값이 없어 카탈로그는 `permission`으로 적힌다. 게이트 자체는 의도대로 동작한다 |
| `export` | `get` | `get_report` | `global` | `permission` | cli:admin export get-report | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |
| `export` | `search` | `list_reports` | `global` | `permission` | cli:admin export list-reports | ok | 403 backendai_generic_forbidden | 행 없음 (성공 read — 정책상 정상) | `성공` | — |

## 레거시 API 경로 발견

concern별 「레거시 API」 하위 섹션의 48행에서 나온 것이다. 레거시 핸들러 자체의 동작 차이는
여기 싣지 않는다 — 이 문서가 보는 것은 v2 액션이다.

### 신원·권한

### LA1 — 레거시만 리소스 그룹을 도메인에 붙일 수 있다

`global_create_domain_node` / `update_domain_node`, 두 경로 모두 같은 액션에 닿는다.

| | 레거시 GQL | REST v2 |
|---|---|---|
| 생성 | `CreateDomainNodeInput.scaling_groups` → `_resolve_sgroup_ids` → `resource_group_ids` | `CreateDomainInput`에 필드 없음 |
| 수정 | `ModifyDomainNodeInput.sgroups_to_add` / `sgroups_to_remove` | `UpdateDomainInput`에 필드 없음 |

```bash
# 레거시로 만들면 연결까지 된다
./bai gql 'mutation { create_domain_node(input:{name:"ba7489a-legacy-dom2", scaling_groups:["default"],
           total_resource_slots:"{}", allowed_vfolder_hosts:"{}"}) { item { name } } }'
# 레거시로 나중에 붙일 수도 있다
./bai gql 'mutation { modify_domain_node(input:{id:"RG9tYWluTm9kZTpiYTc0ODlhLWRvbQ==",
           sgroups_to_add:["default"]}) { item { name } } }'
```
```sql
select d.name, count(s.*) as rg from domains d
  left join sgroups_for_domains s on s.domain_id=d.id where d.name like 'ba7489a%' group by d.name;
-- ba7489a-dom          0   ← POST /v2/domains 로 만든 것 (뒤에 modify_domain_node 로 1이 됨)
-- ba7489a-legacy-dom2  1   ← create_domain_node 로 만든 것
```

영향: REST v2만 쓰는 클라이언트는 도메인에 리소스 그룹을 붙일 수 없다. 3부는 REST 경로만 몰아 이
액션을 `성공`으로 기록했는데, 그 판정은 인자 절반에 대한 것이다.

### LA2 — `POST /v2/domains`로 만든 도메인에는 기본 프로젝트가 없다

도메인을 만드는 액션이 둘이고, 하나만 기본 프로젝트를 만든다.

| 경로 | 액션 | 부수 효과 |
|---|---|---|
| `gql_legacy:CreateDomain`, `rest-v1:POST /admin/domains` | `global_create_domain` | `create_project` 가 이어 돈다 |
| `gql_legacy:CreateDomainNode`, `rest:POST /v2/domains` | `global_create_domain_node` | 없음 |

```
create_domain      → AUDIT global_create_domain|global|create|global|success
                     AUDIT create_project|project|create|scope|success
create_domain_node → AUDIT global_create_domain_node|global|create|global|success   (그것뿐)
```

영향: v2 경로로 만든 도메인은 프로젝트가 하나도 없는 상태로 남는다. 3부의 `global_create_domain`과
`global_create_domain_node` 두 행은 별개 액션이라 나란히 있었을 뿐, 부수 효과가 다르다는 것은
두 경로를 같이 몰아야 보인다.

### LA3 — 프로젝트 멤버십은 레거시 `modify_group`으로만 한 번에 고칠 수 있다

`update_project`가 `user_update_mode`·`user_uuids`를 받아 멤버십을 함께 고친다(`group.py:643`).
REST `UpdateProjectInput`에는 그 필드가 없고, 멤버십은 별도 액션(`assign_users_to_project` /
`unassign_users_from_project`)으로 갈라져 있다.

```bash
./bai gql 'mutation { modify_group(gid:"<proj>", props:{user_update_mode:"add",
           user_uuids:["<user>"]}) { ok msg } }'
```
```sql
select scope_type, scope_id, relation_type from association_scopes_entities where entity_id='<user>';
-- project | <proj> | auto     ← 써진다
```

두 경로 다 `association_scopes_entities`에 쓴다. 결과는 같고 표현만 갈린다.

### LC1 — BA-7501 확인. 레거시가 만든 그룹 소속 preset을 레거시가 다시 못 찾는다

이슈가 예측한 그대로이고, 예측보다 한 단계 나쁘다.

| 대상 | name으로 modify | name으로 delete | id로 |
|---|---|---|---|
| `scaling_group_name = "default"` | 404 Entity not found | 404 Entity not found | ok |
| `scaling_group_name = NULL` (대조군) | ok | ok | ok |

`lookup_resource_preset` 자체는 별도 클래스가 아니라 두 뮤테이션이 공통으로 타는 내부 경로여서
표에는 행을 두지 않았다. 원인은 정적으로도 확정된다. `_resolve_preset_id`(resource_preset.py:207)가
`LookupResourcePresetAction(name=name)`만 넘기고, `ResourcePresetNameLookup.conditions()`
(models/resource_preset/lookups.py:30)는 `resource_group_name`이 `None`이면
`scaling_group_name IS NULL`로 좁힌다.

세 가지를 덧붙인다.

1. **레거시만 쓰는 클라이언트는 자기가 만든 것을 지울 수 없다.** `create_resource_preset`은
   `props.scaling_group_name`을 받아 정상 생성한다. 그런데 그 preset은 곧바로
   `modify_resource_preset`·`delete_resource_preset`의 name 경로에서 사라진다.
   `DeleteResourcePreset.Arguments`에는 그룹 인자가 아예 없으므로 — 리드가 짚은 대로 —
   호출자 쪽 우회로가 없고 스키마를 고쳐야 한다. 확인한 그대로다.
2. **`props.scaling_group_name`을 줘도 소용없다.** 그 값은 갱신 페이로드로만 쓰이고
   `_resolve_preset_id`는 `id`와 `name`만 받는다. 실측으로 같은 404가 난다.
3. **읽기는 보인다.** 레거시 `resource_presets` 질의는 그 preset을 `scaling_group_name: "default"`로
   정상 반환한다. 한 스키마 안에서 보이지만 이름으로는 손댈 수 없는 상태다.

```
mutation { create_resource_preset(name:"X", props:{resource_slots:"...", scaling_group_name:"default"}) { ok } }  -> ok
mutation { modify_resource_preset(name:"X", props:{shared_memory:"1g"}) { ok } }                                   -> 404
mutation { delete_resource_preset(name:"X") { ok } }                                                               -> 404
{ resource_presets { name scaling_group_name } }                                                                   -> X / "default"
```

REST v2는 UUID로 풀어 영향이 없고, 3부가 기록한 경로가 그것뿐이라 여기서만 보인다.

### LC2 — 결합 액션 4건이 카탈로그와 다른 entity type을 기록한다

**A의 F10과 다른 발견이다. 합치면 안 된다.** F10은 "`global` kind 액션은 전부 `entity_type='global'`을
적는다"로, 규칙 하나에 원인 하나(`global_scope/monitor/audit_log.py:73`)다. 아래 넷은 `global`이 아니라
`single_entity` kind이고, 적히는 값도 `global`이 아니라 `domain`·`project`다. 원인이 다르므로 F10을
고쳐도 이 넷은 그대로 남는다.

| action_name | 카탈로그 | 실제 기록 |
|---|---|---|
| `associate_resource_group_with_domains` | `resource_group` | `domain` |
| `disassociate_resource_group_from_domains` | `resource_group` | `domain` |
| `associate_resource_group_with_projects` | `resource_group` | `project` |
| `disassociate_resource_group_from_projects` | `resource_group` | `project` |

keypair 짝(`associate_resource_group_with_keypairs`, `disassociate_resource_group_from_keypairs`)은
`resource_group`으로 정확히 기록한다. 같은 계열 여섯 중 넷만 어긋나므로 일괄 규칙이 아니라
개별 배선 문제로 보인다.
