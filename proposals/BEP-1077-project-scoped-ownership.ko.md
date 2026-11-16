# 프로젝트 scope 소유와 접근

## 관련 이슈

- BA-7520 (이 문서), BA-6877 (공유 기록 마이그레이션), BA-7202, BA-7491, BA-7204 (legacy scope 매핑 제거)
- BEP-1062 (가상 스코프 RBAC 소유 모델)
- BEP-1069 (엔티티 lifecycle 삭제 관리)
- BEP-1076 (프로젝트 멤버십)

## 1. 동기

1. 자원을 가진 엔티티는 사용자나 프로젝트가 개별적으로 소유하는데, UI 는 프로젝트 단위로 보여주므로
   사용자 경험이 모호하다.

2. 프로젝트는 멤버 사이에 가시성을 제공하지 않는다. 소유자만 엔티티를 볼 수 있다. 프로젝트 관리자와
   멤버는 서로 다른 수준의 엔티티 가시성을 필요로 한다.
     * 프로젝트는 엔티티 종류별 가시성 옵션이 필요하다. (같은 메커니즘을 프로젝트 안의 사용자에도
       적용해야 한다.)
          1. 멤버 사이에 엔티티를 노출하지 않는다.
          2. 멤버 사이에 엔티티의 일부 field 만 노출한다.
          3. 멤버 사이에 엔티티를 전부 노출한다.

3. 사용자가 다른 프로젝트에서 접근할 수 있는 엔티티를 사용하려 할 때, 그 다른 프로젝트가 그것에 어떻게
   접근하는지에 대한 명확한 정책이 없다.

4. 엔티티의 접근 범위가 넓으면 그 접근을 공유할 때 의도보다 훨씬 많은 권한을 전달할 수 있다.

## 2. 목표

**프로젝트 뷰 우선 RBAC 을 전반에 적용하고, 그 위에 접근과 공유를 정의한다.**

1. 현재 UX 를 설정으로 표현할 수 있어야 하고, 그 설정이 기본값이다.
2. 소유 표현을 `scope -> virtual_scope -> entity` 로 통일하고 다른 모든 경로를 제거한다.
3. 가시성은 역할이 응답하고, 엔티티 종류 아래 field 수준까지 고를 수 있다.
4. 엔티티를 다른 scope 에 전달하는 동작을 하나의 균일한 묶음으로 정의한다.

## 3. 비목표

| 하지 않는 것 | 이유 |
|---|---|
| 업무 로직 relation 을 가상 스코프로 표현하는 것. 자원 정책 적용 여부, quota, 자원 그룹과 container registry 연결 | 가상 스코프는 접근 권한만 다룬다. 나머지는 엔티티 row 의 프로젝트 column 과 relation 테이블이 응답한다 |
| 프로젝트 안에 특별한 객체를 생성하는 방법을 부여하는 것 | 열린 프로젝트 안에서 비공개인 객체는 프로젝트가 누가 무엇을 소비하는지 보지 못하게 한다 |
| 어느 프로젝트에도 속하지 않는 자원 엔티티를 허용하는 것 | 모든 자원 엔티티는 프로젝트에 속한다. 그렇지 않으면 누가 삭제하고 누가 비용을 내는지 응답할 것이 없다 |
| 허용된 스토리지 호스트, 허용된 자원 그룹, 자원 정책의 위치를 옮기는 것 | 후속 작업으로 나눈다. 방향만 밝힌다. domain 과 프로젝트 축은 유지하고 키페어 축을 제거한다 (5.7 이전과 호환) |
| 공유하는 쪽이 볼 수 없는 프로젝트에 공유하는 것 | 찾을 방법이 없다 |
| 삭제와 정리 절차를 정의하는 것 | BEP-1069 가 정의한다 |

## 4. 영역별 현재 상태와 범위

영역마다 질문을 먼저 밝히고 **✅ 있는 것**과 **➕ 추가할 것**을 나눈다.

### 4.1 업무 로직은 소유자 기반이다

> 엔티티의 프로젝트 FK 는 **소유자**를 표현하지 접근 가능성을 표현하지 않는다. 자원 정책, quota,
> 삭제 권한 같은 업무 로직이 이를 읽고, 접근 권한은 읽지 않는다. 소유자에서 자원 정책을 읽는 것이
> 방향이고, 위치를 옮기는 일 자체는 후속 작업이다 (비목표).

| | 내용 |
|---|---|
| ✅ | 소유 표현이 엔티티마다 다르다. 세션, 배포, 모델 카드는 null 이 아닌 프로젝트 column 이 있고, 개인 vfolder 는 `group` 이 null 이며 프로젝트를 참조하지 않는다. 이미지는 column 이 없고 Docker 레이블 문자열이 참조한다. `models/vfolder/row.py:352`, `models/image/creators.py:87` |
| ✅ | 세션 커밋은 개인 scope 만 허용하는데, push 대상은 세션의 프로젝트가 정한다. `services/session/service.py:413`, `models/project/row.py:205` |
| ✅ | 허용량과 한도가 흩어져 있다. 허용된 스토리지 호스트와 허용된 자원 그룹은 domain, 프로젝트, 키페어 세 축에 있고, vfolder 와 이미지 한도는 사용자 자원 정책과 프로젝트 정책에 있다. `models/resource_policy/row.py:104` |
| ➕ | `ProjectType` 에 개인 프로젝트 값을 추가하고 모든 사용자와 함께 하나씩 생성한다 |
| ➕ | 모든 자원 엔티티에 프로젝트 column 을 준다. 개인 것은 개인 프로젝트를 참조하고, 이미지는 레이블에서 column 으로 옮기며 레이블은 최초 마이그레이션 입력으로만 사용한다 |

### 4.2 엔티티에 대한 권한 검사

> `scope -> virtual_scope -> entity` 를 따라가는 해석 하나가 응답한다. 단건 검사와 목록 질의가 같은
> graph 를 사용한다. 지금 검사 단위는 `(scope, 엔티티 종류, operation bit)` 이므로 엔티티의 일부만
> 부여하는 것을 표현할 수 없고, 실제 목록 동작은 legacy 경로에 있다.

