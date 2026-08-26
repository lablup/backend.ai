# v2 액션 감사

v2 액션 계층이 선언한 것과 실제로 하는 일이 어긋나는 지점을 찾는 조사. 세 부분으로 나눠서
진행하며, 각 부분이 답할 수 있는 질문이 다르다.

| # | 조사 | 답하는 질문 | Jira | 상태 |
|---|---|---|---|---|
| 1 | [코드 상 wiring 조사](./01-wiring.md) | 배선이 카탈로그·규칙과 맞는가 | BA-7486 | 완료 |
| 2 | [권한 검사 로직 확인](./02-permission-logic.md) | 검사되는 권한 자체가 옳은가 | BA-7494 | 진행 중 |
| 3 | [실 동작 테스트](./03-runtime.md) | 요청이 실제로 그렇게 처리되는가 | BA-7489 | 완료 |

1부와 2부는 서버를 띄우지 않고 코드만 읽는다. 2부는 `backend.ai mgr ops list`와
`backend.ai mgr ops entities`의 출력을 RBAC 코드(permission, scope, entity type)와 대조해
검사 로직 자체를 본다. 3부는 살아 있는 매니저에 요청을 보내, 코드만으로는 좁힐 수 없는 해석을
좁힌다. 세 조사 모두 수정은 하지 않는다 — 발견은 각각 별도 이슈로 낸다.

## 1부 결과

기준 커밋 `b2b200c0da`. 정의된 구상 v2 액션 652개, 카탈로그 652행(고유 클래스 651개).

| 항목 | 수 |
|---|---:|
| 조사한 행 | 653 |
| — 실패 | 66 |
| — 성공 | 587 |
| 발견 건수 | 69 |
| 발견이 달린 고유 액션 | 65 |

행보다 발견이 많은 것은 `upsert_artifacts`, `associate_with_storage`,
`disassociate_with_storage` 세 건이 판정을 두 개씩 달기 때문이다.

### 판정별

| 판정 | 분류 | 세부 케이스 | 건수 | 합 |
|---|---|---|---:|---:|
| `W` | 죽은 배선 | 정의됐지만 배선 안 됨 | 1 | **28** |
| | | 배선됐지만 호출 안 됨 | 12 | |
| | | 프로세서 우회 | 3 | |
| | | 도달 불가 owner lookup | 12 | |
| `O` | operation 오선언 | field row 쓰기 | 4 | **21** |
| | | soft delete 역전이 | 1 | |
| | | upsert | 8 | |
| | | v1/v2 불일치 | 8 | |
| `R` | 기록 결함 | 카탈로그 기록 결함 | 4 | **19** |
| | | entity type 불일치 | 6 | |
| | | action_name 자동 변환 | 9 | |
| `G` | 게이트 근거 미흡 | 조건부 시크릿 검사 | 1 | **1** |
| | | **합계** | **69** | **69** |

### concern별

| concern | 실패 | 성공 | 합계 |
|---|---:|---:|---:|
| visibility | 9 | 4 | 13 |
| artifact_registry | 13 | 59 | 72 |
| resource_group | 9 | 68 | 77 |
| deployment | 8 | 77 | 85 |
| vfolder | 8 | 60 | 68 |
| container_registry | 6 | 33 | 39 |
| organization | 6 | 93 | 99 |
| session | 4 | 59 | 63 |
| rbac | 2 | 17 | 19 |
| label | 1 | 4 | 5 |
| app_config | 0 | 21 | 21 |
| metric | 0 | 14 | 14 |
| notification_center | 0 | 13 | 13 |
| resource_policy | 0 | 20 | 20 |
| system | 0 | 45 | 45 |
| **합계** | **66** | **587** | **653** |

## 정정

원 조사 결과에서 두 군데를 고쳤다.

**무인증 라우트 열거.** 인증 미들웨어가 없는 REST 라우트가 GraphiQL 페이지와 public GraphQL
서브그래프 둘뿐이라는 서술은 사실이 아니다. `POST /auth/authorize`, `/auth/signup`,
`/auth/update-password-no-auth`, `/app-config/public/get`,
`/container-registries/webhook/harbor`도 인증 미들웨어를 달지 않는다. 이들이 실어 나르는
액션은 모두 anonymous 게이트이므로 결론은 유지된다 — permission 게이트 액션이 무인증 라우트에
올라간 사례는 없다.

