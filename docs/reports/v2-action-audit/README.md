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
| — 실패 | 325 |
| — 성공 | 181 |

| 판정 | 뜻 | 질문 | 건수 |
|---|---|---|---:|
| `U` | 도달 불가 | Q1 | 34 |
| `E` | 실행 불능 | Q1 | 11 |
| `P` | 게이트 불일치 | Q2 | 168 |
| `G` | 게이트 근거 미흡 | Q2 | 3 |
| `A` | 감사 기록 불일치 | Q3 | 118 |
| `L` | 구분 누출 | Q4 | 11 |
| `B` | 벌크 응답 결함 | Q5 | 11 |
| `X` | 미실행 | — | 26 |

한 행이 판정을 둘 이상 달 수 있어 판정별 합은 행 수보다 크다.

### concern별

| concern | 실패 | 성공 | 합계 |
|---|---:|---:|---:|
| organization | 67 | 32 | 99 |
| resource_group | 53 | 24 | 77 |
| artifact_registry | 50 | 21 | 71 |
| vfolder | 32 | 38 | 70 |
| container_registry | 28 | 11 | 39 |
| resource_policy | 17 | 3 | 20 |
| system | 17 | 28 | 45 |
| rbac | 16 | 3 | 19 |
| app_config | 12 | 9 | 21 |
| notification_center | 11 | 2 | 13 |
| visibility | 11 | 2 | 13 |
| metric | 7 | 7 | 14 |
| label | 4 | 1 | 5 |
| **합계** | **325** | **181** | **506** |

### 판정 코드

1부의 `W`/`O`/`R`/`G`는 코드를 읽어 판정하는 체계라 실행 조사에는 맞지 않는다. 3부는 다섯 질문에
그대로 대응하는 코드를 쓴다.

| 판정 | 뜻 | 질문 |
|---|---|---|
| `U` | 도달 불가 — 클라이언트 경로가 없다 | Q1 |
| `E` | 실행 불능 — 경로는 있으나 어떤 주체·입력으로도 성공하지 않는다 | Q1 |
| `P` | 게이트 불일치 — 선언된 게이트가 요청이 만나는 게이트와 다르다 | Q2 |
| `G` | 게이트 근거 미흡 — 게이트는 선언대로 만나지만 그 게이트를 정당화하는 근거가 런타임에 성립하지 않는다 | Q2 |
| `A` | 감사 기록 불일치 | Q3 |
| `L` | 구분 누출 — 한 호출자가 없는 것과 거부된 것을 가를 수 있다 | Q4 |
| `B` | 벌크 응답 결함 | Q5 |
| `X` | 미실행 — 백엔드 부재 또는 공유 스택 보호 | — |

`G`만 1부에서 글자를 그대로 가져왔다. 1부가 `G`로 판정한 harbor webhook이 3부에서도 `G`라서,
두 문서를 오가는 독자가 같은 액션에서 같은 판정을 본다. `P`는 "선언과 다른 게이트를 만난다"이고
`G`는 "선언대로 만나는데 그 선언이 안전하지 않다"이다.

3부의 `G` 3건은 전부 정당화 기전이 존재하는데 작동하지 않는 경우다.

| 액션 | 무엇이 게이트를 정당화하기로 되어 있었나 |
|---|---|
| `signup` | `PRE_SIGNUP` 훅 — 등록돼 있지 않은데 `success_if_no_hook=True`라 무조건 통과한다 |
| `handle_harbor_webhook` | 웹훅 시크릿 비교 — `extra.webhook_auth_header`가 있을 때만 실행되고, 배포의 모든 레지스트리에서 그 필드가 비어 있다 |
| `public_list_shared_vfolders` | 결과를 호출자와 관련된 공유로 한정하는 것 — `list_shared_vfolder_permissions(None)`이 한정하지 않는다 |

`authorize`는 `G`가 아니다. `anonymous`가 본질적이라 정당화할 기전이 애초에 없고, 결함은 게이트가
아니라 핸들러가 미존재 계정과 오답 비밀번호를 가르는 것이다(`L`).

### 판정 경계에서 정한 것

세 슬라이스를 병렬로 돌리면서 같은 사실을 다르게 세는 일이 생겨 세 군데를 통일했다.

**`global`/`permission`의 superadmin 게이트는 `P`가 아니다.** 2부 A절이 확정한 대로 `GlobalActionProcessor`가
`SuperAdminActionValidator`를 고정하므로, 그 행에서 비-admin이 403을 받는 것은 선언된 게이트가
그대로 작동한 것이다. `P`는 `single_entity`/`scope`/`bulk` + `permission`인데 라우트가 먼저
superadmin을 요구해 RBAC가 판단하지 못하는 경우와, RBAC 부여가 operation보다 넓은 경우에만 붙인다.

**`U`와 `E`를 나눈다.** 경로가 없는 것과, 도달은 하지만 항상 실패하는 것은 Q1에 대한 답이 다르고
수정 방향도 다르다 — `U`는 배선하거나 지우고, `E`는 결함을 고친다.

**`L`은 한 호출자 기준이다.** admin이 404를 받고 비-admin이 403을 받는 것은 게이트가 둘일 뿐
누출이 아니다. 누출은 한 호출자가 없는 엔티티와 거부된 엔티티에 대해 구분되는 답을 받는 것이다.

**`행 없음 (성공 read)`은 `A`가 아니다.** `AuditLogPolicy`는 모든 변경과 모든 실패를 기록하고
성공한 read는 opt-in된 경우만 기록하는데, 이 배포에는 opt-in된 read가 없다.

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

같은 모양이 서로 다른 엔티티에서 독립적으로 나왔다. 개별 버그가 아니라 계층의 성질로 봐야 한다.

| 형태 | 사례 |
|---|---|
| v2가 소유자를 호출자가 보낸 scope 필드에서 취하고 호출자로 제약하지 않는다 | `search_app_config_fragments`, `get_vfolder_v2`, `search_users_by_project`·`get_user` |
| 초대 계열이 write-only — 관리자가 만들고 취소하는 것이 전부이고 초대받은 쪽은 읽지도 수락하지도 못한다 | entity invitation, vfolder invitation |
| v1 쌍이 있으면 v2가 더 약한 표면이다 | v1은 소유권을 검사하고 v2는 떨어뜨렸다, v1은 실제로 purge하고 v2는 하지 않는다, 같은 파일 조작이 버전에 따라 다른 권한을 요구한다 |

### 실행하지 못한 것

| 대상 | 사유 |
|---|---|
| 저장소 15행 | Harbor 없음, 살아 있는 compute agent 없음, delegatee reservoir 없음 |
| agent 라이프사이클 3행 | 살아 있는 agent도 watcher도 없어 실행하면 공유 스택이 불안정해진다 |
| 나머지 `X` | 요청 모델 검증을 통과시키지 못했거나 발화를 확인하지 못했다 |

`agent`, `proxy-coordinator`, `proxy-worker`는 조사 내내 내려가 있었고 `agents` 테이블에는
`TERMINATED` 한 행만 있었다.

### 후속 수정 순서

1. `L`과 소유자 미제약 — 살아 있는 정보 노출이다.
2. `P` — 검사되는 게이트가 선언과 다르다. 실제 접근 제어에 영향이 있다.
3. `E` — 배선은 있는데 아무도 쓸 수 없다.
4. `B` — 벌크 응답 계약.
5. `A`와 `U` — 감사 신뢰도와 죽은 배선. 1부의 `R`·`W`와 같은 줄에 놓고 함께 처리한다.