| | 내용 |
|---|---|
| ✅ | graph 가 권한 해석의 기반이다 (BEP-1062). 생성 시 등재는 12 종류에 선언돼 있다. vfolder 는 사용자나 프로젝트 아래에 등재되고, 세션은 둘 다 아래에 등재된다. `models/vfolder/creators.py:60` |
| ✅ | 사용자가 프로젝트에 가입하면 사용자의 가상 스코프가 프로젝트 scope 에 묶이므로, 사용자 아래에 등재된 엔티티도 프로젝트 scope 권한으로 접근할 수 있다. 해석은 접근 가능한 모든 것에 균일하고, 한 scope 안에서 row 를 나누는 것은 없다. `repositories/permission_controller/db_source/db_source.py:1308` |
| ✅ | backfill 은 `entity_type='user'` 만 다뤘고, 기존 자원 엔티티에는 graph row 가 하나도 없다. `association_scopes_entities` 에 대한 재귀 CTE 는 deprecated 다. `alembic/versions/3ebcf2c3c959`, `db_source.py:998,1131` |
| ✅ | `RBACElementType` 은 `EntityType` 으로 합쳐지는 중이고 `permissions.entity_type` 은 `String(32)` 이므로 값을 추가하는 데 schema 변경이 필요 없다. `common/data/permission/types.py:474` |
| ✅ | 실제 목록 동작은 legacy 경로에 있고 세 역할로만 분기한다. 정리 대상이다. `api/gql_legacy/base.py:548` |
| ✅ | 전역 검색은 superadmin 과 전역 공유 값만 제공하고 권한을 건너뛴다. 사용자 DataLoader 도 권한을 건너뛴다. `repositories/ops/repository.py:199`, `api/gql/data_loader/data_loaders.py:669` |
| ➕ | 전역 검색은 global singleton 에서 권한을 검사하고 row 조건을 붙이지 않는다 (5.8). 사용자 DataLoader 는 권한을 인식하는 bulk 질의로 대체한다 |
| ➕ | 기존 자원 엔티티를 graph 에 backfill 하고 **`scope -> virtual_scope -> entity` 가 아닌 모든 경로를 제거한다.** legacy 재귀 경로, `association_scopes_entities`, `object_permissions`, `RBACElementType` (BA-7204) |
| ➕ | graph 에 own 과 govern 두 relation 이 있다. 생성(`created_in`)은 둘 다 기록하고, 공유는 cap 이 걸린 own 만 기록한다. 프로젝트와 사용자는 자기 domain 과 global 에 생성된다. 사용자의 가상 엔티티는 domain 과 global 이 govern 하며 프로젝트는 절대 govern 하지 않는다. 프로젝트 멤버 목록의 사용자는 READ cap 이 걸린 공유다 |
| ➕ | permission row 의 자식으로 `field_permissions` 테이블을 추가하고, 엔티티마다 catalog(field, 기본 가시 집합)를 선언한다. 검사는 항상 소유 엔티티를 지정한다. 예전 colon 하위 대상 이름은 field 다 |
| ➕ | 목록 포함 조건을 소유자 column 에서 graph 등재로 전환하고, `replace_share` 로 공유된 row 를 접근 가능 집합에 추가한다 |
| ➕ | 읽을 수 없는 field 를 비우고 그 field 로 필터링하거나 정렬하는 것을 거부한다. DataLoader 를 권한을 인식하는 bulk 질의로 대체한다 |

### 4.3 다른 scope 에서 엔티티에 접근하기

> 공유가 응답한다. 지금은 vfolder 에만 있고 legacy 테이블을 사용한다.

| | 내용 |
|---|---|
| ✅ | vfolder 초대만 두 legacy 테이블에 있다. 세션, 배포, 이미지, 모델 카드에는 없다 |
| ✅ | 공유 프리미티브는 받는 쪽을 엔티티 식별자로 받고, 공유 record 도 같은 방식으로 지정하며 만료를 담는다. `models/entity_share/row.py` |
| ✅ | `permission_cap` 은 operation bit 만 담으므로 어느 field 를 전달하는지 표현할 수 없다 |
| ➕ | 공유 record 테이블과 field 축을 담는 이름 있는 cap |
| ➕ | 세션, 배포, 이미지, 모델 카드를 공유 대상으로 추가한다 |

## 5. 구현 설계

### 5.1 소유 범위

모든 엔티티의 소유는 `scope -> virtual_scope -> entity` 로 표현하고, 자원 엔티티에 한정하지 않는다.

**이 경로가 유일하다.** `association_scopes_entities` 에 대한 재귀 경로, `object_permissions`,
`RBACElementType` 은 제거한다. 남기면 같은 질문에 응답이 둘이 된다.

graph 와 permission row(가상 스코프, 등재, binding, permission, field permission)는 ops 계층의 이름
있는 프리미티브로만 기록한다. 다른 계층은 이 row 를 위한 creator 나 purger 를 받지 않고, 그
프리미티브 밖에서 이 row 를 조각조각 생성하거나 변경하는 것은 없다. 역할과 프리셋 편집은 ops 가 row
를 도출하는 완전한 선언을 전달한다. 데이터 마이그레이션은 ops 밖의 유일한 기록자다. permission row
를 직접 다루는 admin mutation 은 legacy 경로와 함께 은퇴한다.

자원 엔티티는 세션, vfolder, 배포, 이미지, 모델 카드다. 소유 scope 는 항상 프로젝트다. **개인이
소유한 자원 엔티티는 그 사람의 개인 프로젝트에 속한다.** 사용자 scope 아래에 있는 자원 엔티티는
없다.

사용자 자신의 정보는 자원 엔티티가 아니다. 키페어, SSH 키, dotfile, 비밀번호는 사용자 아래에 남고
프로젝트로 옮기지 않는다.

개인 프로젝트는 `ProjectType` 값 하나로 구분한다. `groups.type` 은 이미 `general` 과 `model-store`
두 값으로 있다.

| 개인 프로젝트 | |
|---|---|
| 생성 | **사용자와 함께.** 예외 없이 항상 생성하고, 그 사람을 유일한 멤버로 둔다 |
| 멤버 | 그 한 사람. 추가 없음 |
| 수명 | 사용자에 묶인다 |
| 자원 정책 | 위치 이동은 후속 작업이다 (비목표). 그때까지 개인 vfolder 의 한도와 허용량은 지금의 키페어 정책 경로가 응답한다 |

그 유형이 동작을 변경하는 곳은 목록으로 고정한다. 멤버 추가 없음, 삭제는 사용자 purge 에 묶임, 지표
집계에서 제외. 나머지는 일반 프로젝트처럼 동작한다.

vfolder 는 생성 위치로 나뉜다.

| | 개인 vfolder | 프로젝트 vfolder |
|---|---|---|
| 생성 위치 | 자기 개인 프로젝트 | 그 프로젝트 |
| 팀 프로젝트에서 | cap 0 공유로 등재만 한다 (5.4) | 소속 자체 |

개인 vfolder 는 팀 프로젝트 안에서 생성하지 않는다. 팀 프로젝트 scope 에서 권한으로 접근 가능한
vfolder 는 모두 프로젝트 vfolder 다.

소유 프로젝트만 응답하도록 허용된 스토리지 호스트의 위치를 옮기는 일은 후속 작업이다 (비목표).
그때까지 개인 vfolder 허용량은 지금의 합집합 경로(`get_allowed_vfolder_hosts_by_user`)가 변경 없이
응답한다.

가용량 범위는 vfolder row 의 `quota_scope_id` 를 그대로 둔다. 기존 사용자 가용량 범위는 개인
프로젝트의 가용량 범위로 재해석한다. 물리 데이터는 옮기지 않는다.

