# 엔티티 공유 service

엔티티 공유는 공유하는 쪽의 엔티티를 사람이나 프로젝트에 빌려주고, 받는 쪽이 이를 수락, 거절, 반납한다. 이 패키지는 각 답을 검사하는 스코프를 정한다.

## processor 구성

`backend.ai mgr ops list --concern rbac --entity entity_share` 는 연결된 목록을 출력한다. 그 출력은 엔티티 유형, shape, 연산, gate, backing 을 반환한다.

## 답은 그 공유에 답하는 스코프에서 검사한다

- `accept`, `reject`, `leave` 는 `answering_scope` 를 스코프로 하는 scope shape 이다. 호출자는 그 스코프에서 `entity_share` 의 `update` 권한(`leave` 는 `soft_delete`)이 있어야 한다.
- 프로젝트 앞으로 보낸 공유는 그 프로젝트가 답한다. 프로젝트에서 그 권한을 가진 사용자(프로젝트 관리자)가 프로젝트를 대신해 답한다.
- 그 밖의 공유는 사용자 id 나 이메일로 사람을 지정하고, 호출자가 자기 자신으로 답한다.
- write guard 는 같은 문장 안에서 공유의 수신자와 `answering_scope` 를 맞춰 보므로, 공유가 지정하지 않은 스코프로는 아무것도 처리되지 않는다.

## 답하는 스코프는 public lookup 으로 먼저 찾는다

- `lookup_answering_scope` 는 답을 실행하기 전에 공유의 수신자를 읽는다. row 를 읽기 전에는 답이 자기 스코프를 정할 수 없다.
- 받는 쪽은 공유 자체에 대한 권한이 없으므로 lookup 은 `public_lookup_ops` 로 연결한다.
- 뒤따르는 답이 lookup 이 찾은 스코프에서 검사되며, 그 검사가 실제 권한 검사다.
