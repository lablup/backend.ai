---
name: client-ip-masking-adapter-scenarios
type: reference
description: what the client IP masking adapter guarantees, as scenarios; one policy per target set by an upsert that replaces the row whole, the superadmin role on upsert and search against the entity gate on purge, no single read
scope: src/ai/backend/manager/api/adapters/client_ip_masking
keywords: [client ip masking, scenario, adapter, superadmin, monitor, upsert, target, purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# client_ip_masking 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 이 문서 쪽을 먼저
의심한다.

어댑터가 제공하는 호출은 `admin_upsert`, `admin_search`, `admin_purge` 셋이다. `id`로 하나를 조회하는
호출은 없다.

정책 행은 `target_type` 하나당 하나만 존재한다(`client_ip_masking_policies`의 unique 제약).
`target_type`은 `default`(다른 `target_type` 값이 물려받는 기본값), `login_history`, `audit_logs` 중 하나이고,
`mode`는 `none`, `truncate`, `drop` 중 하나다. `ipv4_prefix`·`ipv6_prefix`는 `truncate` 모드가
주소의 앞에서 몇 비트를 남길지 정하는 값(CIDR의 `/24`, `/48`)이며, 요청에서 생략할 수 있다.

호출마다 통과해야 하는 검사가 다르다.

| 호출 | 검사 | 통과하는 호출자 | 거부 예외 |
|---|---|---|---|
| `admin_upsert` | 슈퍼관리자 여부 | 슈퍼관리자 | `InsufficientPrivilege` |
| `admin_search` | 슈퍼관리자 여부 | 슈퍼관리자, 모니터 | `InsufficientPrivilege` |
| `admin_purge` | 그 정책에 대한 엔티티 권한 | 슈퍼관리자 | `NotEnoughPermission` |

정책은 어느 스코프에도 속하지 않으므로 `admin_purge`의 엔티티 권한을 부여받을 방법이 없다. 그래서
`admin_purge`를 통과하는 호출자도 결국 슈퍼관리자뿐이다.

## Upsert (`admin_upsert`)

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 정책을 새로 만든다 | 정책이 하나도 없다. 호출자는 슈퍼관리자 | `target_type=default`, `mode=truncate`, `ipv4_prefix=24`, `ipv6_prefix=48` | 응답 노드의 `target_type`, `mode`, `ipv4_prefix`, `ipv6_prefix`가 보낸 값과 같다 |
| prefix를 보내지 않는다 | 정책이 하나도 없다. 호출자는 슈퍼관리자 | `target_type`과 `mode`만 보낸다 | 응답 노드의 `ipv4_prefix`·`ipv6_prefix`가 null이다 |
| 이미 정책이 있는 `target_type`에 다시 upsert한다 | `target_type`이 `default`인 `truncate` 정책이 있다. 호출자는 슈퍼관리자 | 같은 `target_type=default`에 `mode=drop` | 새 행이 생기지 않는다. 기존 행의 `id`는 그대로이고 `mode`만 `drop`으로 바뀐다 |
| prefix가 저장된 정책에 prefix 없이 다시 upsert한다 | `target_type`이 `default`이고 `ipv4_prefix=24`, `ipv6_prefix=48`이 저장된 정책이 있다. 호출자는 슈퍼관리자 | `target_type`과 `mode`만 보낸다 | 저장돼 있던 `ipv4_prefix`·`ipv6_prefix`가 null이 된다 |
| 일반 사용자가 upsert한다 | 호출자는 슈퍼관리자가 아니다 | upsert | `InsufficientPrivilege`로 거부 |
| 모니터 역할이 upsert한다 | 호출자가 `MONITOR` 역할 | upsert | `InsufficientPrivilege`로 거부 |
| 권한 검사를 꺼도 일반 사용자는 upsert할 수 없다 | 권한 검사 비활성화. 호출자는 슈퍼관리자가 아니다 | upsert | `InsufficientPrivilege`로 거부 |

upsert는 기존 행과 병합하지 않고 보낸 값으로 행을 통째로 바꾼다. 그래서 요청에서 생략한
`ipv4_prefix`·`ipv6_prefix`는 저장돼 있던 값이 있어도 null이 된다. 부분 수정처럼 보여 오해하기 쉬운
동작이라 "prefix가 저장된 정책에 prefix 없이 다시 upsert한다" 시나리오를 따로 둔다.

`ipv4_prefix`·`ipv6_prefix`가 null이면 정책 행에 저장된 값이 없다는 뜻이다. 실제로 주소를 자를 때
쓰는 기본값(24, 48)은 마스킹을 적용하는 `ClientIPMasker`가 채우고, 이 어댑터의 응답에는 null이
그대로 담긴다.

`ipv4_prefix`가 0~32, `ipv6_prefix`가 0~128을 벗어나는 요청은 시나리오로 두지 않는다. 요청 DTO의
검증이 어댑터를 호출하기 전에 거부한다. `target_type`과 `mode`의 값마다 저장되는지도 시나리오로
두지 않는다. 어댑터가 보장하는 것이 아니라 컬럼 타입이 받는 값의 목록이고, 단위 테스트의 자리다.

## 검색 (`admin_search`)

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 전체를 조회한다 | `target_type`이 `default`, `login_history`인 정책 둘이 있다. 호출자는 슈퍼관리자 | 필터 없이 조회 | 둘 다 반환되고 `total_count`가 2다 |
| 모니터 역할이 전체를 조회한다 | `target_type`이 `default`, `login_history`인 정책 둘이 있다. 호출자는 `MONITOR` 역할 | 필터 없이 조회 | 슈퍼관리자와 같은 응답. 둘 다 반환된다 |
| 일반 사용자가 조회한다 | 호출자는 슈퍼관리자가 아니다 | 필터 없이 조회 | `InsufficientPrivilege`로 거부 |

`target_type`과 `mode` 필터가 무엇을 좁히는지는 시나리오로 두지 않는다. 필터를 조건으로 옮기는 것과
그 조건으로 행을 고르는 것은 단위 테스트의 자리다. `target_type`이 `default`, `login_history`,
`audit_logs` 셋뿐이라 정책 행도 셋을 넘지 못하므로, 페이지 크기보다 많은 건수를 만들어 다음 페이지를
확인하는 시나리오도 둘 수 없다.

모니터 역할은 슈퍼관리자 검사에서 읽기 호출만 통과한다. "모니터 역할이 전체를 조회한다"(통과)와
"모니터 역할이 upsert한다"(거부)가 그 차이를 보여 준다.

## 완전 삭제 (`admin_purge`)

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 정책을 완전 삭제한다 | 정책 하나가 있다. 호출자는 슈퍼관리자 | 그 정책의 `id`로 purge | 완전 삭제된 정책의 필드를 그대로 담은 응답 |
| 존재하지 않는 `id`를 완전 삭제한다 | 정책 하나가 있다. 호출자는 슈퍼관리자 | 존재하지 않는 `id`로 purge | `EntityNotFoundError`로 거부 |
| 일반 사용자가 정책을 완전 삭제한다 | 정책 하나가 있다. 호출자는 아무 권한도 없는 일반 사용자 | 그 정책의 `id`로 purge | `NotEnoughPermission`으로 거부 |
| 일반 사용자가 존재하지 않는 `id`를 완전 삭제한다 | 정책 하나가 있다. 호출자는 아무 권한도 없는 일반 사용자 | 존재하지 않는 `id`로 purge | `EntityNotFoundError`가 아니라 `NotEnoughPermission`으로 거부 |
| 권한 검사를 끄면 일반 사용자도 완전 삭제할 수 있다 | 권한 검사 비활성화. 정책 하나가 있고, 호출자는 아무 권한도 없는 일반 사용자 | 그 정책의 `id`로 purge | 완전 삭제된 정책의 필드를 그대로 담은 응답 |

`admin_upsert`, `admin_search`, `admin_purge` 중 `id`를 받는 것은 `admin_purge`뿐이다. upsert는 `target_type`으로 행을 찾고 purge는
`id`로 찾으므로, 완전 삭제할 `id`는 upsert 응답이나 검색 결과에서 읽어 와야 한다. 하나를 조회하는 호출이 없어
`id`를 알아도 그 행을 다시 확인하는 방법은 검색뿐이다.

존재하지 않는 `id`는 호출자에 따라 다른 이유로 거부된다. 권한 검사가 행을 읽기 전에 실행되고, 없는
행에는 부여된 권한도 없으므로 일반 사용자는 `NotEnoughPermission`을 받는다. 권한 검사를 통과하는
슈퍼관리자만 `EntityNotFoundError`를 받는다.

soft delete는 없다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 `admin_upsert`, `admin_search`, `admin_purge`가 모두 위에 있다.

리포트에 함께 포함되는 `batch_load_fields`는 모든 어댑터가 상속받는 공용 메서드이지 이 엔티티의
호출이 아니라서 시나리오를 두지 않는다.
