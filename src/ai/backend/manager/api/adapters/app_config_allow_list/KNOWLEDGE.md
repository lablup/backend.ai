---
name: app-config-allow-list-adapter-scenarios
type: reference
description: app config allow-list adapter authorization, rank, search, batch loading, and purge contracts covered by scenario tests
scope: src/ai/backend/manager/api/adapters/app_config_allow_list
keywords: [app config allow list, scenario, adapter, rank, superadmin, cascade]
generated:
  by: codex/gpt-5
  at: 2026-09-14
status: draft
---
# app_config_allow_list 어댑터의 현재 계약

`app_config_allow_list` 항목은 등록된 `config_name` 값을 특정 `scope_type` 값의 스코프에서 사용할 수 있게 한다.
각 `allow_list` 항목의 `rank` 값은 여러 스코프의 `app_config_fragment` 행을 병합할 때 적용할
우선순위를 정한다.

- `allow_list` 항목은 도메인·프로젝트·사용자 스코프에 자동으로 연결되지 않는다.
- 생성과 전체 검색에는 슈퍼관리자 검사가 적용된다.
- 개별 조회, 배치 조회, 수정, 완전 삭제에는 `allow_list` 엔티티에 대한 권한 검사가 적용된다.
- 현재 기본 역할이 부여되는 스코프와 `allow_list` 항목 사이에 소유 관계가 없으므로,
  일반 사용자는 개별 엔티티 권한 검사도 통과하지 못한다.

`allow_list` 항목을 만들 때 RBAC 노드 자체는 생성된다. 즉 `allow_list` 항목은 RBAC 엔티티이지만,
현재 도메인·프로젝트·사용자 소유 관계에는 연결되지 않는다.

`rank` 컬럼은 `fragment` 행이 아니라 `allow_list` 행에 있다. `fragment` 행을 작성할 수 있는
사용자도 자기 `fragment` 행의 `rank` 값은 바꿀 수 없다. 실제 병합 계약은
[app_config 어댑터](../app_config/KNOWLEDGE.md)가 다룬다.

## 생성은 슈퍼관리자만 할 수 있다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | `rank` 값을 생략하고 `scope_type`이 `public`인 `allow_list` 항목 생성 | `rank` 값 100 |
| 슈퍼관리자 | `rank` 값을 생략하고 `scope_type`이 `domain`인 `allow_list` 항목 생성 | `rank` 값 200 |
| 슈퍼관리자 | `rank` 값을 생략하고 `scope_type`이 `user`인 `allow_list` 항목 생성 | `rank` 값 300 |
| 슈퍼관리자 | `rank` 값 250을 지정해 `scope_type`이 `domain`인 `allow_list` 항목 생성 | `rank` 값 250 |
| 슈퍼관리자 | 등록되지 않은 `config_name` 값을 지정해 생성 | `AppConfigDefinitionNotFound` |
| 슈퍼관리자 | 같은 `config_name`과 `scope_type` 값으로 다시 생성 | `UniqueConstraintViolationError` |
| 일반 사용자 | `allow_list` 항목 생성 | `InsufficientPrivilege` |
| 권한 검사 비활성화, 일반 사용자 | `allow_list` 항목 생성 | `InsufficientPrivilege` |

`rank` 값을 생략하면 `scope_type` 값별 기본값을 사용한다. 100 단위의 간격은 슈퍼관리자가 기존
기본값 사이에 별도 `rank` 값을 지정할 수 있게 한다.

등록되지 않은 `config_name` 값을 지정하면 전용 오류로 변환되어 거부된다. 중복 `allow_list` 항목은
아직 전용 오류로 변환되지 않아 데이터베이스 제약 위반으로 거부된다.

## 개별 조회는 엔티티 읽기 권한을 검사한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 존재하는 ID 조회 | `allow_list` 항목의 모든 필드 반환 |
| 권한이 없는 일반 사용자 | 존재하는 ID 조회 | `NotEnoughPermission` |
| 슈퍼관리자 | 존재하지 않는 ID 조회 | `EntityNotFoundError` |
| 권한 검사 비활성화, 일반 사용자 | 존재하는 ID 조회 | `allow_list` 항목의 모든 필드 반환 |

