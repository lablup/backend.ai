# BEP-1052: 스코프별 앱 설정 재설계

## 개요

앱 설정을 **스코프별 엔티티**로 재설계한다. `(scope_type, scope_id, config_name)` 하나당 row 하나를 두어 저장과 병합이 스코프 수준에서 이뤄진다. 스코프 하나(도메인 하나, 사용자 하나)가 **이름 있는 config 여럿**(`theme`, `menu`, `preferences` 등)을 가질 수 있고, 각각 독립적으로 관리된다.

**조회가 hot path 다.** 사용자가 `config_name` 하나에 대해 실제로 적용받는 설정은 **그 사용자에게 적용되는 모든 fragment 를 deep merge 한 값**이다. fragment 는 `app_config_fragments` 에서 가져오고, 각 fragment 의 허용 목록 항목이 가진 `rank` 순서로 정렬한다. 인덱스 하나를 타는 join 한 번이며, **권한 조회가 없다.** 호출자를 구분하는 데도 권한 조회가 필요 없다. 조회는 도메인만 지정하고 스코프의 사용자 쪽 절반은 세션에서 주입되므로, 호출자가 다른 사용자의 config 를 요청할 방법이 없다.

**쓰기 권한은 미리 설정한다.** 모든 config 이름은 `app_config_definitions` 에 **명시적으로 등록**하고, 관리자가 **미리 구성한** `app_config_allow_list` row 가 fragment 를 쓸 수 있는 `(config_name, scope_type)` 짝을 나열한다. 관리자든 사용자든 **모든** fragment 쓰기에는 짝이 맞는 row 가 필요하다. 관리자는 여기에 추가로 허용 목록과 `app_config_definitions` 자체를 가진다(사용자는 아니다). 따라서 권한 비용은 전부 (드문) 쓰기 경로와 (한 번뿐인) 관리자 설정에 있고, 조회에는 없다.

