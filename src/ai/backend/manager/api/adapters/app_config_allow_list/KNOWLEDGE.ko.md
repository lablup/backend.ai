# app_config_allow_list adapter: 현재 계약

`app_config_allow_list` 항목은 등록된 `config_name` 값을 특정 `scope_type` 값의 스코프에서 사용할 수 있게 한다. 각 `allow_list` 항목의 `rank` 값은 여러 스코프의 `app_config_fragment` row 를 병합할 때 적용할 우선순위를 정한다.

- `allow_list` 항목은 도메인, 프로젝트, 사용자 스코프에 자동으로 연결되지 않는다.
- 생성과 스코프 없는 검색에는 superadmin 검사가 적용된다.
- 개별 조회, batch 조회, 수정, 영구 삭제에는 `allow_list` 엔티티에 대한 권한 검사가 적용된다.
- 기본 역할이 부여되는 스코프는 `allow_list` 항목을 own 하지 않으므로, 일반 사용자는 개별 엔티티 권한 검사도 통과하지 못한다.

`allow_list` 항목을 생성할 때 RBAC 노드도 생성된다. 항목은 RBAC 엔티티이지만 현재 도메인, 프로젝트, 사용자가 own 하지 않는다.

`rank` column 은 `fragment` row 가 아니라 `allow_list` row 에 있다. `fragment` row 를 작성할 수 있는 사용자도 그 row 의 `rank` 값은 변경할 수 없다. 실제 병합 계약은 [app_config adapter](../app_config/KNOWLEDGE.md) 가 다룬다.

## 생성은 superadmin 만 할 수 있다

`rank` 값을 생략하면 `scope_type` 값별 기본값을 사용한다. 100 단위 간격은 superadmin 이 기존 기본값 사이에 별도 `rank` 값을 지정할 수 있게 한다.

등록되지 않은 `config_name` 값을 지정하면 전용 에러로 변환되어 거부된다. 중복 `allow_list` 항목은 아직 전용 에러로 변환되지 않아 데이터베이스 제약 위반으로 거부된다.

## 개별 조회는 엔티티 읽기 권한을 검사한다

권한 검사가 데이터 조회보다 먼저 실행된다. 따라서 권한이 없는 사용자가 존재하지 않는 ID 를 요청하면 대상을 찾을 수 없어 거부되는 것이 아니라 권한 부족으로 거부된다.

## batch 조회는 입력 위치마다 결과를 반환한다

ID 하나의 권한 검사 실패가 batch 전체를 중단하지 않는다. 존재하지 않는 ID 에 `None` 이 반환되는지 권한 부족으로 거부되는지는 그 ID 에 대한 권한 검사를 먼저 통과했는지에 따라 달라진다.

## 스코프 없는 검색은 superadmin 만 할 수 있다

한 요청으로 미리 저장한 항목은 생성 시각이 모두 같다. 기본 순서는 생성 시각 내림차순이고 같은 값은 ID 오름차순으로 끊으므로, 커서 다음 페이지가 같은 항목을 다시 반환하거나 건너뛰지 않는다.

필터와 정렬은 검색 공통 계약이라 이 adapter 의 시나리오로 검증하지 않는다.

## 수정할 수 있는 필드는 `rank` 하나뿐이다

`config_name` 과 `scope_type` 필드는 수정 요청 DTO 에 없다. 이 두 필드를 변경하려면 기존 `allow_list` 항목을 삭제하고 새 `allow_list` 항목을 생성해야 한다.

## 여럿 수정하기

## 영구 삭제는 `allow_list` row 와 RBAC 노드를 제거한다

`allow_list` row 를 삭제하면 그 row 를 참조하는 `fragment` row 도 외래 키 연쇄 삭제로 함께 삭제된다. 항목 자체의 RBAC 노드는 영구 삭제 과정에서 함께 삭제된다. 삭제와 복원 호출은 없다.

현재 영구 삭제 과정은 데이터베이스가 연쇄 삭제한 `fragment` row 의 RBAC 노드까지는 삭제하지 않는다. 이렇게 남는 노드는 보장하는 동작이 아니라 별도 수정이 필요한 한계다. 시나리오는 adapter 응답을 검증하며, 연쇄 삭제된 row 와 남은 RBAC 노드는 직접 조회하지 않는다.

## 여럿 영구 삭제하기

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 항목은 처리된 목록에, 처리하지 못한 항목은 ID 와 이유를 실패 목록에 담는다. 여럿 영구 삭제는 항목마다 `fragment` row 를 먼저 삭제하고 각자의 savepoint 안에서 처리한다.

## 이름

단건 수정과 영구 삭제는 `update`, `purge` 이고 엔티티 권한 검사만 한다. 옛 `admin_update`, `admin_purge` GQL mutation 과 단수 경로(`/v2/app-config-allow-list`)의 REST 수정, 영구 삭제는 deprecated 이며, 같은 호출로 이어지되 superadmin 검사를 그대로 둔다. 새 쓰기 경로는 `/v2/app-config-allow-lists` 아래에 있다.
