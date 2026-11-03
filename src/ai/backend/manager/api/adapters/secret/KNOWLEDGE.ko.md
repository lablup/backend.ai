# secret adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 문장을 먼저 의심한다.

이 adapter 는 자체 엔티티 row 를 갖지 않는다. 저장된 `secret` 이 어느 키로 암호화되었는지 세는 상태 조회와, 저장된 `secret` 전체를 `write_provider_type` 값이 참조하는 provider 로 다시 작성하는 재암호화뿐이다. 둘 다 호출한 사용자가 superadmin 인지 검사하는데, 상태 조회는 읽기 연산이라 monitor 역할도 통과하고 재암호화는 쓰기 연산이라 통과하지 못한다. 한 adapter 안에서 그 차이를 보여 주는 유일한 짝이다.

집계 대상은 키페어의 `secret_key` column 하나뿐이다. 호출자도 키페어를 가지므로 호출자의 `secret_key` 값은 항상 `counts` 집계에 포함되고, 저장된 `secret` 이 하나도 없는 상황은 생성할 수 없다.

키 풀은 시나리오가 직접 생성해 주입한다. 외부 service 는 없다. 구현된 키 provider 는 설정에서 키를 읽는 `config` provider 하나뿐이고, `write_provider_type` 값을 지정하지 않으면 새 값은 평문으로 저장된다.

## 상태 조회

`counts` 는 `provider_type`, `key_id` 순으로 정렬되어 반환된다. 실행마다 순서가 같으므로 그대로 비교한다.

## 재암호화

재암호화는 모든 row 를 동일하게 다룬다. 이미 `write_provider_type` 값이 참조하는 provider 의 키로 암호화된 row 도 새 데이터 키로 다시 작성하므로, "이미 그 키로 암호화된 `secret` 을 다시 옮긴다" 시나리오에서도 `reencrypted` 값이 `scanned` 값과 같다. 중간에 끊긴 재암호화는 다시 실행하면 이어지도록 설계했으므로 같은 요청을 두 번 실행해도 응답이 같다.

`write_provider_type` 이 `plain` 이면 재암호화가 값을 평문으로 되돌린다. "`write_provider_type` 이 `plain` 일 때 실행한다"와 "암호화된 `secret` 을 평문으로 되돌린다" 시나리오가 그 경우다. `reencrypted` 값은 내용이 변경된 row 수가 아니라 다시 작성한 row 수이므로, 평문에서 평문으로 다시 작성한 row 도 센다.

"monitor 역할 사용자가 상태를 조회한다"와 "monitor 역할 사용자가 실행한다" 시나리오가 이 adapter 의 요점이다. 같은 사용자가 상태는 조회할 수 있지만 재암호화는 실행하지 못한다.