**harbor webhook.** 이상 없음으로 분류돼 있었으나 시크릿 비교가 조건부다. 판정 `G`로 옮겼다.

## 후속 수정 순서

1. `O` — 검사되는 권한이 틀린 것. 실제 접근 제어에 영향이 있다.
2. `W` — 죽은 배선. 지우거나 연결한다.
3. `R` — 카탈로그 신뢰도. 감사 기록을 읽는 쪽에 영향이 있다.

`G`는 2부에서 게이트 규칙 전체를 볼 때 같이 판단한다.

## 2부 중간 결과

1부가 "entity type 불일치 6건"으로 묶은 것이 둘로 갈린다. `scope` kind인 3건은 매칭되는 permission
행이 달라지는 실질적 차이이고, `global` kind인 3건은 SUPERADMIN 게이트에 걸리므로 감사 기록에만
남는다.

권한 저장소가 레거시 enum 타입에 남아 있는 문제는 액션 정의가 아니라 스키마의 문제이므로
BA-7498로 분리했다.

자세한 것은 [2부 문서](./02-permission-logic.md).

## 3부 결과

기준 커밋 `05e005d18b`. 살아 있는 매니저에 실제로 요청을 보내 카탈로그 506행을 실행했다.
`session`(63)과 `deployment`(85)은 범위 밖이다.

### 총계

| 항목 | 수 |
|---|---:|
| 조사한 행 | 506 |
| — 실패 | 39 |
| — 경고 | 227 |
| — 미실행 | 26 |
| — 성공 | 214 |

**실패**는 액션이 제 일을 하지 못하는 것, **경고**는 동작은 하는데 선언·기록이 실제와 다르거나,
정보가 새거나, 의도를 알 수 없는 것이다. 행은 배타적으로 배정된다 — `E-`가 하나라도 붙으면 실패,
없이 `W-`만 붙으면 경고다.

| 대분류 | 판정 | 뜻 | 질문 | 건수 |
|---|---|---|---|---:|
| **실패** | `E-GATE` | 사용자가 자기 자원에 접근하지 못한다 | Q2 | 18 |
| | `E-EXEC` | 도달하지만 어떤 주체·입력으로도 성공하지 않는다 | Q1 | 11 |
| | `E-BULK` | 벌크가 항목별로, 순서대로 답하지 않는다 | Q5 | 11 |
| **경고** | `W-GATE` | superadmin 전용인지 알기 어렵다 | Q2 | 117 |
| | `W-LEAK` | 한 호출자가 없는 자원과 접근 권한이 없는 자원을 구별할 수 있다 | Q4 | 10 |
| | `W-GUARD` | 게이트를 정당화하는 근거가 런타임에 없다 | Q2 | 3 |
| | `W-AUDIT` | 감사 행이 카탈로그와 다르다 | Q3 | 115 |
| | `W-UNREACH` | 배선은 있으나 클라이언트 경로가 없다 | Q1 | 34 |
| **미실행** | `X` | 백엔드 부재 또는 공유 스택 보호 | — | 26 |

한 행이 판정을 둘 이상 달 수 있어 판정별 합은 행 수보다 크다.

**대분류는 동작 기준이지 심각도 순이 아니다.** 살아 있는 정보 노출(`W-LEAK`·`W-GUARD`)은 경고에
있지만 수정 순서에서는 맨 앞이다.

### 3부 concern별

| concern | 실패 | 경고 | 미실행 | 성공 | 합계 |
|---|---:|---:|---:|---:|---:|
| organization | 13 | 51 | 0 | 35 | 99 |
| vfolder | 5 | 21 | 5 | 39 | 70 |
| resource_group | 4 | 27 | 7 | 39 | 77 |
| rbac | 4 | 12 | 0 | 3 | 19 |
| visibility | 4 | 5 | 0 | 4 | 13 |
| container_registry | 3 | 16 | 7 | 13 | 39 |
| artifact_registry | 2 | 43 | 5 | 21 | 71 |
| resource_policy | 2 | 15 | 0 | 3 | 20 |
| app_config | 1 | 6 | 0 | 14 | 21 |
| label | 1 | 3 | 0 | 1 | 5 |
| system | 0 | 14 | 1 | 30 | 45 |
| notification_center | 0 | 10 | 1 | 2 | 13 |
| metric | 0 | 4 | 0 | 10 | 14 |
| **합계** | **39** | **227** | **26** | **214** | **506** |

