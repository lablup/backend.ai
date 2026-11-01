---
name: container-registry-adapter-scenarios
type: reference
description: container registry adapter guarantees; superadmin-gated management calls, per-id batch load, missing scoped search, RBAC project relations, linking a project as its default, legacy is_global image visibility, update-only URL validation
scope: src/ai/backend/manager/api/adapters/container_registry
keywords: [container registry, scenario, adapter, superadmin, scoped_search, operation scope, RBAC, allowed groups, is_global, image visibility]
sources:
  - src/ai/backend/manager/api/adapters/container_registry/adapter.py
  - src/ai/backend/manager/services/container_registry/actions/base.py
  - src/ai/backend/manager/services/container_registry/processors.py
  - src/ai/backend/manager/models/container_registry/creators.py
  - src/ai/backend/manager/models/image/creators.py
  - src/ai/backend/manager/models/image/row.py
  - src/ai/backend/manager/repositories/ops/v2/relation/write.py
  - src/ai/backend/manager/api/adapters/image/adapter.py
  - src/ai/backend/manager/api/gql/image/resolver.py
  - tests/scenario/bai_scenario/manager/container_registry
generated:
  by: codex/gpt-5
  at: 2026-09-14
updated:
  by: claude-code/opus-5.5
  at: 2026-10-30
status: draft
---
# container_registry 어댑터 — 시나리오

이 패키지는 `container_registry` API 요청을 레지스트리 및 RBAC 프로세서 호출로 변환한다. 아래
시나리오는 어댑터가 보장하는 권한 검사, 반환값, 오류를 정리한다.

## 대부분의 호출은 슈퍼관리자만 실행할 수 있다

- 각 레지스트리는 상위 스코프에 소유되지 않는 RBAC 엔티티로 생성된다.
- 허용 프로젝트 변경, 여러 ID 조회, 여럿 purge 를 제외한 생성·검색·수정·purge 호출은 global
  action으로 처리되며, 엔티티별 RBAC 권한이 아니라 슈퍼관리자 여부로 접근을 제어한다.
- 허용 프로젝트 추가와 제거는 RBAC 관계 작업을 사용하므로 레지스트리와 프로젝트 양쪽의 권한을
  검사하며, 엔티티 권한 검사 설정의 영향을 받는다.
- 여러 ID 조회와 여럿 purge 는 ID마다 엔티티 권한을 검사하고 결과를 ID별로 반환한다.

## 프로젝트 관계는 권한 그래프에 기록되지만 검색에는 아직 쓰이지 않는다

- 허용 프로젝트를 추가하면 프로젝트가 레지스트리를 `READ` 권한으로 관할하며, 이 권한은
  레지스트리가 소유한 이미지에도 적용된다.
- 레지스트리 검색은 슈퍼관리자용 `admin_search`만 제공하며, 프로젝트 관계를 조건으로 변환하는
  operation scope와 `scoped_search`는 아직 없다.
- 따라서 새 RBAC 그래프에 관계가 있어도 일반 사용자가 접근 가능한 레지스트리나 이미지를 이
  어댑터의 검색 호출로 열거할 수는 없다.

## `is_global` 이미지 공개 정책은 레거시 조회에 남아 있다

- 모든 레지스트리는 상위 소유 스코프 없이 생성되므로 `is_global` 값은 RBAC 소유 관계를 바꾸지
  않으며, 값을 수정해도 기존 프로젝트 관계를 유지한다.
- 레거시 이미지 권한 빌더는 `is_global`인 레지스트리의 이미지를 프로젝트 관계 없이 포함하고,
  `is_global`이 아닌 레지스트리의 이미지는 허용 관계가 있는 프로젝트에만 포함한다.
- 새 관계 그래프는 명시적으로 연결한 프로젝트에 레지스트리와 그 이미지의 읽기 권한을 부여하지만,
  `is_global` 값만으로 모든 프로젝트에 권한을 부여하지는 않는다.
- 이미지 어댑터에는 이 정책을 적용하는 scoped search가 없으므로, 레거시 빌더를 제거하기 전에
  `is_global`인 레지스트리의 이미지 공개 규칙과 목록·단건 조회에 공통으로 적용할 operation
  scope를 정해야 한다.

## 이미지 scoped search는 레거시 접근 조건을 함께 이전해야 한다

- 프로젝트별 이미지 조건은 `is_global`인 레지스트리의 이미지와, `is_global`이 아니면서 프로젝트와
  관계가 있는 레지스트리의 이미지를 선택하고, 호출자 도메인의 `allowed_docker_registries`도
  적용해야 한다.
- customized 이미지는 기존 조회와 동일하게 `creator_id` 컬럼이 가리키는 사용자에게만 노출하거나,
  새 프로젝트 소유권 정책으로 대체한 뒤 목록 조회와 단건 조회가 같은 결과를 내도록 해야 한다.
- 기존 레지스트리·이미지의 권한 그래프를 backfill하지 않으면 새 scoped search가 이전 데이터에
  대한 접근 권한을 찾을 수 없다.

## 생성 시 기본값과 허용 프로젝트 관계를 함께 처리한다

- `url` 값이나 이름이 공백으로만 이루어진 요청은 요청 타입에서 거부하므로 어댑터 시나리오에
  포함하지 않는다.
- `ssl_verify` 값과 `is_global` 값을 생략해도 둘 다 true가 된다.
- 허용 프로젝트를 포함한 생성도 슈퍼관리자 전용이며, 새 레지스트리에 대한 권한을 미리 부여할
  필요는 없다.

