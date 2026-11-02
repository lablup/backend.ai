# client_ip_masking adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 이 문서를 먼저 의심한다.

adapter 가 제공하는 호출은 `upsert`, `admin_search`, `purge`, `partial_bulk_purge` 넷이다. `id` 로 하나를 조회하는 호출은 없다.

정책 row 는 `target_type` 하나당 하나만 존재한다(`client_ip_masking_policies` 의 unique 제약). `target_type` 은 `default`(다른 `target_type` 값이 상속하는 기본값), `login_history`, `audit_logs` 중 하나이고, `mode` 는 `none`, `truncate`, `drop` 중 하나다. `ipv4_prefix` 와 `ipv6_prefix` 는 `truncate` 모드가 주소의 앞에서 남길 비트 수(CIDR 의 `/24`, `/48`)를 정하는 값이며 요청에서 생략할 수 있다.

호출마다 통과해야 하는 검사가 다르다.

| 호출 | 검사 | 통과하는 호출자 | 거부 예외 |
|---|---|---|---|
| `upsert` | superadmin 여부 | superadmin | `InsufficientPrivilege` |
| `admin_search` | superadmin 여부 | superadmin, monitor | `InsufficientPrivilege` |
| `purge` | 그 정책에 대한 엔티티 권한 | superadmin | `NotEnoughPermission` |
| `partial_bulk_purge` | 정책마다 엔티티 권한 | superadmin | 정책마다 실패 목록에 권한 부족 이유 |

정책은 어느 스코프에도 속하지 않으므로 `purge` 가 검사하는 엔티티 권한을 부여받을 방법이 없다. 결국 `purge` 를 통과하는 호출자도 superadmin 뿐이다.

## Upsert (`upsert`)

upsert 는 기존 row 와 병합하지 않고 보낸 값으로 row 전체를 교체한다. 따라서 요청에서 생략한 `ipv4_prefix` 와 `ipv6_prefix` 는 저장된 값이 있어도 null 이 된다. 부분 변경처럼 보여 오해하기 쉬운 동작이라 "prefix 가 저장된 정책에 prefix 없이 다시 upsert 한다" 시나리오를 따로 둔다.

`ipv4_prefix` 와 `ipv6_prefix` 가 null 이면 정책 row 에 저장된 값이 없음을 의미한다. 주소를 자를 때 사용하는 기본값(24, 48)은 마스킹을 적용하는 `ClientIPMasker` 가 채우고, 이 adapter 의 응답에는 null 이 그대로 담긴다.

`ipv4_prefix` 가 0~32, `ipv6_prefix` 가 0~128 을 벗어나는 요청은 시나리오로 두지 않는다. 요청 DTO 의 검증이 adapter 를 호출하기 전에 이를 거부한다. `target_type` 과 `mode` 의 값마다 저장되는지도 시나리오로 두지 않는다. adapter 가 보장하는 동작이 아니라 column 타입이 받는 값의 목록이고, 단위 테스트에서 다룬다.

## 검색 (`admin_search`)

`target_type` 과 `mode` 필터가 무엇을 좁히는지는 시나리오로 두지 않는다. 필터를 조건으로 옮기는 것과 그 조건으로 row 를 고르는 것은 단위 테스트에서 다룬다. `target_type` 이 `default`, `login_history`, `audit_logs` 셋뿐이라 정책 row 도 셋을 넘지 못하므로, 페이지 크기보다 많은 row 를 생성해 다음 페이지를 확인하는 시나리오도 둘 수 없다.

monitor 역할은 superadmin 검사에서 읽기 호출만 통과한다. "monitor 역할이 전체를 조회한다"(통과)와 "monitor 역할이 upsert 한다"(거부)가 그 차이를 보여 준다.

## 영구 삭제 (`purge`)

`upsert`, `admin_search`, `purge` 중 `id` 를 받는 것은 `purge` 뿐이다. upsert 는 `target_type` 으로 row 를 찾고 purge 는 `id` 로 찾으므로, 영구 삭제할 `id` 는 upsert 응답이나 검색 결과에서 읽어 와야 한다. 하나를 조회하는 호출이 없어 `id` 를 알아도 그 row 를 다시 확인하는 방법은 검색뿐이다.

존재하지 않는 `id` 는 호출자에 따라 다른 이유로 거부된다. 권한 검사가 row 를 읽기 전에 실행되고 없는 row 에는 부여된 권한도 없으므로 일반 사용자는 `NotEnoughPermission` 을 받는다. 권한 검사를 통과하는 superadmin 만 `EntityNotFoundError` 를 받는다.

row 를 남기는 삭제는 없다.

## 여럿 영구 삭제 (`partial_bulk_purge`)

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 정책은 처리된 목록에, 처리하지 못한 항목은 `id` 와 이유를 실패 목록에 담는다.
