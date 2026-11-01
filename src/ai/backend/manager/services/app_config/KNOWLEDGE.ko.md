# 앱 설정 서비스: 배경

> 규칙: `../AGENTS.md`. Action shape 와 public gate: `../../actions/KNOWLEDGE.md`.

앱 설정은 저장되는 값이 아니다. 조회할 때마다 세 테이블에 나뉜 값을 병합해 구성하므로 값에 대응하는 row 가 없다.

## 앱 설정을 구성하는 테이블

| 테이블 | 정하는 것 | 기록하는 주체 |
|---|---|---|
| `app_config_definitions` | 어떤 `config_name` 이 있는지 | admin |
| `app_config_allow_list` | 어느 스코프가 `config_name` 을 채울 수 있는지, 병합 순서를 정하는 `rank` | admin |
| `app_config_fragments` | 허용된 스코프가 담은 값 | 해당 스코프 소유자 |

- 조회는 허용된 스코프가 담은 fragment 를 `rank` 오름차순으로 깊이 병합한다.
- action 의 `entity_type()` 은 `app_config` 이고 읽는 테이블은 `app_config_fragments` 이며, 결과의 `entity_ids()` 는 빈 tuple 이다.

## 설계와 값은 별개다

- `app_config_definitions` 와 `app_config_allow_list` 는 superadmin 이 앱 설정을 설계하는 곳이고, `app_config_fragments` 는 그 설계 아래에서 기록한 값을 담는다.
- 설계는 `config_name` 마다 다르다. 어떤 것은 admin 에서만 값을 받고, 어떤 것은 user 까지 열린다.
- domain 이 user 에 우선 적용되는지 그 반대인지도 그 `config_name` 의 `rank` 가 정한다. rank 가 높은 쪽이 우선 적용되고, 값의 소유자는 자기 항목의 우선순위를 올릴 수 없다.

## 두 조회는 스코프 연산이다

둘 다 엔티티 유형 `app_config` 를 가진다.

`backend.ai mgr ops list --concern app_config` 는 연결 및 호출 경로로 처리되는 목록을 출력한다.

- 여러 이름을 한 번에 받기 때문에 `GET` 이 아니라 `SEARCH` 다.
- user 스코프 조회의 세 조건인 public, 그 user 의 domain, 그 user 는 하나의 `VisibleAppConfigFragmentTarget` 으로 묶인다. 호출부가 조립하게 두면 세 조건 중 하나가 빠진 채 병합이 실행될 수 있다.
- 셋은 각각 row 자신의 `(scope_type, scope_id)` 와 일치하는지 확인하고, 스코프가 어디까지 접근하는지 소유권 그래프에 질의하지 않는다. 병합은 각 스코프에 기록된 fragment 를 고른다. 접근 권한은 병합 전에 호출자 자신의 스코프에 대한 RBAC gate 가 판정한다. 그래프로 판정하면 domain 이 자기 user 가 가진 모든 fragment 에 접근하므로 다른 user 의 값이 호출자의 앱 설정에 병합된다(BA-7934, 소유권 그래프로 판정할 때 다른 user 의 값이 섞이는 문제).
- adapter 는 user 와 domain 을 session 에서 채우므로 호출자가 다른 사람의 것을 지정할 수 없다.

## anonymous 조회는 public 값을 반환한다

- anonymous 스코프는 주체를 지정하지 않으므로 접근 권한을 판정할 스코프가 없다. 질의 축은 `PublicAppConfigFragmentTarget` 하나뿐이라 public 인 fragment 만 병합된다.
- `public` 은 소유자가 없어 `scope_id` 도 없다. 조건만 있으면 되는 질의 축에는 표현할 수 있지만, 접근 권한을 판정할 때 지정할 대상이 없다.