권한 검사가 데이터 조회보다 먼저 실행된다. 따라서 권한이 없는 사용자가 존재하지 않는 ID를
요청하면 대상을 찾을 수 없어 거부되는 것이 아니라 권한 부족으로 거부된다.

## 배치 조회는 입력 위치마다 결과를 반환한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 존재하는 ID 2개와 존재하지 않는 ID 1개 | 존재하는 ID는 노드로, 존재하지 않는 ID는 `None`으로 입력 순서대로 반환 |
| 슈퍼관리자 | 같은 ID를 2회 지정 | 같은 노드를 각 위치에 반환 |
| 권한이 없는 일반 사용자 | 존재하는 ID 2개와 존재하지 않는 ID 1개 | 각 위치에 `NotEnoughPermission` 반환 |
| 일반 사용자 | 빈 목록 | 빈 목록 반환 |

ID 하나의 권한 검사 실패가 배치 전체를 중단하지는 않는다. 존재하지 않는 ID에 `None`이
반환되는지 권한 부족으로 거부되는지는 그 ID에 대한 권한 검사를 먼저 통과했는지에 따라 달라진다.

## 전체 검색은 슈퍼관리자만 할 수 있다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 필터 없음 | 모든 `allow_list` 항목과 전체 개수 반환 |
| 슈퍼관리자 | 생성 시각이 모두 같은 항목들에서, 첫 항목을 가리키는 커서 뒤로 1건 | 바로 다음 항목 1건과 앞뒤 페이지 있음 반환 |
| 일반 사용자 | 검색 | `InsufficientPrivilege` |

한 요청으로 심긴 항목은 생성 시각이 모두 같다. 기본 순서는 생성 시각 내림차순이고, 같은 값은
ID 오름차순으로 끊으므로 커서 다음 페이지가 같은 항목을 다시 내놓거나 건너뛰지 않는다.

필터와 정렬은 검색 공통 계약이라 이 어댑터의 시나리오로 검증하지 않는다.

## 수정할 수 있는 필드는 `rank` 하나뿐이다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 새 `rank` 값 지정 | `rank` 값만 변경된 `allow_list` 항목 반환 |
| 슈퍼관리자 | 빈 수정 요청 | 변경되지 않은 `allow_list` 항목 반환 |
| 권한이 없는 일반 사용자 | `rank` 값 수정 | `NotEnoughPermission` |
| 슈퍼관리자 | 존재하지 않는 ID 수정 | `EntityNotFoundError` |

`config_name`과 `scope_type` 필드는 수정 요청 DTO에 없다. 이 두 필드를 바꾸려면 기존
`allow_list` 항목을 삭제하고 새 `allow_list` 항목을 생성해야 한다.

## 완전 삭제는 `allow_list` 행과 RBAC 노드를 제거한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | `fragment` 행이 없는 `allow_list` 항목 완전 삭제 | 삭제한 `allow_list` 항목의 ID 반환 |
| 슈퍼관리자 | `fragment` 행이 있는 `allow_list` 항목 완전 삭제 | `fragment` 행이 있어도 삭제되고 `allow_list` 항목의 ID 반환 |
| 권한이 없는 일반 사용자 | `allow_list` 항목 완전 삭제 | `NotEnoughPermission` |
| 슈퍼관리자 | 존재하지 않는 ID 완전 삭제 | `EntityNotFoundError` |

`allow_list` 행을 삭제하면 그 행을 참조하는 `fragment` 행도 외래 키 연쇄 삭제로 함께 삭제된다.
`allow_list` 항목 자체의 RBAC 노드는 완전 삭제 과정에서 함께 삭제된다. soft delete와 복원 호출은
없다.

현재 완전 삭제 과정은 데이터베이스가 연쇄 삭제한 `fragment` 행의 RBAC 노드까지는 삭제하지
않는다. 이렇게 남는 노드는 보장하는 동작이 아니라 별도 수정이 필요한 한계다. 시나리오는 어댑터
응답을 검증하며, 연쇄 삭제된 행과 남은 RBAC 노드는 직접 조회하지 않는다.