공유는 엔티티를 가상 스코프에 넣고, 사람을 프로젝트에 넣지 않는다. 다른 사람의 개인
프로젝트에 공유해도 그 프로젝트에 멤버가 추가되지 않는다. 공유는 `entity_memberships` 에 row 만
추가하고 프로젝트 column 을 절대 변경하지 않으므로 자원 정책의 대상은 절대 바뀌지 않는다.

graph 에는 relation 이 둘이다. **own** 은 가상 엔티티가 엔티티를 보유한다. 엔티티는 그 가상
엔티티의 목록에 있고 한 hop 떨어져 있다. **govern** 은 scope 가 가상 엔티티를 govern 한다.
scope 의 역할이 그 가상 엔티티가 own 하는 모든 것에 접근한다. govern 이 둘 중 넓다. 생성과 공유가
이들을 조합한다.

| 선언 | own | govern | 규칙 |
|---|---|---|---|
| 생성 시 `created_in` | 예 | 예 | 세션은 자기 프로젝트와 사용자에, domain 은 global 에, 프로젝트와 사용자는 자기 domain 과 global 에 생성된다. 생성자의 목록에 있고 생성자의 역할이 그 아래에 접근한다 (초대). 공유 해제로 제거되지 않는다. 소유는 `transfer(from_scopes, to_scopes, entity)` 로 옮긴다. 사용자의 가상 엔티티는 domain 과 global 이 govern 하고 프로젝트는 절대 govern 하지 않으므로 사용자가 own 하는 것이 프로젝트로 새지 않는다 |
| relation `create_relation(scope, target)` | target 이 READ cap 으로 scope 를 보유한다 | scope 가 READ cap 으로 target 을 govern 한다 | 프로젝트가 자원 그룹이나 registry 와 그가 own 하는 에이전트나 이미지를 읽는다. 자원 그룹이나 registry 는 프로젝트 자체만 읽는다. public singleton 은 자원 그룹이 없는 global 컨테이너 레지스트리와 자원 프리셋을 instance 별로 이 relation 으로 연결하고, public 을 비활성화하면 relation 을 purge 한다 (5.8). govern 쪽 cap 을 기록하는 유일한 곳이다 |
| 공유 `replace_share(scope, entity, cap)` / `replace_share_fields(scope, entity, {READ: paths, UPDATE: paths})` | 예, cap 적용 | 아니오 | `replace_share` 는 cap 까지 모든 field 에 적용된다. cap 은 0 을 포함해 항상 명시한다. `replace_share_fields` 는 field 경로에만 READ/UPDATE 를 둔다 (5.2). `unshare` 로 제거한다. 공유는 받는 scope 에 빌려주는 것이므로 그 scope 자신의 govern 을 통해서만, 그리고 공유된 엔티티 자체에만 응답한다 |

프로젝트 멤버 목록의 사용자는 공유다. `replace_share_fields(project, user, {READ: 기본 공개
field})`. domain 멤버 목록은 없다. 사용자는 자기 domain 에 생성된다. 가입할 때 `auto_assign` 역할을
부여하는 것은 별도 프리미티브다.

| 질문 | 응답하는 것 |
|---|---|
| 누구의 프로젝트인가. 자원 정책과 quota 의 대상, 삭제 권한 | 엔티티 row 의 프로젝트 column (`vfolders.group`, `sessions.group_id`) |
| 무엇을 할 수 있는가 | `scope -> virtual_scope -> entity` 를 따라가는 권한 해석 |
| 어느 뷰에 나타나는가 | graph 등재. 생성 등재와 공유 등재의 합집합 (5.4) |

자원 그룹과 컨테이너 레지스트리와의 relation 은 위 표대로 graph 에 둔다. 자원 그룹이 세션과 배포를
보는 것은 scheduling 때 세션을 자원 그룹에 READ 로 공유해 응답한다 (후속). quota 와 자원 정책이
적용되는지는 graph 가 아니라 relation 테이블과 엔티티 row 가 응답한다.

### 5.2 FieldPermission

엔티티 종류 아래의 권한은 field 수준이다. colon 선언이 하위 대상 유형으로 지정한 것
(`deployment:token`, `vfolder:data`, ...)은 소유 엔티티의 field(token row, vfolder 내용, 세션
환경)이고, 어느 것도 엔티티 유형으로 승격하지 않는다. 검사는 항상 소유 엔티티를 지정한다. 어디에도
연결되지 않은 colon 선언은 `RBACElementType` 과 함께 은퇴한다 (BA-7204).

`FieldPermission` 이 없는 permission row 는 모든 field 에 적용된다. `FieldPermission` 이 붙으면
동작별(read, update)로 나열된 field 만 적용된다. field 의 row 를 추가하거나 제거하는 일, 예를 들어
token 발급은 그 field 에 대한 update 다. catalog 의 기본 가시 집합은 일부만 노출할 때 프리셋이 참조하는
기준 목록이다.

field 검사는 query, search, update spec 이 수행한다. 권한이 없는 field 는 읽기에서 비우고 update
입력에서 뺀다. GraphQL 처럼 field 를 명시적으로 요청하는 인터페이스는 거부로 응답해야 한다.

엔티티마다 catalog 를 선언한다. 목록에 없는 이름은 권한을 받을 수 없고, 목록에 없는 field 는
누구에게도 보이지 않는다.

| catalog 가 응답하는 것 | |
|---|---|
| field 목록 | 질의, 정렬, update 에서 사용하는 이름 |
| 기본 가시 field | 프리셋이 field 목록을 구성할 때 사용하는 기준 집합 |

네 spec 이 catalog 에 근거한다. query 데이터 변환, 조건과 정렬, update, natural key lookup. natural
key lookup 은 그 key 가 속한 field 에 대한 read 를 요구한다. 어긋남은 빠짐없는 테스트가 잡는다.

### 5.3 가시성

역할이 가진 것이 곧 가시성이다. 별도 개념은 없다.

```
Resource entity: visible = a role or an individual grant grants it
Person field:    visible = a role grants it, or I fall inside the subject's disclosure range
Editable = permission grants it (same for both)
```

자원 엔티티에는 대상자 축이 없다. 개별 객체를 비공개로 보이지 않게 하는 것은 비목표에서 금지한다.

동기의 가시성 항목이 제시한 세 선택지는 역할 프리셋으로 표현한다.

| 선택지 | 표현 |
|---|---|
| 노출 없음 | 멤버 역할은 create 만 받고 read 나 update 는 받지 않는다. 관리자만 본다 |
| 일부 field 만 | read 에 `FieldPermission` 목록을 붙인다. 기본 가시 집합이 출발점이다 |
| 전체 노출 | `FieldPermission` 없이 엔티티 권한을 부여한다. 모든 field 가 열린다 |

엔티티는 프로젝트에 등재되지만 멤버 역할에 read 가 없으면 보이지 않는다. 생성자는 자기 소유 경로로,
관리자는 역할 권한으로 본다.