값이 관리자가 고정한 값인지 사용자가 재정의할 수 있는 값인지는 허용 목록 부여가 있는지로 정해진다. [쓰기 모델](#write-model)을 참고한다.

## 사용자 시나리오

스코프 셋이 사용 사례를 포괄한다(로그인 전 셸에는 `public`).

| 사용 사례 | 스코프 | 쓰는 주체 |
|--------------------------------------------------|-------------------|--------------------------------------------------|
| 로그인 전 값(테마, 브랜딩) | `public` | 관리자 |
| 사용자가 **변경할 수 없는** 도메인 전체 값 | `domain` | 관리자 |
| 사용자가 **재정의할 수 있는** 도메인별 **기본값** | `domain` + `user` | 관리자가 기본값을 정하고, 사용자는 (부여된 곳에서) 자기 사본을 쓴다 |
| **기본값이 없는** 사용자 값 | `user` | 사용자(부여된 곳에서). 관리자도 쓸 수 있다 |

- 관리자는 도메인 전체에 적용되는 값을 정한다. 도메인에 고정된 값은 사용자가 변경할 수 없다(`user` 쓰기 부여가 없다).
- 일부 도메인 설정은 **로그인 전에** 읽을 수 있어야 한다(테마).
- 관리자가 부여한 곳에서 사용자는 자기 설정을 서버에 저장한다(언어, 최근 사용한 세션, 표시 여부와 순서를 가진 테이블 column, 실험 기능 토글).
- `config_name` 하나가 스코프마다 다른 값을 가질 수 있다. 관리자는 `public` / `domain` 값을 관리하고, 사용자는 자기 `user` 스코프 fragment 만 변경한다. 스코프별 fragment 를 병합으로 합치는 이 하나의 방식이 위의 모든 사용 사례를 포괄한다.

## 설계 원칙

- **스키마 없는 JSON.** 백엔드는 순수 저장소다. 각 config 의 구조와 의미는 프론트엔드가 가진다.
- **스코프 = 엔티티.** 접근 제어는 field 별이 아니라 스코프 수준에서 표현한다. 스코프는 셋이다. `public`(익명 조회 / 관리자 쓰기), `domain`(같은 도메인 조회 / 관리자 쓰기), `user`(소유자와 관리자 조회 / 소유자 변경, 관리자 쓰기).
- **명시적 이름 등록.** 모든 config 이름은 `app_config_definitions` 에 있다. 허용 목록 항목이 foreign key 로 그 이름을 참조하고, fragment 는 허용 목록 항목을 통해 간접적으로 참조한다(fragment 는 항목이 필요하고 항목은 등록된 이름이 필요하므로 fragment 에 직접 FK 가 필요 없다). 등록되지 않은 `config_name` 에 fragment 가 존재할 수 없다.
- **조회에 권한 조회가 없다.** 병합은 `app_config_fragments` 를 `app_config_allow_list` 와 **반드시** join 한다. `rank` 는 허용 목록 항목에만 있으므로 그것 없이는 순서를 계산할 수 없다(인덱스를 타는 `(config_name, scope_type)` join). join 은 `rank` 만을 위한 것이고, 조회 시점에 RBAC 이나 정책을 평가하지 않는다. 격리는 검사하는 것이 아니라 구조로 보장한다. 조회는 `domain_id` 만 받고, service 가 세션에서 스코프의 사용자 쪽 절반을 채우므로 다른 사용자를 지정할 field 가 없다.
- **허용 목록 = 쓰기 게이트이자 병합 순서.** `app_config_allow_list` 는 `(config_name, scope_type)` 하나당 **row 하나**를 가진다. 그 스코프의 fragment 는 그 row 가 있을 때**만** 생성할 수 있고, 관리자 mutation 과 일반 mutation 이 똑같다. fragment 는 FK(`ON DELETE CASCADE`)로 자기 항목을 참조하므로 항목을 제거하면 그 fragment 도 제거된다. 관리자를 구분하는 점은 관리자만 허용 목록과 `app_config_definitions` 자체를 관리한다는 점이다.
- **`rank` 는 허용 목록 항목에 있다.** 병합 우선순위는 관리자가 가지는 정책이다. fragment 가 아니라 (관리자가 관리하는) 허용 목록 항목에 있으므로, fragment 소유자가 자기 fragment 를 변경해도 병합 순서를 변경할 수 없다(`rank` 절 참고).
- **단일 기준 테이블.** `app_config_fragments` 테이블 하나가 모든 스코프를 담고, 노출 계층만 나뉜다.

---

## 1. 데이터 모델

테이블은 셋이고, `app_config_definitions` 가 나머지 둘이 참조하는 중심이다.

### `app_config_definitions`: 등록된 config

config 이름 하나당 row 하나다. fragment 나 허용 목록 항목이 참조하려면 이름을 먼저 여기 등록해야 한다. **관리자가 명시적으로 관리한다**(`create` / `purge`). 등록은 fragment 쓰기의 부수 효과가 아니라 의도적인 단계다.

- `config_name`: config 이름(unique). 나머지 두 테이블의 foreign key 대상이다. 변경할 수 없다(이름 변경 = 영구 삭제 후 재생성).
- `created_at` / `updated_at`.

### `app_config_fragments`: 스코프별 값(조회 hot path)

자연 복합 키 `(scope_type, scope_id, config_name)`(unique)로 식별한다. 조회 병합은 이 테이블만 스캔한다. 주목할 column 은 다음과 같다.

- `scope_type`: `public | domain | user`.
- `scope_id`: 스코프의 식별자(아래 규칙 참고).
- `config_name`: FK → `app_config_definitions.config_name`.
- `(config_name, scope_type)`: `ON DELETE CASCADE` 를 가진 복합 FK → `app_config_allow_list`. fragment 는 허용 목록 항목이 있는 동안에만 존재하고 자체 rank 를 갖지 않는다. 병합 우선순위는 항목의 `rank` 다(`rank` 절 참고).
- `config`: 스키마 없는 JSON payload.
- `created_at` / `updated_at`.

### `app_config_allow_list`: `(config_name, scope_type)` 별 쓰기 게이트

`(config_name, scope_type)` 하나당 row 하나(unique)다. 정규화된 단일 목적 테이블로, **쓰기 게이트**다. `(config_name, scope_type)` 의 fragment 는 여기에 row 가 있을 때만 쓸 수 있다. 관리자가 미리 설정한다.

- `config_name`: FK → `app_config_definitions.config_name`.
- `scope_type`: fragment 를 쓸 수 있는 스코프(`public | domain | user`). 사용자가 재정의할 수 있는 config 는 `(config_name, user)` row 를 가지고, 관리자 전용 값은 `(config_name, domain)` 이나 `(config_name, public)` 을 가진다.
- `rank`: 이 항목 아래 모든 fragment 가 갖는 병합 우선순위(낮음 → 높음, 높은 쪽이 이긴다). 스코프 유형별 기본값이 있고(`rank` 절 참고), 관리자가 명시적으로 정할 수 있다.
- `created_at` / `updated_at`.

row 의 **존재**가 쓰기 부여이고, row 의 `rank` 가 그 fragment 들의 병합 순서다. row 는 **두 쓰기 경로 모두**를 검사한다. 관리자는 사용자와 달리 허용 목록 row 자체를 생성하거나 영구 삭제할 수도 있고, row 를 영구 삭제하면 그 fragment 가 함께 cascade 된다.

### 스코프 ID 규칙

| `scope_type` | `scope_id` | `config` 의 의미 |
|--------------|-------------------------|----------------------------------|
| `public` | 문자열 `"public"` | config 의 로그인 전 값 |
| `domain` | `domain_id` | 도메인의 값이자 기본값 |
| `user` | `user_id`(UUID 문자열) | 사용자 자신의 값 |

### 무결성

- 관리자든 일반이든 **모든** fragment 생성에는 쓰기 대상 `(config_name, scope_type)` 의 `app_config_allow_list` row 가 필요하다. 쓰기 게이트(도메인 에러)와 복합 FK 가 둘 다 강제한다. 그 항목이 등록된 `config_name` 을 참조하므로 등록이 간접적으로 보장된다. fragment 에 `app_config_definitions` 로 가는 직접 FK 는 필요 없다. 기존 fragment 의 변경과 영구 삭제에는 게이트가 필요 없다. fragment 가 있는 동안 항목이 있다는 것을 FK 가 보장한다.
- 일반(비관리자) mutation 은 호출자 자신의 `user` row 로 더 제한된다. 관리자 mutation 은 어떤 스코프든 대상으로 할 수 있고(여전히 허용 목록이 검사한다), 허용 목록과 `app_config_definitions` 를 관리할 수 있는 유일한 쓰기다.
- `app_config_definitions` 영구 삭제는 **하위 트리 전체로 cascade 된다**. 허용 목록 항목이 `config_name` FK(`ON DELETE CASCADE`)로 제거되고, 그 항목의 fragment 가 다시 그 항목에서 cascade 된다. 따라서 config 이름을 폐기하면 한 문장으로 허용 목록과 fragment 가 정리된다.
- `app_config_allow_list` 영구 삭제는 **부여를 해지하고 데이터를 버린다**. 그 `(config_name, scope_type)` 의 fragment 가 `ON DELETE CASCADE` FK 로 제거되므로, 해지한 값은 같은 문장에서 병합 대상에서 사라진다. 따로 정리할 고아 fragment 가 없다.

<a id="write-model"></a>
### 쓰기 모델

mutation 은 두 종류다.

- **관리자 mutation**(관리자 전용): `(config_name, scope_type)` 이 허용 목록에 있는 어떤 스코프의 fragment 든 `create` / `update` / `purge` 한다. 다른 사용자의 `user` row 를 쓸 수 있는 유일한 mutation 이고, 허용 목록과 `app_config_definitions` 자체를 관리할 수 있는 유일한 mutation 이다.
- **일반 mutation**(인증된 모든 사용자): `(config_name, user)` 의 허용 목록 row 가 **있을 때만** 호출자 자신의 `user` row 를 `create` / `update` / `purge` 한다.

`create` 는 자연 키가 이미 있으면 에러를 낸다. `update` 는 자연 키가 없으면 에러를 낸다. `purge` 는 row 를 제거한다(그리고 그 row 의 병합 기여분도 사라진다). `update` 는 저장된 JSON 을 전체 교체한다. 쓰기 경계에서 부분 갱신이나 deep update 는 없다. 호출자가 config 를 삭제하지 않고 "비우려면" `{}` 로 `update` 한다. fragment 는 남고 여전히 기여분으로 세므로 병합이 성공하고 다른 fragment 가 가진 값을 낸다. 기여분을 완전히 제거하는 것은 `purge` 다.

**재정의할 수 있는지는 쓰기 부여로 정해진다.**

- **고정**(사용자가 변경할 수 없음): 허용 목록에 `(config_name, user)` row 가 없으므로 일반 `user` 스코프 쓰기가 거부되고, 병합 값은 관리자 값이다(`public` / `domain` fragment 만).
- **재정의할 수 있음**: 관리자가 `(config_name, user)` 를 부여한다. 관리자가 `domain` 기본값을 정하고, 사용자는 자기 `user` fragment 를 자유롭게 생성, 변경, 영구 삭제하며, 병합에서 이 값이 이긴다(`user` 항목의 기본 `rank` 가 가장 높다).
- **사용자 전용**: 부여가 있고 관리자 fragment 는 게시되지 않는다.

고정 값을 사용자 설정 가능으로 승격하려면 관리자가 `(config_name, user)` 부여 하나를 추가한다. 데이터 migration 은 필요 없다. 다시 잠그려면 관리자가 부여를 제거한다. cascade 가 기존 `user` fragment 를 함께 제거하므로 관리자 값이 곧바로 다시 적용된다.

---

## 2. `rank`: 병합 우선순위

`rank` 는 **허용 목록 항목**이 갖는 정수 우선순위다. 그 항목 아래 쓰인 모든 fragment 가 그 우선순위로 병합된다(낮음 → 높음, 높은 쪽이 이긴다). fragment 가 아니라 허용 목록에 있는 이유는 병합 순서가 관리자 정책이기 때문이다. fragment 쓰기는 일부가 사용자 소유이고, fragment 에 rank 를 두면 사용자가 자기 row 를 변경해 병합 순서를 변경할 수 있다.

- **스코프 유형별 기본값.** 새 항목의 `rank` 는 `scope_type` 에서 기본값을 가져온다. `public` = 100, `domain` = 200, `user` = 300 이다. 이 기본값이 스코프를 정렬해, 사용자 자신의 fragment 가 도메인 기본값에 우선 적용되고 그것이 public 값에 우선 적용된다. 100 간격은 그 사이에 사용자 지정 순서를 둘 여지를 남긴다.
- **관리자 재정의.** 관리자는 항목을 생성할 때 `rank` 를 명시적으로 정할 수 있다. 예를 들어 `user` 보다 높은 rank 의 `domain` 항목은, `user` 부여가 있는 곳에서도 사용자 fragment 가 이길 수 없는 도메인 강제 값을 생성한다.
- **호출자별 전순서.** 호출자 하나와 `config_name` 하나에 대해 스코프 유형마다 최대 fragment 하나가 적용되므로(`AppConfig` 절 참고), 항목 rank 가 모든 병합 입력에 전순서를 준다.

---

## 3. `AppConfig`: 병합된 뷰

조회 모양은 두 가지다.

- **`AppConfigFragment`**: 스코프와 무관한 raw row 하나다. `scopeType`, `scopeId`, `configName`, `config` 를 가진다. 호출자는 `scopeType` 을 읽어 스코프를 구분한다(스코프별 wrapper 타입은 없다).
- **`AppConfig`**: `config_name` 에 대한 사용자별 병합 뷰다. 순서대로 기여한 `fragments` 와 deep merge 된 `config` 를 가진다.

### 병합을 해석하는 방법

사용자가 `config_name` 을 해석할 때 **적용되는** fragment 는 그 사용자에게 스코프가 적용되는 row 다.

- 모든 `public` fragment(`scope_id = "public"`),
- 사용자의 `domain` fragment(`scope_id = 사용자의 도메인`),
- 사용자의 `user` fragment(`scope_id = 사용자의 id`).

`app_config_fragments` 질의 하나가 정확히 그 row 들을 고르고(사용자의 도메인은 세션에서 알 수 있으므로 RBAC 조회가 없다), 각 row 를 허용 목록 항목과 join 해 `rank` 를 얻고, 그 값으로 정렬한 뒤(낮음 → 높음) deep merge 한다. 중첩 객체는 재귀하고, 스칼라와 목록은 전체를 교체하며, 충돌 시 `rank` 가 높은 쪽이 이긴다.

**병합할 것이 없으면 404 다.** 어떤 보이는 fragment 도 기여하지 않는 `config_name` 은 빈 값이나 null 로 해석하지 않고 `AppConfigFragmentNotFound` 를 낸다. 이름이 등록되지 않았거나 호출자의 스코프에서 보이는 것이 없다는 뜻이다. 클라이언트는 404 에서 내장 기본값으로 대체한다.

따라서 병합된 `config` 는 늘 객체이고 null 이 아니다. 모든 기여 fragment 의 `config` 가 `{}` 일 때만 비어 있다. 병합은 key 를 추가하고 교체하지만 버리지는 않으므로, 비어 있지 않은 fragment 를 어떻게 조합해도 `{}` 로 줄지 않는다.

### 조회 형태

- **해석(Resolve)**: 유일한 조회다. `config_name` 목록을 받아 요청 이름마다 `AppConfig` 하나를 요청 순서대로 반환하고, 같은 이름이 반복되면 출력에서도 반복된다. 이름 하나는 원소 하나짜리 요청이다. 별도의 단일 이름 형태는 없다. 셸을 부트스트랩하는 클라이언트는 config 여럿을 한 번에 요청하고, 진입점이 둘이면 없는 이름을 보고하는 방식만 달라진다. **전부 아니면 전무다.** 요청한 이름 하나에 아무것도 기여하지 않으면 호출 전체가 실패한다. 부분 결과를 내려면 없는 이름을 어떻게든 표시해야 하고, 그렇게 하는 모든 방식이 호출자가 두 번째 실패 유형까지 구분해 처리하게 만든다. 대가는 클라이언트가 선택적 config 이름과 필수 config 이름을 함께 묶어 요청할 수 없다는 점이다.
- **검색(자기 것)**: 사용자 자신의 `AppConfig` 를 `(user_id, config_name)` 으로 묶어 페이지로 나눈다. 이름마다 병합을 독립적으로 평가한다.
- **검색(관리자, 사용자 간)**: 감사와 지원을 위해 아무 사용자의 `AppConfig` 든 해석한다. 관리자 전용이다.

---

## 4. 클라이언트 통합(WebUI)

- **로그인 전에** WebUI 가 `public` config(테마, 브랜딩)를 익명으로 가져와 셸을 렌더링한다.
- **로그인 후에** 병합된 `AppConfig`(`theme`, `menu`, `preferences` 등)를 읽는다. 호출자에게 존재하는 모든 public, domain, user fragment 를 빠르게 join 없이 병합한 값이다. 사용자 변경은 자기 `user` fragment 에 대한 일반 mutation 으로 저장하고(관리자가 부여한 곳에서만 허용된다), 이 mutation 이 다시 계산된 병합 뷰를 반환한다.

---

## 5. 사용자 시나리오

- **config 이름을 등록하고 스코프를 연다**: 관리자가 `theme` 의 `app_config_definitions` row 를 생성하고, 사용할 스코프마다 `app_config_allow_list` row 를 생성한다. 예를 들어 관리자 기본값용 `(theme, domain)` 과, 사용자가 설정을 변경할 수 있으면 `(theme, user)` 를 생성한다. fragment 는 그 스코프의 row 가 생긴 뒤에만 쓸 수 있다.
- **로그인 전 public config**: `public` `theme` 을 익명으로 읽는다.
- **로그인 후 부트스트랩**: 병합된 `AppConfig` 를 질의 한 번으로 읽는다. 각 값은 허용 목록 항목과 join 한 fragment 에 대한 rank 병합이고, 스코프별로 잇는 작업이 없다.
- **사용자가 config 를 변경**: 호출자 자신의 `user` row 에 일반 create/update/purge 를 한다(부여가 있는 곳에서만). 응답은 다시 계산된 병합이다.
- **관리자가 고정 도메인 값을 게시**: `(config_name, domain)` 허용 목록 row 를 추가하고 `domain` fragment 를 쓰며 `(config_name, user)` row 는 추가하지 않는다. 사용자는 재정의할 수 없다.
- **관리자가 값을 사용자 재정의 가능하게 설정한다**: `(config_name, user)` 부여를 추가하면 사용자가 자기 사본을 생성, 변경, 영구 삭제한다. 데이터 migration 은 없다.
- **관리자가 값을 다시 잠근다**: `(config_name, user)` 부여를 제거한다. cascade 가 기존 `user` fragment 를 함께 제거한다.
- **관리자가 기여 순서를 변경한다**: 허용 목록 항목의 `rank` 를 정한다(fragment 별이 아니라 `(config_name, scope_type)` 별).
- **관리자가 config 이름을 폐기**: `app_config_definitions` row 를 영구 삭제한다. 허용 목록 항목과 그 fragment 가 함께 cascade 되므로 사전 정리가 필요 없다.
- **관리자 감사**: 지원을 위해 스코프 간 fragment 검색과 사용자 간 병합 검색을 한다.
