# v2 액션 감사

v2 액션 계층이 선언한 것과 실제로 하는 일이 어긋나는 지점을 찾는 조사. 세 부분으로 나눠서
진행하며, 각 부분이 답할 수 있는 질문이 다르다.

| # | 조사 | 답하는 질문 | Jira | 상태 |
|---|---|---|---|---|
| 1 | [코드 상 wiring 조사](./01-wiring.md) | 배선이 카탈로그·규칙과 맞는가 | BA-7486 | 완료 |
| 2 | [권한 검사 로직 확인](./02-permission-logic.md) | 검사되는 권한 자체가 옳은가 | BA-7494 | 진행 중 |
| 3 | 실 동작 테스트 | 요청이 실제로 그렇게 처리되는가 | BA-7489 | 대기 |

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