기본 프리셋은 엔티티 종류마다 다르다. 지금 동작을 재현하는 것이 기본이고, 프로젝트 vfolder 의 멤버
생성을 여는 것이 의도한 유일한 확장이다.

| 종류 | 멤버 | 프로젝트 관리자 | 소유자 |
|---|---|---|---|
| vfolder (프로젝트 vfolder) | 모든 동작 | 모든 동작 | - |
| 세션, 배포 | create 만, read 없음 | 기본 가시 집합 | 자기 것 전부 |
| 이미지, 모델 카드 | 없음 | 기본 가시 집합 | 자기 것 전부 |
| 사용자 (멤버 목록) | 없음. 동료는 공개 범위로 서로를 본다 | read, 기본 가시 field | - |

세션 read 가 없는 멤버도 자기 세션은 본다. 자기 소유는 접근 가능 집합의 별도 원천이다 (5.4).

사용자 field 에는 대상자가 정하는 공개 범위가 있다.

```
self / project / domain / authenticated users
```

- 관리자는 이 목록에 없다. 관리자는 권한 경로로 본다.
- 프로젝트 정책이 최소 공개 범위를 정하고, 대상자는 더 넓게만 고를 수 있다.
- 비밀번호처럼 누구에게도 보이지 않는 field 는 catalog 에 넣지 않는 것으로 응답한다. 이 설정 밖이다.
- 사용자 update 는 domain 역할에 속하고 항상 `FieldPermission` 목록을 가진다. 자격 증명 secret(secret
  key, 비밀번호, private key)은 어떤 관리자의 field 목록에도 절대 없다. 관리는 재발급과
  비활성화이지 읽기가 아니며, secret 은 발급 시 소유자에게 한 번 보여준다.
- 세션 환경 변수는 사용자 field 가 아니다. 세션 field 로 다룬다.

| field | 기본 공개 |
|---|---|
| 액세스 키 식별자, 허용된 클라이언트 IP, 이중 인증 상태 | self |
| container uid 와 gid | self |
| email, 표시 이름 | domain |

이 설정은 대상자와 field 에만 의존하므로 권한 해석 질의에 join 되지 않는다. 설정은 이름 있는
profile 을 참조한다. 이름을 지정한 수신자에게 여는 것은 가시성이 아니라 공유다.

### 5.4 질의

```
Project-view query = entities enrolled in that project  AND  entities accessible to me
```

멤버십 판단은 소유자 column 에서 graph 등재로 옮긴다. 생성 등재와 공유 등재의 합집합이다. 뷰 필터와
권한 해석이 같은 graph 를 따라가므로 두 기준이 어긋날 수 없다. 소유자 column 은 자원 정책과 quota
판단에만 남는다.

접근 가능 집합에는 원천이 셋이다. 자기 소유, scope 권한, 개별 공유. scope 권한은 row 마다 달라지지
않고 상수이며, row 마다 달라지는 것은 개별 공유뿐이다.

모든 자원 엔티티 질의는 프로젝트 뷰다. 다른 점은 자기 개인 프로젝트를 보는지 다른 프로젝트를 보는지
뿐이다.

| 뷰 | 조건 |
|---|---|
| 프로젝트 뷰 | 등재 AND 접근 가능 |
| 나에게 공유됨 | 개별 공유만 |

조건은 정확히 한 곳, scoped search 에서 붙는다. 전역 검색은 global singleton 에서 권한을 검사하고
row 조건을 붙이지 않는다 (5.8). searcher spec 에 들어가지 않는다. 입력은 scope 만 지정하고,
요청자가 권한을 가지는지는 내부에서 고정한다. 사용자 DataLoader 는 권한을 인식하는 bulk 질의로
대체한다.

권한 해석은 API 경계의 진입 판단만 담당한다. 내부 호출은 권한 질의를 실행하지 않는다.

cap 0 공유 등재는 등재 집합에 들어가지만 아무것도 부여하지 않는다. 소유자가 자기 개인 vfolder 를 팀
프로젝트 뷰에 드러내기 위해 존재한다. 다른 멤버와 관리자는 접근 가능 집합이 비어 있어 아무것도 보지
못한다.

scoped read action 은 거부 대신 필터한다. 기록 성격의 scoped action 은 지금처럼 거부하며, action
마다 표시한다.

읽을 수 있는 field 만 채우는 일은 row 를 가져온 뒤 해석을 한 번 더 거쳐 일어난다. row 는 줄지
않으므로 pagination 이 유지된다.

읽을 수 없는 field 는 필터링이나 정렬에 사용할 수 없다. 다른 엔티티를 참조하는 식별자는 기본 가시
집합에 속한다. 식별자를 따라 그 엔티티로 들어가는 것은 그 엔티티의 권한을 요구하고, 없으면 거부한다.
응답은 이번에 채운 field 목록을 담고, 어느 것이 비었는지 이유를 절대 설명하지 않는다.

### 5.5 공유

대상은 세 검사를 통과해야 한다. instance 마다 소유가 다른가, 소유자가 그것을 보여줄 이유가 있는가,
다른 scope 에서 사용하는 것이 타당한가.

| 엔티티 | |
|---|---|
| vfolder, 배포, 모델 카드 | 대상 |
| 세션 | 관찰만. 입장은 제외 |
| 이미지 | 소유가 column 으로 옮겨간 뒤 대상 |
| 키페어, secret | 대상 아님 |
| 커널, route, 세션 그룹 | 대상 아님 |

세션 입장은 제외한다. mount 가 접근 제어를 우회하기 때문이다. 개인 vfolder mount 는 소유자 외에는
그 세션에 입장할 수 없을 때만 허용하고, mount 시점에 검사한다. mount 가능성은 등재와 무관한 소유
기반 검사이고, 등재는 노출만 응답한다.

보이지 않는 대상은 지정할 수 없다.

| 대상 | 주소 | 수락 |
|---|---|---|
| 사람 (계정 있음) | user id 또는 email | 항상 필요 |
| 사람 (계정 없음) | email | 항상 필요 |
| 프로젝트 | 프로젝트 id | 항상 필요 |
| 소유 이전 | | 받는 쪽이 수락해야 함 |

개인 프로젝트는 프로젝트로 지정하지 않는다. 다른 이름을 가진 한 사람이므로 그 사람을 사람으로
지정한다. 둘 다 허용하면 graph 가 간선 하나를 가지는 한 수신자에 row 둘이 생긴다.

외부 팀에 주려면 그 팀의 한 사람에게 주고, 그 사람이 자기 팀에 넣는다. 사람에게 준 것은 그 사람의
개인 프로젝트에 들어간다.

cap 은 공유 row 마다 bit 별 row 다. `replace_share(scope, entity, cap)` 은 cap 의 bit 마다 "모든
field" row 를 하나씩 기록한다. `replace_share_fields(scope, entity, fields)` 는 READ/UPDATE bit 에
"path" row 를 기록한다. token 없이 배포를 공유하는 것은 token path 를 빼고
`replace_share_fields` 를 호출한다. path 는 하위를 포함하고 deny 는 없다. 실제 field 는
역할의 field 범위와 path 에 있는 cap 들의 field 범위의 교집합이다. 이름 있는 cap(프리셋)은 이 둘을
호출하는 편의일 뿐 저장 단위가 아니다.