## 검색은 슈퍼관리자만 실행하며 레지스트리 고유 필드로 필터링한다

필터 결합(`AND`/`OR`/`NOT`), 정렬, 커서·오프셋 페이지네이션은 모든 엔티티가 공유하는 검색
프레임워크의 동작이므로 이 어댑터의 시나리오에 포함하지 않는다.

## 여러 ID를 요청 순서대로 ID별로 반환한다

- 여러 ID 조회는 ID마다 읽기 권한을 검사한다. 권한이 없는 ID는 권한 부족으로 거부하고, 존재하지
  않는 ID는 거부와 구분되는 빈 값으로 반환하도록 설계되어 있다.
- 권한 검사가 존재 여부보다 먼저 이뤄지므로, 권한이 없는 사용자에게는 존재하지 않는 ID도 권한
  부족으로 거부된다. 대상이 있는지 없는지는 드러나지 않는다.
- ID별 권한 검사는 슈퍼관리자를 먼저 통과시키지 않는다. 슈퍼관리자도 권한 그래프로 판정하므로
  노드가 없는 ID는 빈 값이 아니라 권한 부족으로 거부된다. 단건 조회의 권한 검사는 슈퍼관리자를
  먼저 통과시키므로 두 검사의 결과가 다르며, 어느 쪽으로 맞출지는 아직 결정되지 않았다.

## 수정 후 레지스트리의 `url` 값과 `type` 값을 검증한다

- `url` 검증은 호스트가 있는지만 확인하며 스킴은 제한하지 않는다.
- `http` 또는 `https`로 시작하지 않는 `url` 값에는 `http://`를 붙인 뒤 파싱한다. 따라서
  `ftp://reg.example`이나 공백이 포함된 문자열도 통과하며, 호스트가 비어 있는 `url` 값만 거부된다.
- 이 검증 범위를 강화할지는 아직 결정되지 않았다.
- 검증은 수정 후의 최종 값을 대상으로 한다. 요청에서 `url` 값이나 `project` 값을 생략하더라도
  저장된 값이 규칙을 위반하면 수정 요청을 거부한다.

## 허용 프로젝트 변경은 레지스트리와 프로젝트 양쪽 스코프의 권한을 검사한다

- 관계 작업은 레지스트리와 프로젝트를 한 쌍으로 묶어 권한을 검사하며, 둘 중 하나라도 허용되지 않으면
  요청 전체를 거부한다.
- 일반 사용자는 관계 상태를 확인하기 전에 권한 검사에서 거부된다. 따라서 존재하지 않는 프로젝트를
  추가하는 시나리오와 허용되지 않은 프로젝트를 제거하는 시나리오는 슈퍼관리자로 실행한다.
- 엔티티 권한 검사를 비활성화하면 권한이 없는 사용자도 관계를 변경할 수 있다. 생성 작업은
  슈퍼관리자 여부를 직접 확인하므로 결과가 다르다.
- 이미 존재하는 관계를 다시 추가하는 작업은 멱등하다. 제거 요청에 포함된 관계가 하나도 삭제되지
  않았을 때만 오류가 발생한다.
- 추가는 양쪽 스코프의 생성 권한을, 제거는 양쪽 스코프의 삭제 권한을 요구한다. 다른 종류의 권한으로
  대신할 수 없다.
- 관계 변경 시나리오는 호출 결과뿐 아니라 연관 테이블의 행 수를 확인하여 생성·유지·삭제 여부와
  거부된 요청에 부수효과가 없음을 검증한다.

## 프로젝트와 레지스트리 사이에 association을 만들면서 default 레지스트리로 지정한다

이 호출은 아직 association이 없는 프로젝트와 레지스트리 사이에 association을 만들고, 그 레지스트리를
프로젝트의 default 레지스트리(image commit 대상)로 지정한다. 레거시 프로젝트 생성이 프로젝트를 만든 직후 이
호출을 쓴다.

- 허용 프로젝트 추가와 같은 association 생성 작업이다. 그래서 레지스트리와 프로젝트 양쪽에 생성 권한이 있어야
  실행된다.
- association 생성과 default 지정은 한 번에 쓰인다. association 생성이 거부되면 default 지정도 남지 않는다.
- association이 이미 있는 프로젝트는 이 호출로 default를 지정할 수 없다. 이 호출은 association을 새로 만들 때만
  default를 함께 쓰기 때문이다. 기존 association을 default로 바꾸는 일은 프로젝트의 default 레지스트리 전환이 맡는다.

## purge 는 레지스트리와 허용 프로젝트 관계를 함께 제거한다

이 어댑터는 soft delete와 복원을 지원하지 않는다. purge 하면 레지스트리 행이 데이터베이스에서
제거된다. 옛 삭제 호출(GQL `admin_delete_container_registry_v2`, REST `POST /delete`)은 같은
purge 를 부른다.

## 여럿 purge

- 여럿 purge 는 호출 전체를 거부하지 않는다. 처리한 레지스트리는 처리된 목록에, 처리하지 못한 것은
  ID 와 이유를 실패 목록에 싣는다.
- 단건 purge 는 슈퍼관리자 여부를 검사하지만, 여럿 purge 는 레지스트리마다 HARD_DELETE 권한을
  검사한다. 슈퍼관리자 검사는 GQL resolver 와 REST handler 가 맡는다.

## 이름과 registry 내부 프로젝트명 조회는 레지스트리 읽기 권한을 검사한다
