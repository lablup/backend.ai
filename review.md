아래는 각 브랜치별 리뷰 사항이다. 이를 어떻게 반영할지 계획을 수립해줘.

### 전체
1. Delete role 액션은 상태만 변경하도록, Purge role 액션은 실제 레코드를 제거하도록 수정. 현재 Delete role 액션이 Purger를 넘겨주지만, 이 값으로 상태를 업데이트하도록 작성되어 있다. 따라서, Delete role은 Updater를 넘겨주고, Purge role 액션을 추가하고 이 액션이 Purger를 넘겨주도록 바꾼다.
2. raise할 모든 에러는 반드시 커스텀 정의된 에러여야 한다. ValueError, aiohttp.web 에러를 발생시키지 않도록.
3. update, delete등의 액션 타겟 레코드가 존재하지 않을 때, null 값을 반환하지 말고 not found 에러를 반환하도록 수정.

### feat/BA-3380-types-and-infrastructure

1. UUIDFilter, StrictValueFilter 클래스와 convert_strict_value_filter() 함수는 제거. 직접 비교할 값은 따로 이런 클래스나 함수를 만들지 말자. 예를 들어, 어댑터에서 Role.id==role_id 이런 식으로 직접 넘겨주도록 수정.

2. ai.backend.manager.data.permission.permission의 def to_creator() 함수는 제거.
3. ai.backend.manager.data.permission.role의 RolePermissionsUpdateInput가 Creator, Purger를 인자로 갖도록 수정.

  
### feat/BA-1810-rbac-repository-refactor
1. ai.backend.manager.repositories.permission_controller.db_source.db_source의 create_role() 메서드 인자를 데이터클래스로 수정 (확장성을 위하여).
2. pg_input와 같은 `pg_` prefix 변수명은 지양. (Postgres와 헷갈릴 여지가 있다)
3. delete_permission(), delete_role() 반환값이 nullable이 아니도록 바꾸고, 값이 null인 경우 not found를 raise하도록 수정
4. delete_role()이 Purger가 아니라 Updater를 받도록 수정
5. ai.backend.manager.services.permission_controller.actions.permission에 BaseAction을 상속받기보다 `PermissionAction`을 따로 만들어서 entity_type()을 통일하고 이를  상속하도록 수정.

### feat/BA-3377-rbac-dto-and-exceptions
1. ai.backend.common.dto.manager.rbac.request.SearchRolesRequest의 order 필드는 리스트로 수정되어야 한다 (여러 ordering을 받을 수 있으므로)
2. ai.backend.manager.services.permission_controller.service의 update_role_permissions() 함수에 repository의 private member인 `_db_source`에 접근하고 있다. 이런 식의 접근은 **절대로 행해져서는 안되며** repository에 public 함수를 추가하여 이를 통해 접근하도록 수정되어야 한다.
3. ai.backend.common.dto.manager.rbac.response.RoleDTO에 updated_at 필드가 nullable을 non-nullable로 수정. ai.backend.manager.data.permission.role.RoleData의 updated_at 필드 또한 non-nullable로 바꾸고, 만약 db에서 updated_at 필드 값이 null인 경우 created_at 값을 그대로 쓰도록 변경
4. ai.backend.common.dto.manager.rbac.response.RevokeRoleResponse에 `user_role_id` 필드는 제거.

### feat/BA-3378-rbac-adapters
1. ai.backend.manager.services.permission_controller.actions.object_permission에 ObjectPermissionAction를 정의하고 다른 액션이 이를 상속받도록 수정
2. ai.backend.manager.api.rbac.object_permission_adapter.ObjectPermissionAdapter, ai.backend.manager.api.rbac.object_permission_adapter.PermissionAdapter에 static method는 모두 instance method로 바꿔줘

### feat/BA-3379-rbac-handlers
1. create_app()에서 app prefix를 /v2/admin/으로 수정해줘. JIRA에 앱 버저닝, 어드민 전용 path를 구조화하는 이슈도 작성해줘
2. ai.backend.manager.api.rbac.handler에 raise web.HTTPForbidden는 모두 커스텀 예외로 바꿔줘

### feat/BA-2942-rbac-graphql-api
1. ai.backend.manager.api.gql.rbac.adapter에 RoleGQLAdapter를 따로 정의할 필요 없다. BaseGQLAdapter만 쓰면 된다.
2. ai.backend.manager.api.gql.rbac.resolver에서 raise ValueError 부분 모두 제거. (어차피 db_source에서 Not found 에러가 발생될 것이므로 여기서 핸들링할 필요 없다)