| 항목 | 의미 | 조합 |
|---|---|---|
| 프리셋 기본 | 주는 것 | 종류별 합집합 |
| 역할 설정 | 주는 것 | 종류별 합집합 |
| 공유 하나의 cap | 상한 | 교집합 |
| 초대가 전달하는 cap | 상한 | 교집합 |

```
granted[entity][element_type] |= permission(scope, element_type) & scope_cap & entity_cap
```

공유 가능한 종류는 받는 쪽의 own scope 역할에 있어야 한다. cap 은 좁히기만 하므로 그것이 없으면
공유는 아무것도 부여하지 않는다. cap 0 은 유효하다. 아무것도 부여하지 않으면서 등재는 남긴다 (5.4).

재공유는 cap 의 create bit 로 표현하고 기본은 닫힘이다. 열려면 연쇄 해지가 필요하고, 연쇄 해지에는
부모 공유 기록이 필요하다. 연쇄 없이 재공유를 여는 조합은 없다. 자기가 보유하지 않은 field 는 전달할
수 없다.

해지는 공유할 수 있는 누구나와 받는 쪽 모두 할 수 있고, 실행 중인 작업에 소급되지 않는다.

초대, 공유, 해지는 `entity_memberships` 와 분리된 하나의 테이블에 있다.

| 상태 | graph row |
|---|---|
| 초대됨 | 없음 |
| 활성 | 있음 |
| 거절됨, 만료됨 | 없음 |
| 해지됨 | 삭제됨 |

별도의 직접 공유 경로는 없다. 엔티티 접근을 전달하는 일은 모두 제안으로 시작하고 받는 쪽이 정한다.
사람이 받은 것은 그 사람만의 프로젝트에 들어가고, 프로젝트가 받은 것은 그 프로젝트에 들어간다.

수락은 응답한 scope 를 기록한다. 주소로 도달한 제안은 그때까지 scope 를 가지지 않으므로 수락이
그것을 채운다.

수신자와 엔티티마다 살아 있는 row 하나가 있고, 살아 있다는 것은 제안됐거나 받아들여졌다는
의미이며, 끝난 row 는 그 옆에 쌓인다. 공유가 이미 있는 곳에 다시 제안해도 row 를 추가하지 않고 그
공유가 무엇을 빌려주는지 새로 밝힌다. 이미 받아들여진 곳이면 graph 간선을 그것과 함께 다시
진술하므로 좁히기가 즉시 적용된다. 빌려주는 것은 해지와 마찬가지로 빌려주는 쪽이 정한다.

엔티티를 own 하는 scope 에는 그것을 제안할 수 없다. 대여는 지금 성립한 것을 진술하므로, 수락하면
소유 간선에 cap 이 걸려 그 scope 가 가진 것보다 적어지게 된다.

기다리는 중인 제안만 만료된다. 수락은 그 시점을 해제하고, 받아들여진 것은 해지될 때까지 유지된다.

삭제는 BEP-1069 가 정의한다. 공유하는 쪽이 세 가지를 정한다.

| | |
|---|---|
| 소유하는 쪽이 삭제할 때 | 공유된 모든 대상에서 사라진다 |
| 삭제 | 공유 row 를 유지한다 |
| purge | 공유 row 를 삭제한다 |

소유하지 않은 프로젝트에는 삭제 동작이 없고 공유 해제만 있다.

자원 그룹 허용량은 제출한 주체에 대해 검사하고 소유 기반으로 유지한다. 공유된 것에 대한 모든
action 은 소유 프로젝트에 대해 검사한다.

### 5.6 엔티티별 차이

| 엔티티 | 소유 | 접근 | 공유 | 마이그레이션 |
|---|---|---|---|---|
| vfolder | 개인 vfolder 는 개인 프로젝트에, 프로젝트 vfolder 는 그 프로젝트에 | vfolder 데이터는 field 로 제공하고, 멤버는 프로젝트 vfolder 에 모든 동작을 받는다 | 신규. cap 0 등재 포함 | 개인 vfolder 의 소유와 등재를 개인 프로젝트로 옮긴다 |
| 세션 | 이미 프로젝트 | 멤버는 create 만. 상세와 환경은 field 로 나뉜다 | 관찰만 | 없음 |
| 배포 | 이미 프로젝트 | 멤버는 create 만. token 과 revision 은 field 로 제공한다 | 신규 | 없음 |
| 이미지 | 레이블에서 column 으로. 커밋된 이미지는 개인 프로젝트 소유 | 나눌 것 없음 | column 마이그레이션 뒤 | 레이블 backfill |
| 모델 카드 | 이미 프로젝트 | 나눌 것 없음 | 신규 | 없음 |
| 사용자 | 그 자체가 scope | 자격 증명과 profile 은 field 로 나뉜다 | 대상 아님 | 없음 |

### 5.7 이전과 호환

| 단계 | 내용 |
|---|---|
| 1 | 자원 엔티티의 가상 스코프 멤버십을 backfill 한다 |
| 2 | `ProjectType` 값을 추가하고 사용자마다 개인 프로젝트를 생성한다. 이후 사용자 생성 경로가 그것을 생성한다 |
| 3 | 개인 vfolder 의 소유자 column 과 등재를 개인 프로젝트로 옮긴다. `quota_scope_id` 는 유지한다 |
| 4 | 이미지 레이블을 소유 column 으로 옮기고 개인 프로젝트를 대상으로 한다. 레이블은 이 최초 입력으로만 사용한다 |
| 5 | legacy vfolder 공유 테이블을 공유 record 와 graph 로 마이그레이션한다 |
| 6 | `global` 과 `public` singleton row 와 그 가상 엔티티 node 를 생성한다 |
| 7 | 멤버십을 backfill 한다. global 엔티티와 domain 을 global 에, 유형 전체가 public 인 엔티티를 global 과 public 에, 프로젝트와 사용자를 추가로 global 에 넣는다 |
| 8 | public relation 을 backfill 한다. `is_global=true` 인 컨테이너 레지스트리와 자원 그룹이 없는 자원 프리셋을 public 에 연결한다 |
| 9 | public 기본 역할을 생성하고 모든 사용자에게 부여한다 |
| 10 | gate validator 를 singleton 권한 검사로 전환한다 |

1 단계가 없으면 나머지는 아무것도 하지 않는다. 10 단계는 7 부터 9 단계 뒤에 적용한다. 세션, 배포,
모델 카드는 null 이 아닌 프로젝트 column 을 가지므로 옮길 것이 없다.