### 3부 판정 분류에서 정한 것

1부의 `W`/`O`/`R`/`G`는 코드를 읽어 판정하는 체계라 실행 조사에는 맞지 않는다. 3부는 실패와 경고를
가르고, 각 판정이 다섯 질문 중 어디에 대응하는지를 코드에 담는다.

| 규칙 | 근거 |
|---|---|
| 라우트의 superadmin 요구 자체는 결함이 아니다 | `ActionGate`는 `anonymous`·`public`·`permission` 셋뿐이고 superadmin 값이 없다. superadmin 전용은 `kind=global`로만 표현되므로 `single_entity` 액션이 superadmin 전용이면 카탈로그가 적을 방법이 없다. 카탈로그가 틀린 것이 아니라 어휘에 없는 것이라 `성공`으로 둔다 |
| `get_vfolder_v2`는 `성공`이다 | `role_domain_default_member`가 domain 스코프 vfolder READ를 가져 도메인 구성원이 통과한다. 액션이 아니라 역할 프리셋의 범위 문제이고, v1은 소유권을 검사해 모델이 갈린다 |
| `E-GATE`와 `W-GATE`는 발견 내용으로 가른다 | 경로 문자열로는 의도를 알 수 없다. 사용자가 자기 자원에 접근하지 못한다고 실증된 18행만 `E-GATE`이고, 나머지는 라우트가 superadmin을 요구한다는 사실까지만 확인됐다 |
| `W-UNREACH`는 경고다 | API가 없다는 것이지 동작이 깨진 것이 아니다. 1부가 `W`(죽은 배선)로 이미 판정한 것과 같은 대상이다 |
| `W-GUARD`는 1부의 `G`와 같다 | 1부가 `G`로 판정한 harbor webhook이 3부에서도 같은 판정이라, 두 문서를 오가는 독자가 같은 액션에서 같은 결론을 본다 |
| `W-LEAK`은 한 호출자 기준이다 | admin이 404를 받고 비-admin이 403을 받는 것은 게이트가 둘일 뿐 누출이 아니다 |
| `행 없음 (성공 read)`은 `W-AUDIT`가 아니다 | `AuditLogPolicy`는 모든 변경과 모든 실패를 기록하고 성공한 read는 opt-in된 경우만 기록하는데, 이 배포에는 opt-in된 read가 없다 |

마지막 규칙은 기록 문제만이 아니다. 두 슬라이스가 각각 확인 없이 `no row`를 대량으로 단정했다가
되돌렸고, 정정된 그림은 초안과 반대다 — 감사 계측은 대체로 건전하고, 진짜 공백은 라우트 미들웨어
거부와 레거시 GraphQL 우회 둘뿐이다.

`W-GUARD` 3건은 전부 정당화 기전이 존재하는데 작동하지 않는 경우다.

| 액션 | 무엇이 게이트를 정당화하기로 되어 있었나 |
|---|---|
| `signup` | `PRE_SIGNUP` 훅 — 등록돼 있지 않은데 `success_if_no_hook=True`라 무조건 통과한다 |
| `handle_harbor_webhook` | 웹훅 시크릿 비교 — `extra.webhook_auth_header`가 있을 때만 실행되고, 배포의 모든 레지스트리에서 그 필드가 비어 있다 |
| `public_list_shared_vfolders` | 결과를 호출자와 관련된 공유로 한정하는 것 — `list_shared_vfolder_permissions(None)`이 한정하지 않는다 |

`authorize`는 `W-GUARD`가 아니다. `anonymous`가 본질적이라 정당화할 기전이 애초에 없고, 결함은
게이트가 아니라 핸들러가 미존재 계정과 오답 비밀번호를 가르는 것이다(`W-LEAK`).

