---
name: app-config-definition-adapter-scenarios
type: reference
description: app config definition adapter authorization, search, batch loading, and purge contracts covered by scenario tests
scope: src/ai/backend/manager/api/adapters/app_config_definition
keywords: [app config definition, scenario, adapter, superadmin, cascade]
generated:
  by: codex/gpt-5
  at: 2026-09-14
status: draft
---
# app_config_definition 어댑터의 현재 계약

`app_config_definition` 엔티티에는 사용할 수 있는 `config_name` 값을 등록한다. 실제 설정 값은
`app_config_fragment` 행에, 스코프별 허용 범위는 `app_config_allow_list` 항목에 저장된다.

- `definition` 엔티티는 도메인·프로젝트·사용자 스코프 중 어디에도 자동으로 속하지 않는다.
- 생성과 전체 검색은 호출자가 슈퍼관리자인지 검사한다.
- 개별 조회, 배치 조회, 완전 삭제는 대상 `definition` 엔티티에 대한 권한을 검사한다.
- 현재 기본 역할이 부여되는 스코프와 `definition` 사이에 소유 관계가 없으므로,
  일반 사용자는 개별 엔티티 권한 검사도 통과하지 못한다.

`definition` 하나를 만들 때 RBAC 노드 자체는 생성된다. 따라서 “`definition` 엔티티는 RBAC 엔티티가
아니다”가 아니라 “현재 도메인·프로젝트·사용자 소유 관계에 연결되지 않는다”가 정확한 설명이다.

## 등록은 슈퍼관리자에게만 열려 있다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 새 이름 등록 | 지정한 이름과 서버가 만든 ID·시각 반환 |
| 슈퍼관리자 | 이미 등록된 이름 재등록 | `UniqueConstraintViolationError` |
| 일반 사용자 | 새 이름 등록 | `InsufficientPrivilege` |
| 권한 검사 비활성화, 일반 사용자 | 새 이름 등록 | `InsufficientPrivilege` |

이름이 중복되면 데이터베이스 제약 위반으로 거부된다. 이를 전용 오류로 변환하는 계약은 아직 없다.
빈 이름과 128자를 넘는 이름은 요청 DTO가 거부하므로 어댑터 시나리오에서 다루지 않는다.

## 개별 조회는 엔티티 읽기 권한을 검사한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 존재하는 ID 조회 | `definition` 엔티티의 모든 필드 반환 |
| 권한이 없는 일반 사용자 | 존재하는 ID 조회 | `NotEnoughPermission` |
| 슈퍼관리자 | 존재하지 않는 ID 조회 | `EntityNotFoundError` |
| 권한 검사 비활성화, 일반 사용자 | 존재하는 ID 조회 | `definition` 엔티티의 모든 필드 반환 |

권한 검사가 데이터 조회보다 먼저 실행된다. 따라서 권한이 없는 사용자가 존재하지 않는 ID를
요청하면, 대상을 찾을 수 없어 거부되는 것이 아니라 권한 부족으로 거부된다.

## 배치 조회는 입력 위치마다 결과를 반환한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 존재하는 ID 둘과 없는 ID 하나 | 두 노드와 `None`을 입력 순서대로 반환 |
| 슈퍼관리자 | 같은 ID 두 번 | 같은 노드를 두 위치에 반환 |
| 권한이 없는 일반 사용자 | 존재하는 ID 둘과 없는 ID 하나 | 각 위치에 `NotEnoughPermission` 반환 |
| 일반 사용자 | 빈 목록 | 빈 목록 반환 |

한 ID가 권한 검사에 실패해도 배치 전체가 중단되지는 않는다. 존재하지 않는 ID 위치에 `None`이
반환되는지 권한 부족으로 거부되는지는 그 ID의 권한 검사를 먼저 통과했는지에 따라 달라진다.

## 전체 검색은 슈퍼관리자에게만 열려 있다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 필터 없음 | 모든 `definition` 엔티티와 전체 개수 반환 |
| 일반 사용자 | 검색 | `InsufficientPrivilege` |

필터·정렬·페이지네이션은 검색 공통 계약이므로 이 어댑터의 시나리오로는 검증하지 않는다.

## 완전 삭제는 `definition` 행과 RBAC 노드를 제거한다

| 상황 | 요청 | 결과 |
|---|---|---|
| 슈퍼관리자 | 종속 행이 없는 `definition` 완전 삭제 | 삭제한 `definition` 행의 ID 반환 |
| 슈퍼관리자 | `allow_list` 항목과 `fragment` 행이 있는 `definition` 완전 삭제 | 종속 행이 있어도 거부되지 않고 `definition` 행의 ID 반환 |
| 권한이 없는 일반 사용자 | `definition` 완전 삭제 | `NotEnoughPermission` |
| 슈퍼관리자 | 존재하지 않는 ID 완전 삭제 | `EntityNotFoundError` |

`definition` 행을 삭제하면 외래 키 연쇄 삭제로 같은 이름의 `allow_list` 항목과 `fragment` 행도
삭제된다. `definition` 자체의 RBAC 노드는 완전 삭제 과정에서 함께 삭제된다. soft delete와 복원
호출은 없다.

현재 완전 삭제 과정은 데이터베이스가 연쇄 삭제한 `allow_list` 항목과 `fragment` 행의 RBAC 노드까지는
삭제하지 않는다. 남은 RBAC 노드는 보장할 동작이 아니라 별도 수정이 필요한 한계다. 시나리오는
어댑터 응답을 검증하며, 연쇄 삭제된 행과 남은 RBAC 노드는 직접 조회하지 않는다.

## 여럿 완전 삭제하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 ID 하나를 한 번에 완전 삭제한다 | `definition` 둘 | 셋 완전 삭제 | 둘은 처리된 목록에 오고, 없는 ID는 대상 없음 이유로 실패 목록에 옴 |
| 권한이 없는 일반 사용자가 여럿을 완전 삭제한다 | 같은 `definition` 둘 | 둘 완전 삭제 | 삭제된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 `definition`은 처리된 목록에, 처리하지 못한 것은 ID와
이유를 실패 목록에 싣는다. 여럿 완전 삭제는 `definition`마다 `allow_list` 항목과 `fragment` 행을 먼저
지우고 각자의 savepoint 안에서 처리한다.

## 이름

단건 완전 삭제는 `purge`이고 엔티티 권한 검사만 한다. 옛 `admin_purge` GQL mutation은 deprecated이고,
같은 호출로 이어지되 슈퍼관리자 검사를 그대로 둔다. REST `DELETE /v2/app-config-definitions/{id}`는
경로가 같아 새 이름의 동작으로 바뀌었다.

병합된 설정 조회 계약은 [app_config 어댑터](../app_config/KNOWLEDGE.md)가 다룬다.
