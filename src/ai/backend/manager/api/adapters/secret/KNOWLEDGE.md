---
name: secret-adapter-scenarios
type: reference
description: what the secret adapter guarantees; the status count of stored secrets by the key holding them, the re-encryption pass that rewrites every row through the write provider, the monitor role passing the status and refused the pass
scope: src/ai/backend/manager/api/adapters/secret
keywords: [secret, scenario, adapter, superadmin, monitor, reencrypt, key provider, plaintext]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# secret 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터는 자체 엔티티 행을 갖지 않는다. 저장된 `secret`이 어느 키로 암호화돼 있는지 세는 상태
조회와, 저장된 `secret` 전부를 `write_provider_type` 값이 가리키는 제공자로 다시 쓰는 재암호화뿐이다.
둘 다 호출한 사용자가 슈퍼관리자인지 검사하는데, 상태 조회는 읽기 연산이라 모니터 역할도 통과하고
재암호화는 쓰기 연산이라 통과하지 못한다. 한 어댑터 안에서 그 차이를 보여 주는 유일한 짝이다.

집계 대상은 키페어의 `secret_key` 컬럼 하나뿐이다. 호출자도 키페어를 가지므로 호출자의 `secret_key`
값은 언제나 `counts` 집계에 포함되고, 저장된 `secret`이 하나도 없는 상황은 만들 수 없다.

키 풀은 시나리오가 직접 만들어 주입한다. 외부 서비스는 없다 — 구현된 키 제공자는 설정에서 키를 읽는
`config` 제공자 하나뿐이고, `write_provider_type` 값을 지정하지 않으면 새 값은 평문으로 저장된다.

## 상태 조회

`counts`는 `provider_type`, `key_id` 순으로 정렬되어 반환된다. 실행마다 순서가 같으므로 그대로 비교한다.

## 재암호화

재암호화는 모든 행을 동일하게 다룬다. 이미 `write_provider_type` 값이 가리키는 제공자의 키로 암호화된
행도 새 데이터 키로 다시 쓰므로, "이미 그 키로 암호화된 `secret`을 다시 옮긴다" 시나리오에서도
`reencrypted` 값이 `scanned` 값과 같다. 중간에 끊긴 재암호화는 다시 실행해 이어 가도록 설계돼 있고,
그래서 같은 요청을 두 번 실행해도 응답이 같다.

`write_provider_type`이 `plain`이면 재암호화가 값을 평문으로 되돌린다. "`write_provider_type`이
`plain`일 때 실행한다"와 "암호화된 `secret`을 평문으로 되돌린다" 시나리오가 그 경우다. `reencrypted` 값은
내용이 바뀐 행의 수가 아니라 다시 쓴 행의 수이므로, 평문에서 평문으로 다시 쓴 행도 센다.

"모니터 역할이 상태를 조회한다"와 "모니터 역할이 실행한다" 시나리오가 이 어댑터의 요점이다. 같은
사용자가 상태는 조회할 수 있지만 재암호화는 실행하지 못한다.