자원 정책과 허용량의 위치를 옮기는 일은 후속 작업이다 (비목표). 그때까지 개인 vfolder 의 한도와
허용량은 지금의 키페어 정책 경로가 변경 없이 응답하므로 이 마이그레이션은 검사 동작을 변경하지 않는다.
후속 방향: 허용된 스토리지 호스트와 허용된 자원 그룹을 domain 과 프로젝트 축에만 두고 키페어 축을
제거한다. 사용자 자원 정책의 vfolder 와 이미지 한도를 프로젝트 정책으로 옮긴다. `allowed_vfolder_types`
설정을 정책에 흡수하고 은퇴시킨다.

커밋된 이미지는 지금처럼 개인 전용으로 남고 소유 scope 가 개인 프로젝트가 된다. push 되는 물리
registry 는 소유와 무관하게 세션의 프로젝트 설정을 계속 따른다. 물리 배치는 바뀌지 않는다.

남겨진 개인 프로젝트는 소유자 없는 프로젝트가 된다. 비워질 때까지 사용자 purge 를 차단하거나, 유예
기간 뒤 함께 purge 한다.

| 지금 | 이후 |
|---|---|
| 일반 사용자는 자기 세션만 본다 | 같음. 멤버 역할에 세션 read 를 부여하지 않는 것이 기본이다 |
| domain 관리자는 domain 전체를 본다 | 같음 |
| 개인 vfolder 는 소유자와 공유받은 사람만 본다 | 같음. 팀 프로젝트 scope 에 묶이지 않은 개인 프로젝트에 있다 |
| 개인 vfolder 에 사용할 수 있는 스토리지 호스트 | 같음. 검사 경로가 바뀌지 않는다 |
| 프로젝트 vfolder 는 모든 멤버가 본다 | 같음 |
| 프로젝트 vfolder 생성 | 넓어진다. 관리자 전용에서 모든 멤버로. `services/vfolder/services/vfolder.py:329` |
| vfolder 초대 | 같음. 대상에 프로젝트가 추가된다 |
| 세션 커밋 | 같음. 개인 소유만 |
| 동료의 사용자 정보 | 좁아진다. 자격 증명이 가려진다 |
| 관리자가 키페어 secret 을 읽음 | 좁아진다. 자격 증명 secret 을 누구도 읽을 수 없고, 관리가 재발급과 비활성화가 된다 |

프로젝트 vfolder 생성 확대와 사용자 정보 축소가 의도한 변경이다.

| UI 에 필요한 것 | |
|---|---|
| 나에게 공유됨 목록 | 개별 부여만 사용하는 질의 |
| 소유자 표시 | 소유 프로젝트 이름만 |
| 삭제 버튼 | 소유하지 않은 프로젝트에는 없음 |

### 5.8 global 과 public scope

어느 scope 에도 속하지 않던 global 엔티티를 `global` 과 `public` 두 singleton scope 아래에 모은다.
superadmin 전용 gate 와 login 전용 gate 는 이 두 scope 의 역할 권한으로 정한다.

지금 "모두에게 보임"은 네 가지 방식으로 표현된다. superadmin 전용 gate 는 역할로 위임할 수 없다.

| 방식 | 예 |
|---|---|
| login 만 검사하는 gate | runtime_variant, resource_slot_type, login_client_type, prometheus_query_preset |
| column 조건 | `container_registries.is_global`, `resource_presets.scaling_group_name IS NULL`, `app_config_fragments.scope_type='public'` |
| 빈 `scope_targets` | public app_config_fragment 검색 |
| 자동 가입 | MODEL_STORE 프로젝트 |

**Singleton**

| 이름 | 의미 | 기본 접근 |
|---|---|---|
| `global` | 시스템 소유 scope. 소유 트리의 root | 없음. 역할을 부여받은 사용자만 |
| `public` | 모든 사용자에게 노출된 scope | 모든 사용자에게 자동 부여되는 기본 역할을 통한 READ |

- 두 singleton 은 엔티티 유형이 `global` 이고 id 로 구분한다. 역할 내용만 다르다.
- 테이블 하나는 엔티티 유형 하나에 대응한다. 어떤 테이블도 여러 유형으로 읽히지 않는다.

**테이블과 id**

| 항목 | 내용 |
|---|---|
| 테이블 | `global_entities(id, name, created_at)`, `name` unique |
| 이름의 원천 | 코드 enum (`GLOBAL`, `PUBLIC`) |
| row 생성 | 마이그레이션이 이름으로 insert 하고 DB 가 id 를 생성한다 |
| id lookup | manager 시작 시 한 번 질의해 이름, id cache 로 둔다. 요청은 cache 를 읽는다 |
| 코드 참조 | 이름으로만. UUID 상수 없음, seed 파일 없음 |

- cache 가 load 되기 전에 id 를 읽으면 에러가 난다. DB 를 사용하는 CLI 명령은 cache 를 먼저 load 한다.
- id 는 설치마다 다르므로 테스트와 fixture 는 이름만 참조한다.

**존재 보장**

service 로직은 singleton 이 항상 있다고 가정한다.

| 계층 | 역할 |
|---|---|
| DB | 마이그레이션이 insert 한다. 삭제 방지 trigger 는 없다. `models/AGENTS.md` 는 `global_entities` row 와 singleton 가상 엔티티 node 를 절대 삭제하지 않는다고 밝힌다 |
| ops | singleton node 를 찾고, 없으면 호출이 실패한다. singleton 을 암묵적으로 생성하는 경로는 없다 |
| Manager 시작 | id cache 를 load 하면서 두 row 와 node 가 있는지도 검사한다. 없으면 시작이 실패하고 복구 명령을 알려준다 |
| 복구 | `mgr permissions provision` 이 enum 에서 row, node, 멤버십, relation, 프리셋 역할을 조정한다. 새 id 가 생성되면 manager 를 재시작한다 |

singleton node 를 삭제하면 FK cascade 로 그 scope 의 역할, 역할 할당, 연결이 삭제된다. superadmin
이 직접 생성하거나 할당한 역할은 원천이 없어 backup 에서만 복구할 수 있다.

**멤버십과 relation**

| 대상 | 방식 | 값 |
|---|---|---|
| global 엔티티 | 멤버십 | `global` |
| 유형 전체가 public 인 엔티티 | 멤버십 | `global`, `public` |
| domain | 멤버십 | `global` |
| 프로젝트, 사용자 | 멤버십 | `domain`, `global` |
| instance 별 public (`is_global`, 자원 그룹이 없는 프리셋) | `public` 에 대한 relation. 비활성화할 때 추가하고 purge 한다 | 멤버십은 `global` 유지 |
| 소유자가 바뀌는 엔티티 (vfolder, 에이전트, 템플릿) | 기존 멤버십을 옮긴다 (`transfer`) | 변경 없음 |