### 슬라이스 간에 걸친 결함

각각 한 번 고치면 되는 것이고, 서로 다른 슬라이스에서 독립적으로 발견됐다.

| 결함 | 발견 슬라이스 |
|---|---|
| `global` kind 액션이 전부 `entity_type='global'`을 기록한다 — `actions/v2/global_scope/monitor/audit_log.py:73`이 `action.entity_type()` 대신 `GLOBAL_ENTITY_TYPE`을 넘긴다 | 3개 전부 |
| RBAC 거부가 전부 `role_create_forbidden`으로 나온다 — `errors/permission.py:93`이 엔티티·operation과 무관하게 `ErrorDomain.ROLE` + `ErrorOperation.CREATE`를 고정한다 | 3개 전부 |
| 라우트 레벨 `superadmin_required` 거부는 프로세서에 닿지 않아 감사 행이 없다 | 3개 전부 |
| 엔티티 create가 unique 제약을 건드리면 실패한 `INSERT`의 바인딩된 파라미터를 그대로 응답에 실어 보낸다 — `repositories/ops/v2/write_base.py:233`이 선언된 check와 매칭되지 않으면 파싱된 오류를 다시 올린다. 시크릿이 평문으로 나간다 | 신원, 저장소 |
| 감사 로그 읽기 표면 전체가 모든 클라이언트에서 사용 불가 — `client_ip`가 DB에서 `inet`인데 DTO는 `str \| None`이라 `GET /v2/audit-logs`·`adminAuditLogsV2`·`scopedAuditLogsV2`가 함께 죽는다 | 리드 확인, 2개 슬라이스에서 재현 |

### 반복된 형태

같은 모양이 서로 다른 엔티티에서 독립적으로 나왔다.

| 형태 | 사례 |
|---|---|
| v2가 소유자를 호출자가 보낸 scope 필드에서 취하고 호출자로 제약하지 않는다 | `search_app_config_fragments`, `search_users_by_project`·`get_user` |
| 초대 계열이 write-only — 관리자가 만들고 취소하는 것이 전부이고 초대받은 쪽은 읽지도 수락하지도 못한다 | entity invitation, vfolder invitation |
| v1 쌍이 있으면 v2와 권한 모델이 갈린다 | v1은 vfolder 소유권을 검사하고 v2는 도메인 부여로 통과시킨다, v1은 실제로 purge하고 v2는 하지 않는다, 같은 파일 조작이 버전에 따라 다른 권한을 요구한다 |

### 3부에서 실행하지 못한 것

| 대상 | 사유 |
|---|---|
| 저장소 15행 | Harbor 없음, 살아 있는 compute agent 없음, delegatee reservoir 없음 |
| agent 라이프사이클 3행 | 살아 있는 agent도 watcher도 없어 실행하면 공유 스택이 불안정해진다 |
| 나머지 `X` | 요청 모델 검증을 통과시키지 못했거나 발화를 확인하지 못했다 |

`agent`, `proxy-coordinator`, `proxy-worker`는 조사 내내 내려가 있었고 `agents` 테이블에는
`TERMINATED` 한 행만 있었다.

### 3부 후속 수정 순서

심각도 순이지 대분류 순이 아니다.

1. `W-LEAK`·`W-GUARD` (13행) — 살아 있는 정보 노출. 경고로 분류돼 있으나 가장 먼저다.
2. `E-GATE` (18행) — 사용자가 자기 자원을 쓰지 못한다.
3. `E-EXEC` (11행) — 배선은 있는데 아무도 쓸 수 없다.
4. `E-BULK` (11행) — 벌크 응답 계약.

나머지 경고는 그다음이다. `W-GATE` 117행은 **고치기 전에 의도부터 정해야 한다** — 각 라우트의
superadmin 요구가 설계인지 과잉인지 가려야 `E-GATE`로 올릴지 `성공`으로 내릴지가 정해진다.
`W-AUDIT`과 `W-UNREACH`는 1부의 `R`·`W`와 같은 줄에 놓고 함께 처리한다.
