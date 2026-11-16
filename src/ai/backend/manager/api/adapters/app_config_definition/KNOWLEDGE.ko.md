# app_config_definition adapter: 현재 계약

`app_config_definition` 엔티티에는 사용할 수 있는 `config_name` 값을 등록한다. 실제 설정 값은 `app_config_fragment` row 에, 스코프별 허용 범위는 `app_config_allow_list` 항목에 저장된다.

- `definition` 엔티티는 도메인, 프로젝트, 사용자 스코프 중 어디에도 자동으로 속하지 않는다.
- 생성과 스코프 없는 검색은 호출자가 superadmin 인지 검사한다.
- 개별 조회, batch 조회, 영구 삭제는 대상 `definition` 엔티티에 대한 권한을 검사한다.
- 현재 기본 역할이 부여되는 스코프는 `definition` 을 own 하지 않으므로, 일반 사용자는 개별 엔티티 권한 검사도 통과하지 못한다.

`definition` 하나를 생성할 때 RBAC 노드 자체는 생성된다. 따라서 정확한 설명은 "`definition` 엔티티는 RBAC 엔티티가 아니다"가 아니라 "현재 도메인, 프로젝트, 사용자 소유 관계에 연결되지 않는다"이다.

## 등록은 superadmin 에게만 허용된다

이름이 중복되면 데이터베이스 제약 위반으로 거부된다. 이를 전용 에러로 변환하는 계약은 아직 없다. 빈 이름과 128자를 넘는 이름은 요청 DTO 가 거부하므로 adapter 시나리오에서 다루지 않는다.

## 개별 조회는 엔티티 읽기 권한을 검사한다

권한 검사가 데이터 조회보다 먼저 실행된다. 따라서 권한이 없는 사용자가 존재하지 않는 ID 를 요청하면 대상을 찾을 수 없어 거부되는 것이 아니라 권한 부족으로 거부된다.

## batch 조회는 입력 위치마다 결과를 반환한다

한 ID 가 권한 검사에 실패해도 batch 전체가 중단되지 않는다. 존재하지 않는 ID 위치에 `None` 이 반환되는지 권한 부족으로 거부되는지는 그 ID 의 권한 검사를 먼저 통과했는지에 따라 달라진다.

## 스코프 없는 검색은 superadmin 에게만 허용된다

필터, 정렬, 페이지네이션은 검색 공통 계약이므로 이 adapter 의 시나리오로 검증하지 않는다.

## 영구 삭제는 `definition` row 와 RBAC 노드를 삭제한다

`definition` row 를 삭제하면 외래 키 연쇄 삭제로 같은 이름의 `allow_list` 항목과 `fragment` row 도 삭제된다. `definition` 자체의 RBAC 노드는 영구 삭제 과정에서 함께 삭제된다. soft delete 와 복원 호출은 없다.

현재 영구 삭제 과정은 데이터베이스가 연쇄 삭제한 `allow_list` 항목과 `fragment` row 의 RBAC 노드까지는 삭제하지 않는다. 남은 RBAC 노드는 보장할 동작이 아니라 별도 수정이 필요한 한계다. 시나리오는 adapter 응답을 검증하며, 연쇄 삭제된 row 와 남은 RBAC 노드는 직접 조회하지 않는다.

## 여럿 영구 삭제하기

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 `definition` 은 처리된 목록에, 처리하지 못한 항목은 ID 와 이유를 실패 목록에 담는다. 여럿 영구 삭제는 `definition` 마다 `allow_list` 항목과 `fragment` row 를 먼저 삭제하고 각자의 savepoint 안에서 처리한다.

## 이름

단건 영구 삭제는 `purge` 이고 엔티티 권한 검사만 한다. 옛 `admin_purge` GQL mutation 은 deprecated 이며, 같은 호출로 이어지되 superadmin 검사를 그대로 둔다. REST `DELETE /v2/app-config-definitions/{id}` 는 경로가 같고 새 이름의 동작으로 바뀌었다.

병합된 설정 조회 계약은 [app_config adapter](../app_config/KNOWLEDGE.md) 가 다룬다.