- 모든 global 엔티티는 global 의 멤버다. public 은 노출을 넓히지만 소유 트리의 root 가 아니다.
- 유형 전체가 public 인 것은 전환하지 않으므로 멤버십이다. 멤버십은 cap 을 담지 않으므로 public 역할의 내용이 READ 로 제한한다.
- instance 별 public 은 relation 이다. relation 이 READ cap 으로 대상을 govern 하므로 public 역할이 registry 와 그가 own 하는 이미지를 읽는다.
- public 을 비활성화하면 relation 을 즉시 purge 한다.
- instance 별 public 의 원천은 column(`is_global`, `scaling_group_name`)이다. 복구와 질의 조건이 column 을 읽는다.
- 프로젝트와 사용자도 global 의 멤버이므로, global 역할이 프로젝트와 사용자가 own 하는 자원에 접근하면서도 권한 해석은 두 단계(멤버십과 govern)로 유지된다. 재귀 질의는 없다.
- 하위 자원(커널, revision, replica, route, ...)은 node 를 받지 않고 소유 엔티티에 대한 field 검사로 남는다.
- global 엔티티 생성은 다른 엔티티와 같은 생성 spec 과 scope 검사를 사용하고, 대상 scope 는 `global` 이다.

**역할**

| scope | 역할 | 할당 | 권한 |
|---|---|---|---|
| public | 기본 역할 | 모든 사용자에게 자동 부여 | 유형 전체 public 엔티티와 container_registry, image, resource_preset 에 대한 READ |
| global | 위임 역할 (선택) | superadmin 이 할당 | 예: container_registry 에 대한 write |

- singleton 역할은 프리셋에 scope 항목을 추가해 선언한다. 없으면 지금처럼 유형마다 역할을 생성하고, 있으면 그 scope 에서만 생성한다.
- seed 파일이 scope 를 지정하고(`scope: public`), provision 이 DB 에서 id 를 푼다.
- global 과 public 의 역할을 관리하려면 `role` 권한이 필요하므로 superadmin 이 한다.

**사용자 역할 bypass**

RBAC 역할과 동기화하지 않는다.

| 사용자 역할 | bypass 위치 | 동작 |
|---|---|---|
| superadmin | graph 권한 해석 | node 가 있으면 전체 권한 |
| monitor | 전역 validator | global operation 중 read 만 통과 |

monitor bypass 는 graph 권한 해석으로 넓히지 않는다. 넓히면 id 로 단건 조회가 열린다.

**Gate**

| 지금 | 이후 | 질의 조건 |
|---|---|---|
| superadmin 전용 gate | superadmin, monitor bypass 뒤에 global singleton 에서 action 유형과 operation 권한을 검사한다 | 없음. 전체 목록 |
| login 전용 gate | public singleton 에서 권한을 검사한다 | 유형 전체 public 은 없음. instance 별 public 은 기존 column 조건 유지 |
| 익명 gate | 유지 | 사용자가 없으므로 역할이 정하지 않는다 |

validator 는 processor 생성자에서 고정되므로 호출부는 바뀌지 않는다.

**분류**

| 엔티티 | 멤버십 | public relation 조건 | 사용자 노출 경로 |
|---|---|---|---|
| runtime_variant, runtime_variant_preset | global, public | | public 역할 |
| prometheus_query_preset, prometheus_query_preset_category | global, public | | public 역할 |
| resource_slot_type, login_client_type | global, public | | public 역할 |
| deployment_preset | global, public | | public 역할 |
| app_config_fragment (`scope_type='public'`) | global, public | | public 역할 |
| container_registry | global | `is_global=true` | public relation |
| resource_preset | global | `scaling_group_name IS NULL` | public relation |
| domain | global | | domain 역할 |
| resource_group | global | | domain, 프로젝트, 사용자 relation |
| idle_checker | global | | domain, 프로젝트, 자원 그룹, 사용자 relation |
| keypair, user, project resource_policy | global | | 사용자, 프로젝트 참조 |
| object_storage, vfs_storage, storage_namespace | global | | 없음 |
| artifact_registry, artifact | global | | 없음 |
| notification_channel, notification_rule | global | | 없음 |
| retention_policy, role_preset | global | | 없음 |
| app_config_allow_list, app_config_definition | global | | 없음 |
| service_catalog, client_ip_masking_policy | global | | 없음 |

**호환**

| 대상 | 동작이 그대로인 조건 |
|---|---|
| superadmin | graph 해석과 전역 validator 의 bypass 유지 |
| monitor | 전역 validator 의 read bypass 유지 |
| public 을 읽는 일반 사용자 | public 역할이 모든 사용자에게 부여되고, 유형 전체 public 엔티티가 validator 전환 전에 public 멤버십을 얻는다 |
| global operation 을 하는 일반 사용자 | 역할이 없어 거부된다. 지금과 같음 |

validator 는 역할 할당과 멤버십 backfill 뒤에 전환한다 (5.7 이전과 호환).

**범위 밖**

| 항목 | 처리 |
|---|---|
| MODEL_STORE 자동 가입, 모델 카드 가시성 | 프로젝트 소유로 유지한다. public 노출이 필요하면 public relation 을 검토한다 |
| domain 별 허용 registry | public 노출과 domain 허용 목록은 별개 계층이다 |
| monitor bypass 를 graph 해석으로 넓히기 | 하지 않는다 |
| artifact_registry 가 한 테이블을 여러 유형으로 읽기 | 별도로 다룬다 |

## 6. 결정 요약

| 결정 | 내용 |
|---|---|
| 소유 표현 | 자원 엔티티에 한정하지 않고 `scope -> virtual_scope -> entity` 로 통일한다 |
| 다른 경로 | 제거한다. legacy 재귀 경로, `association_scopes_entities`, `object_permissions`, `RBACElementType` |
| graph 와 permission row 기록 | ops 프리미티브로만. 이 row 를 위한 creator/purger 표면을 다른 곳에 두지 않는다. 역할과 프리셋 편집은 완전한 선언을 전달하고, permission row 를 직접 다루는 mutation 은 legacy 경로와 함께 은퇴한다 |
| 자원 엔티티 소유 scope | 항상 프로젝트. 개인이 소유한 것은 개인 프로젝트로 간다 |
| 개인 vfolder | 개인 프로젝트에서만 생성한다. 팀 프로젝트 안에는 없다 |
| 허용된 스토리지 호스트와 자원 정책 | 위치 이동은 후속 작업이다. 그때까지 키페어 정책 경로가 응답하므로 검사 동작은 바뀌지 않는다 |
| 가용량 범위 | `quota_scope_id` 유지. 사용자 가용량 범위를 개인 프로젝트의 것으로 재해석한다. 물리 이동 없음 |
| 사용자 자신의 정보 | 자원 엔티티가 아니다. 사용자 아래에 남는다 |
| column 과 graph | column 은 자원 정책과 quota 에, 권한 해석은 가능한 동작에, graph 등재는 뷰 멤버십에 응답한다 |
| relation | own 과 govern. `created_in` 은 둘 다 기록하고, 공유와 relation 은 cap 이 걸린 own 만 기록한다. 사용자의 가상 엔티티는 domain 과 global 이 govern 한다. public 은 자원 그룹이 없는 global 컨테이너 레지스트리와 자원 프리셋을 instance 별 relation 으로 연결한다 |
| 멤버 목록 | 프로젝트 멤버 목록의 사용자는 READ cap 이 걸린 공유다(기본 공개 field). domain → user 는 govern 이다 |
| 프로젝트 가입 | 프로젝트 관리자가 초대하고 초대받은 사람이 수락한다. 직접 등록은 domain 관리자 동작이다 (BEP-1076 프로젝트 멤버십) |
| 자격 증명 secret | 어떤 관리자도 읽을 수 없다. 관리는 재발급과 비활성화다. secret 은 발급 시 소유자에게 한 번 보여준다 |
| relation (자원 그룹, registry) | scope 가 READ 로 target 을 govern 하고, target 은 READ 공유로 scope 를 보유한다. 자원 그룹과 컨테이너 레지스트리 모두 같다. quota 는 relation 테이블이 응답한다 |
| `created_in` row | 공유 해제로 제거되지 않고 cap 을 담지 않는다 |
| 예전 colon 하위 대상 | 소유 엔티티의 field 다. 어느 것도 엔티티 유형으로 승격하지 않고 colon 선언은 `RBACElementType` 과 함께 은퇴한다 |
| field | `FieldPermission`. permission row 의 자식이고 read 와 update. 없으면 모든 field, 있으면 목록만 |
| catalog | 엔티티마다 선언한다. 목록에 없는 이름은 권한을 받지 못하고 목록에 없는 field 는 보이지 않는다 |
| 가시성 | 역할이 응답한다. 자원 엔티티는 권한 축만, 사용자 field 는 권한이나 대상자의 공개 범위를 사용한다 |
| 멤버 기본 프리셋 | 프로젝트 vfolder 는 모든 동작, 세션과 배포는 create 만, 이미지와 모델 카드는 없음 |
| 사용자 field 공개 | self / project / domain / 인증된 사용자. 프로젝트 정책이 최소를 정하고 대상자는 넓히기만 할 수 있다 |
| 질의 | graph 등재 AND 접근 가능(자기 소유, scope 권한, 개별 공유). scoped search 한 곳. 모든 질의는 프로젝트 뷰 |
| 전역 검색과 DataLoader | 전역 검색은 global singleton 에서 권한을 검사하고 row 조건이 없다. DataLoader 는 권한 인식 bulk 질의로 대체한다 |
| singleton scope | `global`(소유 트리의 root, 기본 접근 없음)과 `public`(모든 사용자에게 READ). 둘 다 엔티티 유형이 `global` 이고 id 로 구분 |
| 멤버십 규칙 | global 엔티티와 domain 은 global 에, 유형 전체 public 엔티티는 global 과 public 에, 프로젝트와 사용자는 자기 domain 과 global 에. instance 별 public 은 global 멤버십에 public relation 을 추가한다 |
| singleton id | 이름으로 `global_entities` 에 insert 하고 id 는 DB 가 생성한다. 코드는 이름만 참조하고 manager 는 시작 시 이름, id cache 를 한 번 load 하며 row 나 node 가 없으면 시작을 거부한다 |
| bypass | superadmin 은 graph 권한 해석, monitor 는 전역 validator 의 read. RBAC 역할과 동기화하지 않는다 |
| gate | superadmin 전용 gate 는 global singleton, login 전용 gate 는 public singleton 에서 권한을 검사한다. 익명 gate 는 유지 |
| 테이블과 엔티티 유형 | 테이블 하나에 엔티티 유형 하나. 어떤 테이블도 여러 유형으로 읽히지 않는다 |
| 해석 실행 위치 | API 경계의 진입 판단에만. 내부 호출은 권한 질의를 실행하지 않는다 |
| cap 0 공유 | 등재만 남기고 아무것도 부여하지 않는다. 소유자의 프로젝트 뷰에 드러내기 위한 것 |
| 참조 field | 식별자는 기본으로 가시적이다. 역참조는 대상 엔티티의 권한을 요구하고 없으면 거부한다 |
| scoped read | 거부 대신 필터한다. 기록 action 은 계속 거부한다 |
| 공유 주소 | 보이지 않는 대상은 지정할 수 없다. 사람은 user id 나 email, 프로젝트는 프로젝트 id. 개인 프로젝트는 프로젝트로 지정하지 않는다 |
| 공유 수락 | 항상 필요하다. 받은 것이 받는 scope 에 들어가기 때문이다. 수락 설정은 없다 |
| 공유 cap | 공유 row 마다 bit 별 cap row 하나. `replace_share` 는 모든 field, `replace_share_fields` 는 field 경로. 이름 있는 cap 은 둘을 호출하는 편의 |
| 재공유 | 기본은 닫힘. 열려면 연쇄 해지가 필요하다 |
| 공유 record | `entity_memberships` 와 분리한다. 초대 상태에는 graph row 가 없다 |
| 소유하지 않은 프로젝트 | 삭제 동작이 없고 공유 해제만 있다 |
| 자원 그룹 허용량 | 소유 기반. 공유는 배치 권한을 옮기지 않는다 |
| 커밋된 이미지 | 지금처럼 개인 소유만. 소유 scope 는 개인 프로젝트이고 물리 registry 는 세션 프로젝트 설정을 따른다 |
| 마이그레이션 순서 | graph backfill 이 먼저. 검사 동작은 바뀌지 않는다 |
| 개인 프로젝트 생성 | 사용자와 함께, 항상, 예외 없이 |
| 개인 프로젝트 구분 | `ProjectType` 값, 동작이 바뀌는 곳은 목록으로 고정 |

## 7. 열린 질문

- catalog(field, 기본 가시 집합)의 위치. 코드 선언에 두는 방식과 테이블에 두는 방식 중 선택
- 사용자 purge 를 개인 프로젝트가 빌 때까지 차단하는 방식과 유예 기간 뒤 자동 purge 하는 방식 중 선택
- 모델 카드를 vfolder 로 합치는 방식과 별도 엔티티로 두는 방식 중 선택
- 관리자가 cap 0 등재(프로젝트에 연결된 외부 vfolder)를 관찰할 수 있는지 여부. 관찰한다면 cap 에 read 를 넣는 것은 별도 결정
- 개인 vfolder 를 프로젝트 vfolder 로 전환하는 기능의 제공 여부
- GraphQL 이 명시적으로 요청된, 권한 없는 field 를 거부로 전환하는 계층
- 삭제 전에 엔티티를 사용하는 곳이 몇 곳인지 보여주는 것의 필요 여부

## 8. 참고

- [BEP-1062: Virtual Scope RBAC Ownership Model](BEP-1062-virtual-scope-rbac.md)
- [BEP-1069: Entity Lifecycle Deletion Management](BEP-1069-entity-lifecycle-deletion.md)
- [BEP-1076: Project Membership](BEP-1076-project-membership.md)
